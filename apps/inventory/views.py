"""
Django views for inventory app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from decimal import Decimal
from apps.accounts.decorators import manager_required
from .models import Product, Supplier, Category, StockMovement
from .forms import ProductForm, SupplierForm, CategoryForm


@login_required
@manager_required
def product_list(request):
    """Display list of products with performance intelligence."""
    from apps.billing.models import InvoiceItem
    from django.db.models import Sum
    
    from django.db import models
    products = Product.objects.filter(is_active=True).select_related('category', 'supplier').all()
    categories = Category.objects.all()
    low_stock_count = Product.objects.filter(is_active=True, quantity_in_stock__lte=models.F('low_stock_threshold')).count()
    
    # Calculate top sellers for the Intelligence Sidebar
    top_ids = InvoiceItem.objects.values('product_id').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:3]
    top_products = Product.objects.filter(id__in=[p['product_id'] for p in top_ids])
    
    context = {
        'products': products,
        'categories': categories,
        'top_products': top_products,
        'low_stock_count': low_stock_count,
        'title': 'Products'
    }
    return render(request, 'inventory/product_list.html', context)


@login_required
@manager_required
def product_detail(request, pk):
    """Display product details."""
    product = get_object_or_404(Product, pk=pk)
    stock_movements = StockMovement.objects.filter(product=product).order_by('-created_at')
    
    context = {
        'product': product,
        'stock_movements': stock_movements,
        'title': product.name
    }
    return render(request, 'inventory/product_detail.html', context)


@login_required
@manager_required
def product_create(request):
    """Create new product."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product {product.name} created successfully!')
            return redirect('inventory:product_detail', pk=product.id)
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Add Product'
    }
    return render(request, 'inventory/product_form.html', context)


@login_required
@manager_required
def product_edit(request, pk):
    """Edit existing product."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product {product.name} updated successfully!')
            return redirect('inventory:product_list')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'title': f'Edit {product.name}'
    }
    return render(request, 'inventory/product_form.html', context)


@login_required
@manager_required
def product_delete(request, pk):
    """Delete product."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product {product_name} deleted.')
        return redirect('inventory:product_list')
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})


@login_required
@manager_required
def product_restock(request, pk):
    """Quick restock a product."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 0))
        if qty > 0:
            # StockMovement.save() auto-updates product.quantity_in_stock
            StockMovement.objects.create(
                product=product,
                movement_type='in',
                quantity=qty,
                notes='Quick restock via inventory page',
                created_by=request.user
            )
            messages.success(request, f'Restocked {qty} units of {product.name}. New total: {product.quantity_in_stock + qty}')
        else:
            messages.error(request, 'Quantity must be greater than 0.')
    return redirect('inventory:product_list')


@login_required
@manager_required
def product_scan(request):
    """Handle AI Label Scan for products."""
    if request.method == 'POST' and request.FILES.get('label_photo'):
        photo = request.FILES['label_photo']
        # Simulated AI logic for the wow factor
        # In a real app, this would use pytesseract or an external AI API
        from .ml_utils import analyze_label
        extracted_data = analyze_label(photo)
        
        # Pass extracted data to the create form as initial values
        initial_data = {
            'name': extracted_data.get('name', ''),
            'unit_price': extracted_data.get('price', 0),
            'sku': extracted_data.get('sku', ''),
        }
        form = ProductForm(initial=initial_data)
        messages.info(request, "AI Analysis Complete! Please verify the details below.")
        
        return render(request, 'inventory/product_form.html', {
            'form': form,
            'title': 'Verify Scanned Product',
            'extracted_preview': extracted_data
        })
        
    return render(request, 'inventory/product_scan.html', {'title': 'Scan Product Label'})


@login_required
@manager_required
def supplier_list(request):
    """List suppliers."""
    suppliers = Supplier.objects.all()
    return render(request, 'inventory/supplier_list.html', {
        'suppliers': suppliers,
        'title': 'Suppliers'
    })


@login_required
@manager_required
def supplier_create(request):
    """Add supplier."""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'inventory/supplier_form.html', {'form': form, 'title': 'Add Supplier'})


@login_required
@manager_required
def supplier_edit(request, pk):
    """Edit supplier."""
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    return render(request, 'inventory/supplier_form.html', {'form': form, 'title': 'Edit Supplier'})


@login_required
@manager_required
def category_list(request):
    """List categories."""
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {
        'categories': categories,
        'title': 'Categories'
    })


@login_required
@manager_required
def category_create(request):
    """Add category."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventory:category_list')
    else:
        form = CategoryForm()
    return render(request, 'inventory/category_form.html', {'form': form, 'title': 'Add Category'})

@login_required
@manager_required
@require_POST
def update_discount(request):
    """Update discount for a product from the Command Center."""
    product_id = request.POST.get('product_id')
    discount_percent = request.POST.get('discount_percent', 0)
    
    try:
        product = Product.objects.get(id=product_id)
        product.discount_percent = Decimal(str(discount_percent))
        product.save(update_fields=['discount_percent'])
        messages.success(request, f'Discount of {discount_percent}% applied to {product.name}')
    except Product.DoesNotExist:
        messages.error(request, 'Product not found.')
    except Exception as e:
        messages.error(request, f'Error updating discount: {str(e)}')
        
    return redirect('accounts:admin_dashboard')

