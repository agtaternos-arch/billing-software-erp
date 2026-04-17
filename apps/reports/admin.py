"""
Django admin configuration for reports app.
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.reports.models import SalesReport, InventoryReport, CustomerReport, ExpenseReport, ProfitAndLoss


@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    """Admin interface for SalesReport model (read-only)."""
    list_display = [
        'report_date', 'total_sales', 'total_orders', 'average_order_value', 'tax_collected'
    ]
    list_filter = ['report_date']
    readonly_fields = ['report_date', 'total_sales', 'total_orders', 'average_order_value', 'tax_collected', 'created_at']
    
    def has_add_permission(self, request):
        """Reports are auto-generated, prevent manual addition."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Reports should be read-only."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of reports."""
        return False


@admin.register(InventoryReport)
class InventoryReportAdmin(admin.ModelAdmin):
    """Admin interface for InventoryReport model (read-only)."""
    list_display = [
        'report_date', 'total_items', 'total_quantity', 'total_value', 'low_stock_items'
    ]
    list_filter = ['report_date']
    readonly_fields = ['report_date', 'total_items', 'total_quantity', 'total_value', 'low_stock_items', 'created_at']
    
    def has_add_permission(self, request):
        """Reports are auto-generated, prevent manual addition."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Reports should be read-only."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of reports."""
        return False


@admin.register(CustomerReport)
class CustomerReportAdmin(admin.ModelAdmin):
    """Admin interface for CustomerReport model (read-only)."""
    list_display = [
        'report_date', 'new_customers', 'active_customers', 'total_revenue', 'average_customer_revenue'
    ]
    list_filter = ['report_date']
    readonly_fields = ['report_date', 'new_customers', 'active_customers', 'total_revenue', 'average_customer_revenue', 'created_at']
    
    def has_add_permission(self, request):
        """Reports are auto-generated, prevent manual addition."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Reports should be read-only."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of reports."""
        return False


@admin.register(ExpenseReport)
class ExpenseReportAdmin(admin.ModelAdmin):
    """Admin interface for ExpenseReport model."""
    list_display = [
        'report_month', 'total_expenses', 'budget', 'variance_display'
    ]
    list_filter = ['report_month']
    readonly_fields = ['report_month', 'total_expenses', 'category_breakdown', 'variance', 'created_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_month', 'period_type')
        }),
        ('Amounts', {
            'fields': ('total_expenses', 'budget', 'variance')
        }),
        ('Details', {
            'fields': ('category_breakdown',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Reports are auto-generated, prevent manual addition."""
        return False
    
    def variance_display(self, obj):
        """Display variance with color indicator."""
        variance_pct = obj.budget_variance_percent if obj.budget_variance_percent else 0
        color = '#28a745' if variance_pct <= 0 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">${:.2f} ({:.1f}%)</span>',
            color,
            obj.variance,
            variance_pct
        )
    variance_display.short_description = 'Variance'


@admin.register(ProfitAndLoss)
class ProfitAndLossAdmin(admin.ModelAdmin):
    """Admin interface for ProfitAndLoss model (read-only)."""
    list_display = [
        'report_period', 'period_type', 'total_revenue', 'net_profit', 'margin_display'
    ]
    list_filter = ['period_type', 'report_period']
    readonly_fields = [
        'report_period', 'period_type', 'total_revenue', 'cost_of_goods',
        'gross_profit', 'operating_expenses', 'net_profit', 'created_at',
        'gross_profit_margin', 'net_profit_margin'
    ]
    
    fieldsets = (
        ('Period Information', {
            'fields': ('report_period', 'period_type')
        }),
        ('Revenue & COGS', {
            'fields': ('total_revenue', 'cost_of_goods', 'gross_profit', 'gross_profit_margin')
        }),
        ('Operations & Profit', {
            'fields': ('operating_expenses', 'net_profit', 'net_profit_margin')
        }),
        ('Audit', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Reports are auto-generated, prevent manual addition."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Reports should be read-only."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of reports."""
        return False
    
    def margin_display(self, obj):
        """Display profit margins."""
        return format_html(
            'Gross: {:.1f}% | Net: {:.1f}%',
            obj.gross_profit_margin,
            obj.net_profit_margin
        )
    margin_display.short_description = 'Margins'
