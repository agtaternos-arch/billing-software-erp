"""
Inventory app models for managing products, stock, and suppliers.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class Supplier(models.Model):
    """
    Supplier information for product sourcing.
    
    Attributes:
        name: Supplier company name
        contact_person: Contact person name
        email: Email address
        phone: Phone number
        address: Business address
        city: City name
        country: Country name
        payment_terms: Payment terms (e.g., "Net 30")
        is_active: Active/inactive status
    """
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='USA')
    payment_terms = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='e.g., Net 30, Net 60, COD'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'suppliers'
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['name']
    
    def __str__(self):
        """Return supplier name."""
        return self.name


class Category(models.Model):
    """
    Product categories for organization.
    
    Attributes:
        name: Category name
        description: Category description
        code: Unique category code
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=20, unique=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        """Return category name."""
        return self.name


class Product(models.Model):
    """
    Product inventory with stock tracking.
    
    Attributes:
        name: Product name
        description: Product description
        sku: Stock Keeping Unit (unique identifier)
        category: Product category
        supplier: Primary supplier
        unit_price: Selling price per unit
        cost_price: Cost price per unit
        quantity_in_stock: Current stock quantity
        low_stock_threshold: Alert when stock falls below this
        weight: Product weight
        is_active: Active/inactive status
        tax_rate: Tax percentage
        reorder_quantity: Quantity to reorder
    """
    name = models.CharField(max_length=300, db_index=True)
    description = models.TextField(blank=True, null=True)
    sku = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Stock Keeping Unit'
    )
    barcode = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text='Scan barcode or enter manually'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Cost price per unit'
    )
    quantity_in_stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    low_stock_threshold = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        help_text='Alert when stock falls below this quantity'
    )
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text='Weight in kg'
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Discount percentage to apply to this product'
    )
    is_active = models.BooleanField(default=True, db_index=True)
    gst_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='GST/HSN Code'
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Tax percentage'
    )
    reorder_quantity = models.IntegerField(
        default=50,
        validators=[MinValueValidator(1)],
        help_text='Quantity to order when restocking'
    )
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def __str__(self):
        """Return product name with SKU."""
        return f"{self.name} ({self.sku})"
    
    @property
    def is_low_stock(self):
        """Check if product is below low stock threshold."""
        return self.quantity_in_stock <= self.low_stock_threshold
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage."""
        if self.cost_price == 0:
            return 0
        return ((self.unit_price - self.cost_price) / self.cost_price) * 100
    
    @property
    def stock_value(self):
        """Calculate total stock value at cost price."""
        return self.quantity_in_stock * self.cost_price


class StockMovement(models.Model):
    """
    Track all stock movements (in/out).
    
    Attributes:
        product: Product reference
        movement_type: Type of movement (purchase, sales, adjustment, return)
        quantity: Quantity moved
        reference: Reference to source (invoice, PO, etc.)
        notes: Additional notes
        created_by: User who recorded the movement
        created_at: Timestamp
    """
    MOVEMENT_TYPES = [
        ('purchase', 'Purchase Order'),
        ('sales', 'Sales Invoice'),
        ('adjustment', 'Stock Adjustment'),
        ('return', 'Customer Return'),
        ('damaged', 'Damaged/Loss'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField(help_text='Positive for inbound, negative for outbound')
    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Reference number (Invoice, PO, etc.)'
    )
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    def __str__(self):
        """Return movement description."""
        return f"{self.get_movement_type_display()} - {self.product.name} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        """Update product quantity upon saving movement."""
        is_new = self._state.adding
        if is_new:
            # Update product quantity
            self.product.quantity_in_stock += self.quantity
            self.product.save()
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'stock_movements'
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', '-created_at']),
        ]
    
    def __str__(self):
        """Return movement description."""
        direction = '+' if self.quantity > 0 else '-'
        return f"{direction}{abs(self.quantity)} {self.product.sku} ({self.get_movement_type_display()})"


class PurchaseOrder(models.Model):
    """
    Purchase orders for restocking from suppliers.
    
    Attributes:
        po_number: Unique purchase order number
        supplier: Supplier reference
        order_date: Date when order was placed
        expected_delivery: Expected delivery date
        status: Order status (pending, received, cancelled)
        total_amount: Total order amount
        notes: Additional notes
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('partial', 'Partial'),
        ('cancelled', 'Cancelled'),
    ]
    
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='purchase_orders'
    )
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'purchase_orders'
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        ordering = ['-order_date']
    
    def __str__(self):
        """Return PO number with status."""
        return f"PO-{self.po_number} ({self.get_status_display()})"


class PurchaseOrderItem(models.Model):
    """
    Items in a purchase order.
    
    Attributes:
        purchase_order: Foreign key to PurchaseOrder
        product: Product being ordered
        quantity: Quantity ordered
        unit_price: Price per unit
        received_quantity: Quantity received
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    received_quantity = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'purchase_order_items'
    
    def __str__(self):
        """Return item description."""
        return f"{self.product.name} x{self.quantity}"
    
    @property
    def line_total(self):
        """Calculate line total."""
        return self.quantity * self.unit_price
