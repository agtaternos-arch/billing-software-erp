"""
Django admin configuration for inventory app.
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.inventory.models import Product, Supplier, Category, StockMovement, PurchaseOrder, PurchaseOrderItem


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Admin interface for Supplier model."""
    list_display = ['name', 'contact_person', 'email', 'phone', 'payment_terms', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Supplier Information', {
            'fields': ('name', 'is_active')
        }),
        ('Contact', {
            'fields': ('contact_person', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'country')
        }),
        ('Terms', {
            'fields': ('payment_terms',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    list_display = ['name', 'code', 'product_count']
    search_fields = ['name', 'code']
    
    def product_count(self, obj):
        """Display product count for this category."""
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin interface for Product model."""
    list_display = [
        'sku', 'name', 'category', 'unit_price', 'stock_badge',
        'low_stock_status', 'profit_margin', 'is_active'
    ]
    list_filter = ['is_active', 'category', 'supplier', 'created_at']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = ['created_at', 'updated_at', 'profit_margin', 'stock_value']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'description', 'sku', 'is_active')
        }),
        ('Categorization', {
            'fields': ('category', 'supplier')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'unit_price', 'tax_rate', 'profit_margin')
        }),
        ('Stock Management', {
            'fields': (
                'quantity_in_stock', 'low_stock_threshold', 'reorder_quantity', 'stock_value'
            )
        }),
        ('Additional', {
            'fields': ('weight', 'image'),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def stock_badge(self, obj):
        """Display current stock with color indicator."""
        color = '#28a745' if obj.quantity_in_stock > obj.low_stock_threshold else '#dc3545'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; '
            'border-radius: 3px; display: inline-block;">{} units</span>',
            color,
            obj.quantity_in_stock
        )
    stock_badge.short_description = 'Stock'
    
    def low_stock_status(self, obj):
        """Indicate if product is low on stock."""
        if obj.is_low_stock:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">⚠️ LOW</span>'
            )
        return '✓ OK'
    low_stock_status.short_description = 'Status'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Admin interface for StockMovement model."""
    list_display = [
        'product', 'movement_type_badge', 'quantity', 'reference', 'created_by', 'created_at'
    ]
    list_filter = ['movement_type', 'created_at', 'product']
    search_fields = ['product__name', 'reference']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Movement Details', {
            'fields': ('product', 'movement_type', 'quantity', 'reference')
        }),
        ('Information', {
            'fields': ('notes', 'created_by', 'created_at')
        }),
    )
    
    def movement_type_badge(self, obj):
        """Display movement type with icon."""
        colors = {
            'purchase': '#28a745',
            'sales': '#17a2b8',
            'adjustment': '#ffc107',
            'return': '#6c757d',
            'damaged': '#dc3545',
        }
        icons = {
            'purchase': '📦',
            'sales': '🛒',
            'adjustment': '🔧',
            'return': '↩️',
            'damaged': '⚠️',
        }
        color = colors.get(obj.movement_type, '#6c757d')
        icon = icons.get(obj.movement_type, '')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; display: inline-block;">{} {}</span>',
            color,
            icon,
            obj.get_movement_type_display()
        )
    movement_type_badge.short_description = 'Type'


class PurchaseOrderItemInline(admin.TabularInline):
    """Inline admin for purchase order items."""
    model = PurchaseOrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'received_quantity']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """Admin interface for PurchaseOrder model."""
    list_display = [
        'po_number', 'supplier', 'order_date', 'expected_delivery',
        'status_badge', 'total_amount'
    ]
    list_filter = ['status', 'order_date', 'expected_delivery', 'supplier']
    search_fields = ['po_number', 'supplier__name']
    readonly_fields = ['order_date', 'created_at']
    inlines = [PurchaseOrderItemInline]
    
    fieldsets = (
        ('PO Information', {
            'fields': ('po_number', 'supplier')
        }),
        ('Dates', {
            'fields': ('order_date', 'expected_delivery')
        }),
        ('Status & Amount', {
            'fields': ('status', 'total_amount')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status as a colored badge."""
        colors = {
            'pending': '#ffc107',
            'received': '#28a745',
            'partial': '#17a2b8',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; display: inline-block;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
