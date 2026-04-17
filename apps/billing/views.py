"""
Django views for billing app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.contrib import messages
from decimal import Decimal
import json
from django.utils import timezone
from django.urls import reverse

from apps.accounts.decorators import active_user_required, manager_required, owner_required
from apps.inventory.models import Product, StockMovement
from .models import Invoice, InvoiceItem, Payment, Expense
from .forms import InvoiceForm, PaymentForm
from .pdf_invoice import generate_invoice_pdf


@login_required
@active_user_required
def invoice_list(request):
    """Display list of invoices with filtering."""
    invoices = Invoice.objects.select_related('customer').all()
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        invoices = invoices.filter(status=status)
    
    # Search
    search = request.GET.get('search')
    if search:
        invoices = invoices.filter(
            invoice_number__icontains=search
        ) | invoices.filter(
            customer__name__icontains=search
        )
    
    context = {
        'invoices': invoices,
        'status_filter': status,
        'search_query': search,
        'title': 'Invoices'
    }
    return render(request, 'billing/invoice_list.html', context)


@login_required
@active_user_required
def invoice_detail(request, pk):
    """Display invoice details with payment history."""
    invoice = get_object_or_404(Invoice, pk=pk)
    context = {
        'invoice': invoice,
        'total_paid': invoice.paid_amount,
        'remaining_balance': invoice.remaining_balance,
        'title': f'Invoice {invoice.invoice_number}'
    }
    return render(request, 'billing/invoice_detail.html', context)


@login_required
@active_user_required
@require_http_methods(["GET", "POST"])
def invoice_create(request):
    """Create new invoice with multiple line items."""
    if request.method == 'POST':
        return _handle_invoice_create(request)
    
    # GET request - show form
    products = Product.objects.filter(is_active=True)
    form = InvoiceForm()
    
    context = {
        'form': form,
        'products': products,
        'title': 'Create Invoice'
    }
    return render(request, 'billing/invoice_form.html', context)


def _handle_invoice_create(request):
    """Handle invoice creation with line items."""
    try:
        with transaction.atomic():
            # Get form data
            invoice_number = request.POST.get('invoice_number')
            customer_id = request.POST.get('customer')
            invoice_date = request.POST.get('invoice_date')
            
            # Auto-assign a generic Walk-In Customer for rapid checkout
            if not customer_id or customer_id == 'walkin':
                from apps.customers.models import Customer
                walk_in, _ = Customer.objects.get_or_create(
                    name="Walk-in Customer",
                    defaults={
                        'email': 'walkin@torvix.pos',
                        'phone': '0000000000',
                        'address': 'Counter Sale',
                        'city': 'Default',
                        'postal_code': '000000',
                    }
                )
                customer_id = walk_in.id
                
            due_date = request.POST.get('due_date')
            
            # Generate invoice number if not provided
            if not invoice_number:
                import uuid
                from datetime import datetime
                invoice_number = f"INV-{datetime.now().strftime('%y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
            
            # Default due date to today for POS
            if not due_date:
                due_date = invoice_date or timezone.now().date()

            notes = request.POST.get('notes')
            terms = request.POST.get('terms')
            tax_rate = Decimal(str(request.POST.get('tax_rate', 10)))
            
            # Get items data
            items_data = json.loads(request.POST.get('items_json', '[]')) \
                if 'items_json' in request.POST else _extract_items_from_post(request)
            
            if not items_data:
                messages.error(request, 'Please add at least one item to the invoice.')
                return redirect('billing:invoice_create')
            
            # Create invoice
            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                customer_id=customer_id,
                invoice_date=invoice_date or timezone.now().date(),
                due_date=due_date,
                notes=notes,
                terms=terms or 'Net 30',
                created_by=request.user,
            )
            
            # Create line items and calculate totals
            subtotal = Decimal(0)
            for item_data in items_data:
                product = Product.objects.get(id=item_data['product_id'])
                quantity = int(item_data['quantity'])
                unit_price = Decimal(str(item_data['unit_price']))
                discount_percent = Decimal(str(item_data.get('discount_percent', 0)))
                
                item = InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_percent=discount_percent,
                )
                
                # Automate stock deduction
                product.quantity_in_stock -= quantity
                product.save(update_fields=['quantity_in_stock'])
                
                StockMovement.objects.create(
                    product=product,
                    movement_type='sales',
                    quantity=-quantity,
                    reference=invoice.invoice_number,
                    notes='Automated deduction via Invoice',
                    created_by=request.user
                )

                subtotal += item.line_total
            
            # Calculate and update invoice totals
            invoice.subtotal = subtotal
            invoice.tax_amount = subtotal * (tax_rate / Decimal('100'))
            invoice.total_amount = subtotal + invoice.tax_amount
            
            # Payment Handling for POS
            payment_method = request.POST.get('payment_method')
            if payment_method and payment_method != 'tab':
                from apps.billing.models import Payment
                Payment.objects.create(
                    invoice=invoice,
                    amount=invoice.total_amount,
                    payment_date=invoice.invoice_date,
                    payment_method=payment_method,
                    reference=f"POS-{invoice.invoice_number}",
                    notes=f"Cash Tendered: {request.POST.get('cash_tendered', '0')}" if payment_method == 'mixed' else "",
                    created_by=request.user
                )
                invoice.status = 'paid'
                
                # Award loyalty points
                if invoice.customer and hasattr(invoice.customer, 'loyalty_points'):
                    from apps.customers.models import StoreSetting
                    setting = StoreSetting.get_settings()
                    if Decimal(str(setting.points_conversion_rate)) > Decimal('0'):
                        points_earned = int(invoice.total_amount / Decimal(str(setting.points_conversion_rate)))
                        invoice.customer.loyalty_points += points_earned
                        invoice.customer.save(update_fields=['loyalty_points'])

            elif payment_method == 'tab':
                invoice.status = 'pending'
                if invoice.customer and hasattr(invoice.customer, 'due_amount'):
                    invoice.customer.due_amount += invoice.total_amount
                    invoice.customer.save(update_fields=['due_amount'])
                    
            elif request.POST.get('pos_origin') == 'true':
                invoice.status = 'paid' # POS default shouldn't be draft if from POS checkout mostly
            else:
                invoice.status = 'sent' if request.POST.get('action') == 'send' else 'draft'
                
            invoice.save()
            
            messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
            
            # If from POS, return JSON response for AJAX handling
            if request.POST.get('pos_origin') == 'true':
                return JsonResponse({
                    'status': 'success',
                    'invoice_id': invoice.id,
                    'invoice_url': reverse('billing:invoice_thermal', kwargs={'pk': invoice.id}),
                    'message': f'Invoice {invoice.invoice_number} created successfully!'
                })
                
            return redirect('billing:invoice_detail', pk=invoice.id)
            
    except Exception as e:
        if request.POST.get('pos_origin') == 'true':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        messages.error(request, f'Error creating invoice: {str(e)}')
        return redirect('billing:invoice_create')


def _extract_items_from_post(request):
    """Extract invoice items from POST data."""
    items = []
    index = 0
    while f'product_{index}' in request.POST:
        try:
            product_id = request.POST.get(f'product_{index}')
            quantity = request.POST.get(f'quantity_{index}')
            unit_price = request.POST.get(f'unit_price_{index}')
            discount = request.POST.get(f'discount_{index}', 0)
            
            if product_id and quantity and unit_price:
                items.append({
                    'product_id': int(product_id),
                    'quantity': int(quantity),
                    'unit_price': Decimal(unit_price),
                    'discount_percent': Decimal(discount),
                })
            index += 1
        except (ValueError, TypeError):
            break
    return items


@login_required
@active_user_required
@manager_required
def invoice_edit(request, pk):
    """Edit existing invoice."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.status == 'paid':
        messages.warning(request, 'Cannot edit paid invoices.')
        return redirect('billing:invoice_detail', pk=pk)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Invoice updated successfully!')
            return redirect('billing:invoice_detail', pk=pk)
    else:
        form = InvoiceForm(instance=invoice)
    
    context = {
        'form': form,
        'invoice': invoice,
        'title': 'Edit Invoice'
    }
    return render(request, 'billing/invoice_form.html', context)


