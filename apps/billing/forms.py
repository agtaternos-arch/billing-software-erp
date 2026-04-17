"""
Forms for billing module.
"""
from django import forms
from apps.billing.models import Invoice, InvoiceItem, Payment, Expense


class InvoiceForm(forms.ModelForm):
    """Form for creating/editing invoices."""
    class Meta:
        model = Invoice
        fields = ['customer', 'due_date', 'notes', 'terms']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'terms': forms.TextInput(attrs={'class': 'form-control'}),
        }


class InvoiceItemForm(forms.ModelForm):
    """Form for invoice line items."""
    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity', 'unit_price', 'discount_percent']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
        }


class PaymentForm(forms.ModelForm):
    """Form for recording payments."""
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'payment_method', 'reference', 'notes']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ExpenseForm(forms.ModelForm):
    """Form for recording expenses."""
    class Meta:
        model = Expense
        fields = ['title', 'category', 'amount', 'date', 'description', 'receipt']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'receipt': forms.FileInput(attrs={'class': 'form-control'}),
        }
