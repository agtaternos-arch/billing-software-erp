"""
Django admin configuration for billing app.
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.billing.models import Invoice, InvoiceItem, Payment, Expense


class InvoiceItemInline(admin.TabularInline):
    """Inline admin for invoice items."""
    model = InvoiceItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'discount_percent']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin interface for Invoice model."""
    list_display = [
        'invoice_number', 'customer_name', 'invoice_date', 'due_date',
        'status_badge', 'total_amount', 'paid_amount', 'balance'
    ]
    list_filter = ['status', 'invoice_date', 'due_date', 'customer']
    search_fields = ['invoice_number', 'customer__name']
    readonly_fields = ['created_at', 'updated_at', 'subtotal', 'tax_amount', 'total_amount', 'invoice_date']
    inlines = [InvoiceItemInline]
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'customer', 'invoice_date', 'due_date')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'tax_amount', 'total_amount', 'paid_amount')
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes', 'terms')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_name(self, obj):
        """Display customer name."""
        return obj.customer.name
    customer_name.short_description = 'Customer'
    
    def status_badge(self, obj):
        """Display status as a colored badge."""
        colors = {
            'draft': '#6c757d',
            'sent': '#17a2b8',
            'paid': '#28a745',
            'partial': '#ffc107',
            'overdue': '#dc3545',
            'cancelled': '#999',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; '
            'border-radius: 3px; display: inline-block;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def balance(self, obj):
        """Display remaining balance."""
        balance = obj.remaining_balance
        color = '#28a745' if balance == 0 else '#dc3545' if balance > 0 else '#6c757d'
        return format_html(
            '<span style="color: {}; font-weight: bold;">${:.2f}</span>',
            color,
            balance
        )
    balance.short_description = 'Balance'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model."""
    list_display = [
        'invoice_number', 'amount', 'payment_date', 'payment_method', 'user_name'
    ]
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['invoice__invoice_number', 'reference']
    readonly_fields = ['created_at', 'payment_date']
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('invoice', 'amount', 'payment_method', 'payment_date')
        }),
        ('Reference', {
            'fields': ('reference', 'notes')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def invoice_number(self, obj):
        """Display invoice number."""
        return obj.invoice.invoice_number
    invoice_number.short_description = 'Invoice'
    
    def user_name(self, obj):
        """Display user who recorded payment."""
        return obj.created_by.username if obj.created_by else 'N/A'
    user_name.short_description = 'Recorded By'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """Admin interface for Expense model."""
    list_display = [
        'title', 'category_badge', 'amount', 'date', 'user_name'
    ]
    list_filter = ['category', 'date']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Expense Information', {
            'fields': ('title', 'category', 'amount', 'date')
        }),
        ('Details', {
            'fields': ('description', 'receipt')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def category_badge(self, obj):
        """Display category as a badge."""
        colors = {
            'supplies': '#17a2b8',
            'utilities': '#ffc107',
            'rent': '#6c757d',
            'salary': '#28a745',
            'transportation': '#007bff',
            'meals': '#fd7e14',
            'maintenance': '#dc3545',
            'other': '#9c27b0',
        }
        color = colors.get(obj.category, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; display: inline-block;">{}</span>',
            color,
            obj.get_category_display()
        )
    category_badge.short_description = 'Category'
    
    def user_name(self, obj):
        """Display user who recorded expense."""
        return obj.created_by.username if obj.created_by else 'N/A'
    user_name.short_description = 'Recorded By'
