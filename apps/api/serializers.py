"""
REST API serializers for all models.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile, AuditLog
from apps.customers.models import Customer, ContactPerson, CustomerCategory
from apps.inventory.models import Product, Supplier, Category, StockMovement, PurchaseOrder, PurchaseOrderItem
from apps.billing.models import Invoice, InvoiceItem, Payment, Expense
from apps.reports.models import SalesReport, InventoryReport, CustomerReport, ExpenseReport, ProfitAndLoss


# Account Serializers
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'department', 'phone', 'is_active']


# Customer Serializers
class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model."""
    class Meta:
        model = Customer
        fields = ['id', 'name', 'email', 'phone', 'address', 'city', 'state', 'postal_code', 'country', 'company_name', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class ContactPersonSerializer(serializers.ModelSerializer):
    """Serializer for ContactPerson model."""
    class Meta:
        model = ContactPerson
        fields = ['id', 'customer', 'name', 'title', 'email', 'phone', 'is_primary', 'created_at']


# Inventory Serializers
class SupplierSerializer(serializers.ModelSerializer):
    """Serializer for Supplier model."""
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_person', 'email', 'phone', 'address', 'city', 'country', 'payment_terms', 'is_active', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'code']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    profit_margin = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'sku', 'category', 'category_name', 
            'supplier', 'supplier_name', 'unit_price', 'cost_price', 
            'quantity_in_stock', 'low_stock_threshold', 'is_low_stock', 
            'profit_margin', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for StockMovement model."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = ['id', 'product', 'product_name', 'movement_type', 'quantity', 'reference', 'notes', 'created_by_username', 'created_at']
        read_only_fields = ['created_at']


# Billing Serializers
class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for InvoiceItem model."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = InvoiceItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'discount_percent', 'line_total']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model."""
    items = InvoiceItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    remaining_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'customer', 'customer_name', 'invoice_date', 
            'due_date', 'status', 'subtotal', 'tax_amount', 'total_amount', 
            'paid_amount', 'remaining_balance', 'notes', 'items', 'created_at'
        ]
        read_only_fields = ['created_at', 'invoice_date']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""
    class Meta:
        model = Payment
        fields = ['id', 'invoice', 'amount', 'payment_date', 'payment_method', 'reference', 'notes', 'created_at']
        read_only_fields = ['created_at', 'payment_date']


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for Expense model."""
    class Meta:
        model = Expense
        fields = ['id', 'title', 'category', 'amount', 'date', 'description', 'receipt', 'created_at']
        read_only_fields = ['created_at']


# Report Serializers
class SalesReportSerializer(serializers.ModelSerializer):
    """Serializer for SalesReport model."""
    class Meta:
        model = SalesReport
        fields = ['id', 'report_date', 'total_sales', 'total_orders', 'average_order_value', 'tax_collected']


class InventoryReportSerializer(serializers.ModelSerializer):
    """Serializer for InventoryReport model."""
    class Meta:
        model = InventoryReport
        fields = ['id', 'report_date', 'total_items', 'total_quantity', 'total_value', 'low_stock_items']


class ProfitAndLossSerializer(serializers.ModelSerializer):
    """Serializer for ProfitAndLoss model."""
    gross_profit_margin = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    net_profit_margin = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = ProfitAndLoss
        fields = [
            'id', 'report_period', 'period_type', 'total_revenue', 'cost_of_goods',
            'gross_profit', 'gross_profit_margin', 'operating_expenses', 'net_profit', 'net_profit_margin'
        ]
