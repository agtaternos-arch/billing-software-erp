"""
Django views for customers app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import manager_required
from .models import Customer, ContactPerson, CustomerCategory
from .forms import CustomerForm, ContactPersonForm, CustomerCategoryForm


@login_required
@manager_required
def customer_list(request):
    """Display list of customers."""
    customers = Customer.objects.all()
    
    # Calculate real tier counts based on total_spent
    from apps.billing.models import Invoice
    from django.db.models import Sum
    
    vip_count = 0
    platinum_count = 0
    standard_count = 0
    
    for c in customers:
        spent = Invoice.objects.filter(
            customer=c, status__in=['paid', 'partial']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        spent = float(spent)
        if spent >= 10000:
            vip_count += 1
        elif spent >= 5000:
            platinum_count += 1
        else:
            standard_count += 1
    
    context = {
        'customers': customers,
        'vip_count': vip_count,
        'platinum_count': platinum_count,
        'standard_count': standard_count,
        'title': 'Customers'
    }
    return render(request, 'customers/customer_list.html', context)


@login_required
@manager_required
def customer_detail(request, pk):
    """Display customer details."""
    customer = get_object_or_404(Customer, pk=pk)
    contacts = ContactPerson.objects.filter(customer=customer)
    invoices = customer.invoices.all().order_by('-invoice_date')
    
    # Itemized purchase history
    from apps.billing.models import InvoiceItem
    purchased_items = InvoiceItem.objects.filter(invoice__customer=customer).select_related('product', 'invoice').order_by('-invoice__invoice_date')
    
    context = {
        'customer': customer,
        'contacts': contacts,
        'invoices': invoices,
        'purchased_items': purchased_items,
        'title': customer.name
    }
    return render(request, 'customers/customer_detail.html', context)


@login_required
@manager_required
def customer_create(request):
    """Create new customer."""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer {customer.name} added successfully!')
            return redirect('customers:customer_detail', pk=customer.id)
    else:
        form = CustomerForm()
    
    context = {
        'form': form,
        'title': 'Add Customer'
    }
    return render(request, 'customers/customer_form.html', context)


@login_required
@manager_required
def customer_edit(request, pk):
    """Edit existing customer."""
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f'Customer {customer.name} updated successfully!')
            return redirect('customers:customer_detail', pk=pk)
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
        'title': f'Edit {customer.name}'
    }
    return render(request, 'customers/customer_form.html', context)


@login_required
@manager_required
def customer_delete(request, pk):
    """Delete customer."""
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        name = customer.name
        customer.delete()
        messages.success(request, f'Customer {name} deleted.')
        return redirect('customers:customer_list')
    return render(request, 'customers/customer_confirm_delete.html', {'customer': customer})


@login_required
@manager_required
def category_list(request):
    """Display list of customer categories."""
    categories = CustomerCategory.objects.all()
    return render(request, 'customers/category_list.html', {
        'categories': categories,
        'title': 'Customer Categories'
    })


@login_required
@manager_required
def category_create(request):
    """Create new customer category."""
    if request.method == 'POST':
        form = CustomerCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer Category created successfully!')
            return redirect('customers:category_list')
    else:
        form = CustomerCategoryForm()
    
    return render(request, 'customers/category_form.html', {
        'form': form,
        'title': 'Add Customer Category'
    })
