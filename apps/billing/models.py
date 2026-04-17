"""
Billing app models for invoices and payment tracking.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid
import os


class Invoice(models.Model):
    """
    Sales invoices with line items and payment tracking.
    
    Attributes:
        invoice_number: Unique invoice number
        customer: Customer being invoiced
        invoice_date: Date invoice was issued
        due_date: Payment due date
        status: Invoice status (draft, sent, paid, partial, overdue, cancelled)
        subtotal: Total before tax
        tax_amount: Tax amount
        total_amount: Grand total
        paid_amount: Amount paid so far
        notes: Additional notes
        terms: Payment terms
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('pending', 'Pending (Pay Later)'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.PROTECT,
        related_name='invoices'
    )
    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    notes = models.TextField(blank=True, null=True)
    terms = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        default='Net 30'
    )
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['customer', '-invoice_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        """Return invoice number with status."""
        return f"INV-{self.invoice_number} ({self.get_status_display()})"
    
    @property
    def remaining_balance(self):
        """Calculate remaining balance to be paid."""
        return self.total_amount - self.paid_amount
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue."""
        if self.status in ['paid', 'cancelled']:
            return False
        return timezone.now().date() > self.due_date

    @property
    def payment_method_label(self):
        """Dynamic invoice type label (CASH, UPI, TAB)."""
        # If it's on tab, it's a CREDIT INVOICE or TAB RECEIPT
        if self.status == 'pending':
            return "CREDIT INVOICE"
        
        # Check associated payments
        payments = self.payments.all()
        if not payments.exists():
            return "UNPAID INVOICE"
        
        method = payments.first().payment_method
        if method == 'cash': return "CASH INVOICE"
        if method == 'upi': return "UPI RECEIPT"
        if method == 'card': return "CARD RECEIPT"
        return "TAX INVOICE"

    def calculate_totals(self):
        """Recalculate invoice totals from line items."""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.tax_amount = self.subtotal * Decimal('0.10')  # 10% default tax
        self.total_amount = self.subtotal + self.tax_amount
        return self.total_amount


class InvoiceItem(models.Model):
    """
    Line items in an invoice.
    
    Attributes:
        invoice: Foreign key to Invoice
        product: Product being sold
        quantity: Quantity sold
        unit_price: Price per unit
        discount_percent: Discount percentage on line item
        tax_rate: Tax rate for this item
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        db_table = 'invoice_items'
    
    def __str__(self):
        """Return item description."""
        return f"{self.product.name} x{self.quantity}"
    
    @property
    def line_total(self):
        """Calculate line total after discount."""
        subtotal = self.quantity * self.unit_price
        discount = subtotal * (self.discount_percent / Decimal('100'))
        return subtotal - discount


class Payment(models.Model):
    """
    Payment records for invoices.
    
    Attributes:
        invoice: Invoice being paid
        amount: Payment amount
        payment_date: Date payment was received
        payment_method: Method of payment (cash, check, bank transfer, credit card)
        reference: Payment reference number
        notes: Additional notes
    """
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('upi', 'UPI / QR'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('credit_memo', 'Credit Memo'),
        ('other', 'Other'),
    ]
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Reference number (check #, transaction ID, etc.)'
    )
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date']
    
    def __str__(self):
        """Return payment description."""
        return f"Payment of {self.amount} for {self.invoice}"
    
    def save(self, *args, **kwargs):
        """Update invoice paid amount when payment is saved."""
        super().save(*args, **kwargs)
        self.invoice.paid_amount = self.invoice.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        # Update invoice status
        if self.invoice.paid_amount >= self.invoice.total_amount:
            self.invoice.status = 'paid'
        elif self.invoice.paid_amount > 0:
            self.invoice.status = 'partial'
        
        self.invoice.save(update_fields=['paid_amount', 'status'])


class Expense(models.Model):
    """
    Track business expenses for reporting.
    
    Attributes:
        title: Expense title
        category: Expense category
        amount: Expense amount
        date: Date of expense
        description: Detailed description
        receipt: Attached receipt
        created_by: User who recorded expense
    """
    CATEGORIES = [
        ('supplies', 'Office Supplies'),
        ('utilities', 'Utilities'),
        ('rent', 'Rent'),
        ('salary', 'Salary'),
        ('transportation', 'Transportation'),
        ('meals', 'Meals & Entertainment'),
        ('maintenance', 'Maintenance & Repairs'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    receipt = models.FileField(
        upload_to='receipts/',
        blank=True,
        null=True
    )
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='expenses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'expenses'
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'
        ordering = ['-date']
    
    def __str__(self):
        """Return expense title."""
        return f"{self.title} - {self.amount}"
