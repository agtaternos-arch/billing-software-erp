"""
Forms for customers module.
"""
from django import forms
from apps.customers.models import Customer, ContactPerson, CustomerCategory


class CustomerForm(forms.ModelForm):
    """Form for creating/editing customers."""
    class Meta:
        model = Customer
        fields = [
            'name', 'company_name', 'email', 'phone', 'alt_phone',
            'address', 'city', 'state', 'postal_code', 'country',
            'tax_id', 'credit_limit', 'notes', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'alt_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ContactPersonForm(forms.ModelForm):
    """Form for creating/editing contact persons."""
    class Meta:
        model = ContactPerson
        fields = ['customer', 'name', 'title', 'email', 'phone', 'is_primary']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CustomerCategoryForm(forms.ModelForm):
    """Form for creating/editing customer categories."""
    class Meta:
        model = CustomerCategory
        fields = ['name', 'description', 'discount_percent']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
        }