@login_required
@active_user_required
def invoice_pdf(request, pk):
    """Generate and download invoice as PDF."""
    invoice = get_object_or_404(Invoice, pk=pk)
    return generate_invoice_pdf(invoice)


@login_required
@active_user_required
@manager_required
@require_POST
def invoice_delete(request, pk):
    """Delete invoice (only if draft)."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.status != 'draft':
        messages.error(request, 'Only draft invoices can be deleted.')
        return redirect('billing:invoice_detail', pk=pk)
    
    invoice_number = invoice.invoice_number
    invoice.delete()
    messages.success(request, f'Invoice {invoice_number} deleted.')
    return redirect('billing:invoice_list')


@login_required
@active_user_required
def payment_create(request, invoice_id):
    """Record payment for an invoice."""
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    
    if invoice.status == 'paid':
        messages.warning(request, 'Invoice is already paid.')
        return redirect('billing:invoice_detail', pk=invoice_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.created_by = request.user
            payment.save()
            
            # Status update is handled in model's save method
            messages.success(request, f'Payment of ${payment.amount} recorded successfully!')
            return redirect('billing:invoice_detail', pk=invoice_id)
    else:
        form = PaymentForm(initial={
            'invoice': invoice,
            'amount': invoice.remaining_balance,
        })
    
    context = {
        'invoice': invoice,
        'form': form,
        'title': 'Record Payment'
    }
    return render(request, 'billing/payment_form.html', context)


@login_required
@active_user_required
def get_product_price(request, product_id):
    """API endpoint to get product price."""
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({
            'price': str(product.unit_price),
            'name': product.name,
            'stock': product.quantity_in_stock,
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


@login_required
@active_user_required
def get_customer_detail(request, customer_id):
    """API endpoint to get customer details and loyalty stats."""
    from apps.customers.models import Customer
    from django.db.models import Sum
    try:
        customer = Customer.objects.get(id=customer_id)
        # Calculate loyalty tier
        total_spent = float(customer.total_spent)
        tier = "Bronze"
        if total_spent >= 5000:
            tier = "Gold"
        elif total_spent >= 1000:
            tier = "Silver"
        
        return JsonResponse({
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'total_spent': total_spent,
            'total_invoices': customer.total_invoices,
            'tier': tier,
            'points': int(total_spent / 10), # 1 point per $10 spent
        })
    except Customer.DoesNotExist:
        return JsonResponse({'error': 'Customer not found'}, status=404)


@login_required
@active_user_required
def dashboard_view(request):
    """
    Main business dashboard with dynamic metrics and charts.
    """
    # Role-based redirect for staff/cashier
    if hasattr(request.user, 'profile') and request.user.profile.role == 'cashier':
        return redirect('billing:pos_terminal')
    
    from apps.customers.models import Customer
    from apps.inventory.models import Product
    from django.db.models import Sum, F
    from django.db import models
    from datetime import timedelta
    from django.utils import timezone
    
    today = timezone.now().date()
    
    # Calculate metrics
    total_paid_invoices = Invoice.objects.filter(status='paid')
    total_revenue = total_paid_invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
    active_customers = Customer.objects.count()
    
    # AI Insight: Today's Profit & Health Score
    from apps.billing.models import InvoiceItem
    sold_items_today = InvoiceItem.objects.filter(invoice__invoice_date=today, invoice__status__in=['paid', 'partial', 'sent'])
    revenue_today = Invoice.objects.filter(invoice_date=today, status__in=['paid', 'partial', 'sent']).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
    cost_today = sum((item.quantity * item.product.cost_price for item in sold_items_today), Decimal('0'))
    profit_today = revenue_today - cost_today
    
    # Low stock items (below threshold)
    low_stock_products_all = Product.objects.filter(is_active=True, quantity_in_stock__lte=models.F('low_stock_threshold'))
    low_stock_count = low_stock_products_all.count()
    
    products_sold = InvoiceItem.objects.aggregate(Sum('quantity'))['quantity__sum'] or 0
    products_sold_today = InvoiceItem.objects.filter(invoice__invoice_date=today).aggregate(Sum('quantity'))['quantity__sum'] or 0
    start_of_month = today.replace(day=1)
    products_sold_month = InvoiceItem.objects.filter(invoice__invoice_date__gte=start_of_month).aggregate(Sum('quantity'))['quantity__sum'] or 0
    overdue_invoices = Invoice.objects.filter(status='overdue').count()
    
    # AI Insight: Most Sold Product
    most_sold_raw = InvoiceItem.objects.values('product__id', 'product__name', 'product__sku').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_qty').first()
    
    most_sold_product = most_sold_raw['product__name'] if most_sold_raw else "N/A"
    most_sold_qty = most_sold_raw['total_qty'] if most_sold_raw else 0
    
    # AI Insight: Smart Restock Suggestion
    restock_suggestion = None
    if low_stock_products_all.exists():
        urgent = low_stock_products_all.order_by('quantity_in_stock').first()
        restock_suggestion = f"Critical: Order {urgent.reorder_quantity} units of {urgent.name} (Current: {urgent.quantity_in_stock})"
    
    # Sales Chart Data (last 7 days)
    labels = []
    sales_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        labels.append(date.strftime('%a'))
        daily_total = Invoice.objects.filter(invoice_date=date, status__in=['paid', 'sent', 'partial']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        sales_data.append(float(daily_total))
        
    # AI Alert logic
    sales_drop_alert = None
    if len(sales_data) >= 2 and sales_data[-2] > 0:
        drop = ((sales_data[-2] - sales_data[-1]) / sales_data[-2]) * 100
        if drop > 30:
            sales_drop_alert = f"Sales dropped by {drop:.0f}% compared to yesterday."

    # Business Health Score Algorithm (0-100)
    health_score = 100
    if overdue_invoices > 5: health_score -= 15
    if low_stock_count > 10: health_score -= 10
    if sales_drop_alert: health_score -= 15
    if profit_today < 0: health_score -= 20
    health_score = max(0, min(100, health_score))
        
    # Recent Activity
    recent_invoices = Invoice.objects.select_related('customer').all().order_by('-created_at')[:5]
    low_stock_products = Product.objects.filter(is_active=True, quantity_in_stock__lte=models.F('low_stock_threshold'))[:5]
    
    # AI Insight: Top 5 Sold Products Ranking
    top_5_raw = InvoiceItem.objects.values('product__id', 'product__name', 'product__sku').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_qty')[:5]
    
    top_5_products = []
    for item in top_5_raw:
        top_5_products.append({
            'name': item['product__name'],
            'sku': item['product__sku'],
            'qty': item['total_qty'],
            'revenue': float(item['total_revenue'])
        })
        
    context = {
        'total_revenue': total_revenue,
        'profit_today': profit_today,
        'revenue_today': revenue_today,
        'health_score': health_score,
        'active_customers': active_customers,
        'low_stock_count': low_stock_count,
        'products_sold': products_sold,
        'products_sold_today': products_sold_today,
        'products_sold_month': products_sold_month,
        'overdue_count': overdue_invoices,
        'sales_labels': labels,
        'sales_data': sales_data,
        'sales_drop_alert': sales_drop_alert,
        'recent_invoices': recent_invoices,
        'low_stock_products': low_stock_products,
        'most_sold_product': most_sold_product,
        'most_sold_qty': most_sold_qty,
        'top_5_products': top_5_products,
        'restock_suggestion': restock_suggestion,
        'today': today,
        'title': 'Admin Command Center'
    }
    return render(request, 'dashboard.html', context)


@login_required
@active_user_required
@manager_required
def expense_list_view(request):
    """Display list of expenses with date filtering."""
    from datetime import datetime
    expenses = Expense.objects.all().order_by('-date')
    
    current_filter = request.GET.get('filter', '')
    start_date = None
    end_date = None
    today = timezone.now().date()
    
    if current_filter == 'today':
        expenses = expenses.filter(date=today)
    elif current_filter == 'month':
        start_of_month = today.replace(day=1)
        expenses = expenses.filter(date__gte=start_of_month)
    
    # Custom date range
    sd = request.GET.get('start_date')
    ed = request.GET.get('end_date')
    if sd:
        start_date = datetime.strptime(sd, '%Y-%m-%d').date()
        expenses = expenses.filter(date__gte=start_date)
        current_filter = 'custom'
    if ed:
        end_date = datetime.strptime(ed, '%Y-%m-%d').date()
        expenses = expenses.filter(date__lte=end_date)
        current_filter = 'custom'
    
    context = {
        'expenses': expenses,
        'title': 'Expenses',
        'current_filter': current_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'billing/expense_list.html', context)


@login_required
@active_user_required
@manager_required
@require_http_methods(["GET", "POST"])
def expense_create(request):
    """Create a new expense record."""
    from .forms import ExpenseForm
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            if not expense.date:
                expense.date = timezone.now().date()
            expense.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'message': 'Expense recorded successfully!'})
            
            messages.success(request, f'Expense "{expense.title}" recorded successfully!')
            return redirect('accounts:admin_dashboard')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        form = ExpenseForm(initial={'date': timezone.now().date()})
    
    return render(request, 'billing/expense_form.html', {'form': form, 'title': 'Add Expense'})


@login_required
@active_user_required
@manager_required
def expense_export_pdf_view(request):
    """Export expenses as PDF."""
    expenses = Expense.objects.all().order_by('-date')
    from apps.billing.pdf_expense import generate_expense_pdf
    return generate_expense_pdf(expenses)


@login_required
@active_user_required
def pos_terminal_view(request):
    """
    Futuristic POS Terminal for rapid checkout.
    """
    from apps.inventory.models import Product
    from apps.customers.models import Customer
    from apps.billing.models import InvoiceItem
    from django.db.models import Sum
    
    products = Product.objects.filter(is_active=True).order_by('name')
    customers = Customer.objects.filter(is_active=True).order_by('name')
    
    # Get top 5 popular products
    popular_ids = InvoiceItem.objects.values('product_id').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]
    popular_products = Product.objects.filter(id__in=[p['product_id'] for p in popular_ids])
    
    # If no popular products, just take first 5 active ones
    if not popular_products.exists():
        popular_products = products[:5]
    
    context = {
        'products': products,
        'customers': customers,
        'popular_products': popular_products,
        'title': 'POS Terminal'
    }
    return render(request, 'billing/pos_terminal.html', context)


@login_required
@active_user_required
def invoice_thermal_preview(request, pk):
    """
    Direct thermal print view for an invoice.
    """
    invoice = get_object_or_404(Invoice, pk=pk)
    
    business_details = {
        'name': 'Torvix Supermarket',
        'address': 'Wayanad, Kerala',
        'phone': '9876543210'
    }
    
    context = {
        'invoice': invoice,
        'business': business_details,
        'title': f'Thermal Print - {invoice.invoice_number}'
    }
    return render(request, 'billing/thermal_invoice.html', context)
@login_required
@active_user_required
@require_POST
def ai_process_view(request):
    """
    AI Processing Node for POS.
    Searches for products and returns natural language responses.
    """
    try:
        data = json.loads(request.body)
        query = data.get('query', '').lower()
        
        if not query:
            return JsonResponse({'response': 'How can I help you today?'})
        
        import difflib
        
        # 1. Parsing Intents
        is_checkout = any(w in query for w in ['checkout', 'bill', 'pay'])
        is_add = any(w in query for w in ['add', 'get', 'need'])
        is_restock = 'restock' in query
        is_print = 'print' in query
        
        potential_matches = Product.objects.filter(is_active=True)
        product_names = [p.name.lower() for p in potential_matches]
        
        # 2. Extract potential quantities (very basic "add 2 soap")
        words = query.split()
        qty = 1
        for word in words:
            if word.isdigit():
                qty = int(word)
                break
                
        # 3. Fuzzy Match for Spelling Mistakes
        best_matches = difflib.get_close_matches(query, product_names, n=3, cutoff=0.3)
        # Also try matching individual words if full query didn't match anything
        if not best_matches:
            for word in words:
                if len(word) > 2:
                    word_matches = difflib.get_close_matches(word, product_names, n=2, cutoff=0.6)
                    best_matches.extend(word_matches)
        
        # Remove duplicates
        best_matches = list(set(best_matches))
        
        if is_print and is_checkout:
            # Send specialized command to frontend to trigger checkout and print
            return JsonResponse({
                'response': "Initiating automated checkout sequence and preparing PDF print job...",
                'action': 'checkout_and_print'
            })
            
        if not best_matches:
            if is_checkout:
                return JsonResponse({
                    'response': "I can process the checkout for you. Opening the payment terminal...",
                    'action': 'checkout'
                })
            return JsonResponse({'response': "I couldn't confidently identify any products in your request. Could you specify the product name again?"})

        # Match back to objects
        matched_products = potential_matches.filter(name__iregex=r'(' + '|'.join(best_matches) + ')')
        
        if is_restock:
            # Mock restock behavior
            p = matched_products.first()
            p.quantity_in_stock += qty
            p.save()
            return JsonResponse({
                'response': f"Successfully logged {qty} new units for {p.name} into inventory. The database is updated."
            })
            
        if is_add or is_checkout:
            p = matched_products.first()
            if p.quantity_in_stock < qty:
                return JsonResponse({'response': f"CRITICAL: Insufficient stock for {p.name}. Only {p.quantity_in_stock} remaining."})

            # Check if it was an exact match in the query (unlikely if we're here, but possible)
            is_perfect_match = any(p.name.lower() in word for word in words) # basic heuristic
            
            # Since the AI is an assistant, always ask for confirmation for complex workflows
            return JsonResponse({
                'response': f"Did you mean **{p.name}**? (Reply '*yes proceed*' to add and checkout, or '*no*')",
                'action': 'require_confirmation',
                'product_id': p.id,
                'qty': qty,
                'is_checkout': is_checkout,
                'is_print': is_print
            })
            
        return JsonResponse({
            'response': f"I found {matched_products.count()} potential matches. What would you like to do with them?"
        })
        
    except Exception as e:
        return JsonResponse({'response': f"AI Integrity Compromised: {str(e)}"}, status=500)


@login_required
@active_user_required
@manager_required
def report_gst_view(request):
    """
    Generate GST Report (CGST / SGST breakdown).
    """
    from datetime import date
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta
    
    # Defaults to current month
    today = timezone.now().date()
    start_date = date(today.year, today.month, 1)
    end_date = today
    
    if request.GET.get('start_date'):
        start_date = request.GET.get('start_date')
    if request.GET.get('end_date'):
        end_date = request.GET.get('end_date')
        
    invoices = Invoice.objects.filter(
        invoice_date__range=[start_date, end_date],
        status__in=['paid', 'sent', 'partial']
    ).prefetch_related('items')
    
    report_data = []
    total_taxable = 0
    total_cgst = 0
    total_sgst = 0
    total_igst = 0 # Future proof
    
    for inv in invoices:
        cgst = float(inv.tax_amount) / 2
        sgst = float(inv.tax_amount) / 2
        
        report_data.append({
            'date': inv.invoice_date,
            'invoice_number': inv.invoice_number,
            'customer': inv.customer.name,
            'taxable_amount': float(inv.subtotal),
            'cgst': cgst,
            'sgst': sgst,
            'total': float(inv.total_amount)
        })
        
        total_taxable += float(inv.subtotal)
        total_cgst += cgst
        total_sgst += sgst

    context = {
        'title': 'GST Report',
        'report_data': report_data,
        'start_date': start_date,
        'end_date': end_date,
        'totals': {
            'taxable': total_taxable,
            'cgst': total_cgst,
            'sgst': total_sgst,
            'grand_total': total_taxable + total_cgst + total_sgst
        }
    }
    return render(request, 'billing/reports_gst.html', context)


@login_required
@active_user_required
@owner_required
def report_profit_loss_view(request):
    """
    Generate Profit/Loss Analytics. Revenue - Cost = Gross Profit.
    """
    from django.utils import timezone
    import datetime
    
    today = timezone.now().date()
    start_date = request.GET.get('start_date', datetime.date(today.year, today.month, 1))
    end_date = request.GET.get('end_date', today)
    
    invoices = Invoice.objects.filter(
        invoice_date__range=[start_date, end_date],
        status__in=['paid', 'sent', 'partial']
    )
    
    from apps.billing.models import InvoiceItem
    sold_items = InvoiceItem.objects.filter(
        invoice__in=invoices
    ).select_related('product')
    
    revenue = sum(float(item.line_total) for item in sold_items)
    cost_of_goods = sum(float(item.product.cost_price * item.quantity) for item in sold_items)
    gross_profit = revenue - cost_of_goods
    
    expenses = Expense.objects.filter(date__range=[start_date, end_date])
    total_expenses = sum(float(e.amount) for e in expenses)
    
    net_profit = gross_profit - total_expenses
    
    context = {
        'title': 'Profit & Loss Report',
        'revenue': revenue,
        'cost_of_goods': cost_of_goods,
        'gross_profit': gross_profit,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'margin': (net_profit / revenue * 100) if revenue > 0 else 0,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'billing/reports_profit_loss.html', context)

