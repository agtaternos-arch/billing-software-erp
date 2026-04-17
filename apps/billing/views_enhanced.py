"""
Enhanced billing views with advanced invoice functionality.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.contrib import messages
from decimal import Decimal
import json

from apps.accounts.decorators import active_user_required
from apps.inventory.models import Product
from .models import Invoice, InvoiceItem, Payment
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
            due_date = request.POST.get('due_date')
            notes = request.POST.get('notes')
            terms = request.POST.get('terms')
            tax_rate = Decimal(str(request.POST.get('tax_rate', 10)))
            
            # Get items data (from JavaScript calculated values)
            items_data = json.loads(request.POST.get('items_json', '[]')) \
                if 'items_json' in request.POST else _extract_items_from_post(request)
            
            if not items_data:
                messages.error(request, 'Please add at least one item to the invoice.')
                return redirect('billing:invoice_create')
            
            # Create invoice
            invoice = Invoice.objects.create(
                invoice_number=invoice_number,
                customer_id=customer_id,
                invoice_date=invoice_date,
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
                unit_price = Decimal(item_data['unit_price'])
                discount_percent = Decimal(item_data.get('discount_percent', 0))
                
                item = InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_percent=discount_percent,
                )
                
                subtotal += item.line_total
            
            # Calculate and update invoice totals
            invoice.subtotal = subtotal
            invoice.tax_amount = subtotal * (tax_rate / Decimal('100'))
            invoice.total_amount = subtotal + invoice.tax_amount
            invoice.status = 'sent' if request.POST.get('action') == 'send' else 'draft'
            invoice.save()
            
            messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
            return redirect('billing:invoice_detail', pk=invoice.id)
            
    except Exception as e:
        messages.error(request, f'Error creating invoice: {str(e)}')
        return redirect('billing:invoice_create')


def _extract_items_from_post(request):
    """Extract invoice items from POST data."""
    items = []
    
    # Count items by looking for product field
    index = 0
    while f'product_{index}' in request.POST or f'product' in request.POST:
        try:
            # Try named format first
            product_id = request.POST.get(f'product_{index}') or request.POST.get('product')
            quantity = request.POST.get(f'quantity_{index}') or request.POST.get('quantity')
            unit_price = request.POST.get(f'unit_price_{index}') or request.POST.get('unit_price')
            discount = request.POST.get(f'discount_{index}') or request.POST.get('discount_percent', 0)
            
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
            
            # Update invoice status
            if payment.amount >= invoice.remaining_balance:
                invoice.status = 'paid'
            else:
                invoice.status = 'partial'
            invoice.save()
            
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
    }
    return render(request, 'billing/payment_form.html', context)


@login_required
@active_user_required
def get_product_price(request, product_id):
    """API endpoint to get product price (for form autocomplete)."""
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({
            'price': str(product.selling_price),
            'name': product.name,
            'stock': product.quantity_in_stock,
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
