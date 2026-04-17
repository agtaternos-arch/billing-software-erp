"""
Forms for inventory module.
"""
from django import forms
from apps.inventory.models import Product, Supplier, Category, PurchaseOrder


class ProductForm(forms.ModelForm):
    """Form for creating/editing products."""
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'barcode', 'sku', 'category', 'supplier',
            'unit_price', 'cost_price', 'quantity_in_stock',
            'low_stock_threshold', 'tax_rate', 'reorder_quantity', 'gst_number', 'image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scan or type barcode'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'quantity_in_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'reorder_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class SupplierForm(forms.ModelForm):
    """Form for creating/editing suppliers."""
    class Meta:
        model = Supplier
        fields = [
            'name', 'contact_person', 'email', 'phone',
            'address', 'city', 'country', 'payment_terms', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CategoryForm(forms.ModelForm):
    """Form for creating/editing categories."""
    class Meta:
        model = Category
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PurchaseOrderForm(forms.ModelForm):
    """Form for creating purchase orders."""
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'expected_delivery', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'expected_delivery': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
