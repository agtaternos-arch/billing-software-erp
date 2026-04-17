"""
Django admin configuration for customers app.
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.customers.models import Customer, ContactPerson, CustomerCategory


class ContactPersonInline(admin.TabularInline):
    """Inline admin for contact persons."""
    model = ContactPerson
    extra = 1
    fields = ['name', 'title', 'email', 'phone', 'is_primary']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Admin interface for Customer model."""
    list_display = [
        'name', 'email', 'phone', 'city', 'invoice_count',
        'status_badge', 'credit_limit'
    ]
    list_filter = ['is_active', 'country', 'created_at']
    search_fields = ['name', 'email', 'phone', 'company_name']
    readonly_fields = ['created_at', 'updated_at', 'total_invoices', 'total_spent']
    inlines = [ContactPersonInline]
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'company_name', 'email', 'phone', 'alt_phone', 'is_active')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Business', {
            'fields': ('tax_id', 'credit_limit')
        }),
        ('Additional', {
            'fields': ('notes',)
        }),
        ('Statistics', {
            'fields': ('total_invoices', 'total_spent'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display active/inactive status."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 3px; display: inline-block;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; '
                'border-radius: 3px; display: inline-block;">✗ Inactive</span>'
            )
    status_badge.short_description = 'Status'
    
    def invoice_count(self, obj):
        """Display number of invoices."""
        count = obj.total_invoices
        return format_html(
            '<span style="background-color: #17a2b8; color: white; padding: 3px 8px; '
            'border-radius: 3px; display: inline-block;">{} invoices</span>',
            count
        )
    invoice_count.short_description = 'Invoices'


@admin.register(ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    """Admin interface for ContactPerson model."""
    list_display = [
        'name', 'customer', 'title', 'email', 'phone', 'primary_badge'
    ]
    list_filter = ['is_primary', 'customer', 'created_at']
    search_fields = ['name', 'email', 'phone', 'customer__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('customer', 'name', 'title')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'is_primary')
        }),
        ('Audit', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def primary_badge(self, obj):
        """Indicate if this is the primary contact."""
        if obj.is_primary:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; '
                'border-radius: 3px; display: inline-block;">★ Primary</span>'
            )
        return '-'
    primary_badge.short_description = 'Primary'


@admin.register(CustomerCategory)
class CustomerCategoryAdmin(admin.ModelAdmin):
    """Admin interface for CustomerCategory model."""
    list_display = ['name', 'discount_percent', 'customer_count']
    search_fields = ['name']
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description', 'discount_percent')
        }),
    )
    
    def customer_count(self, obj):
        """Display count of customers in this category."""
        # Assuming there's a many-to-many relationship or a method
        return 0  # Update this based on actual relationship
    customer_count.short_description = 'Customers'
