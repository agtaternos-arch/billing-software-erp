"""
Reports app models for historical data and analytics.
"""
from django.db import models
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from decimal import Decimal


class SalesReport(models.Model):
    """
    Daily sales summary for reporting and analytics.
    
    Attributes:
        report_date: Date of the report
        total_sales: Total sales for the day
        total_orders: Number of orders
        average_order_value: Average order value
        tax_collected: Total tax collected
    """
    report_date = models.DateField(unique=True, db_index=True)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sales_reports'
        verbose_name = 'Sales Report'
        verbose_name_plural = 'Sales Reports'
        ordering = ['-report_date']
    
    def __str__(self):
        """Return report date."""
        return f"Sales Report - {self.report_date}"


class InventoryReport(models.Model):
    """
    Daily inventory snapshot for stock tracking.
    
    Attributes:
        report_date: Date of the report
        total_items: Total number of item types
        total_quantity: Total quantity in stock
        total_value: Total stock value
        low_stock_items: Count of items below threshold
    """
    report_date = models.DateField(unique=True, db_index=True)
    total_items = models.IntegerField(default=0)
    total_quantity = models.IntegerField(default=0)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    low_stock_items = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_reports'
        verbose_name = 'Inventory Report'
        verbose_name_plural = 'Inventory Reports'
        ordering = ['-report_date']
    
    def __str__(self):
        """Return report date."""
        return f"Inventory Report - {self.report_date}"


class CustomerReport(models.Model):
    """
    Customer metrics and performance tracking.
    
    Attributes:
        report_date: Date of the report
        new_customers: New customers added
        active_customers: Active customers
        total_revenue: Revenue from customers
        average_customer_revenue: Average revenue per customer
    """
    report_date = models.DateField(unique=True, db_index=True)
    new_customers = models.IntegerField(default=0)
    active_customers = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_customer_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'customer_reports'
        verbose_name = 'Customer Report'
        verbose_name_plural = 'Customer Reports'
        ordering = ['-report_date']
    
    def __str__(self):
        """Return report date."""
        return f"Customer Report - {self.report_date}"


class ExpenseReport(models.Model):
    """
    Monthly expense tracking and categorization.
    
    Attributes:
        report_month: Month of the report (stored as YYYY-MM)
        total_expenses: Total expenses for the month
        category_breakdown: JSON breakdown by category
        variance: Variance from budget
    """
    report_month = models.CharField(
        max_length=7,
        unique=True,
        db_index=True,
        help_text='Format: YYYY-MM'
    )
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    category_breakdown = models.JSONField(default=dict, blank=True)
    variance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'expense_reports'
        verbose_name = 'Expense Report'
        verbose_name_plural = 'Expense Reports'
        ordering = ['-report_month']
    
    def __str__(self):
        """Return report month."""
        return f"Expense Report - {self.report_month}"
    
    @property
    def budget_variance_percent(self):
        """Calculate variance percentage."""
        if self.budget and self.budget > 0:
            return (self.variance / self.budget) * 100
        return 0


class ProfitAndLoss(models.Model):
    """
    Profit and loss statement.
    
    Attributes:
        report_period: Period for P&L (YYYY-MM or YYYY for year)
        total_revenue: Total revenue
        cost_of_goods: Cost of goods sold
        gross_profit: Gross profit
        operating_expenses: Operating expenses
        net_profit: Net profit
    """
    PERIOD_TYPES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    report_period = models.CharField(max_length=10, unique=True, db_index=True)
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES, default='monthly')
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_of_goods = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    operating_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'profit_and_loss'
        verbose_name = 'Profit & Loss'
        verbose_name_plural = 'Profit & Loss'
        ordering = ['-report_period']
    
    def __str__(self):
        """Return P&L period."""
        return f"P&L - {self.report_period}"
    
    @property
    def gross_profit_margin(self):
        """Calculate gross profit margin percentage."""
        if self.total_revenue > 0:
            return (self.gross_profit / self.total_revenue) * 100
        return 0
    
    @property
    def net_profit_margin(self):
        """Calculate net profit margin percentage."""
        if self.total_revenue > 0:
            return (self.net_profit / self.total_revenue) * 100
        return 0
