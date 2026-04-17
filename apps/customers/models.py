"""
Customers app models for managing customer information.
"""
from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from django.utils import timezone
from decimal import Decimal


class StoreSetting(models.Model):
    """Global configuration settings for the store."""
    points_conversion_rate = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('100.00'),
        help_text="Amount in ₹ required to earn 1 loyalty point"
    )
    
    class Meta:
        db_table = 'store_settings'
        verbose_name = 'Store Setting'
        verbose_name_plural = 'Store Settings'
        
    def __str__(self):
        return "Global Store Settings"

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj


class Customer(models.Model):
    """
    Customer information with contact details and purchase history.
    
    Attributes:
        name: Customer's business or full name
        email: Email address for notifications
        phone: Primary contact phone number
        alt_phone: Alternate phone number
        address: Complete address
        city: City name
        state: State/Province
        postal_code: Postal/ZIP code
        country: Country name
        company_name: Company/Business name
        tax_id: Tax identification number
        is_active: Whether the customer is active
        credit_limit: Maximum credit allowed
        notes: Additional notes about customer
        created_at: Account creation date
        updated_at: Last update date
    """
    name = models.CharField(
        max_length=200,
        db_index=True,
        help_text='Customer name or company name'
    )
    email = models.EmailField(
        blank=True, null=True,
        help_text='Primary email address (Optional)'
    )
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Invalid phone format')],
        help_text='Phone number'
    )
    alt_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Alternate phone number'
    )
    address = models.TextField(help_text='Street address')
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='USA')
    company_name = models.CharField(max_length=200, blank=True, null=True)
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Tax ID or GST number'
    )
    is_active = models.BooleanField(default=True, db_index=True)
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Maximum credit allowed for this customer'
    )
    notes = models.TextField(blank=True, null=True)
    due_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Current outstanding balance owed by the customer'
    )
    loyalty_points = models.IntegerField(
        default=0,
        help_text='Accumulated loyalty points'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customers'
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def __str__(self):
        """Return customer name with active status."""
        status = '✓' if self.is_active else '✗'
        return f"{self.name} ({status})"
    
    @property
    def full_address(self):
        """Return formatted full address."""
        parts = [
            self.address,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join(part for part in parts if part)
    
    @property
    def total_invoices(self):
        """Get count of total invoices for this customer."""
        from apps.billing.models import Invoice
        return Invoice.objects.filter(customer=self).count()
    
    @property
    def total_spent(self):
        """Get total amount spent by customer."""
        from apps.billing.models import Invoice
        return Invoice.objects.filter(
            customer=self,
            status__in=['paid', 'partial']
        ).aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0

    @property
    def loyalty_tier(self):
        """Return loyalty tier based on total spent."""
        spent = float(self.total_spent)
        if spent >= 10000:
            return 'vip'
        elif spent >= 5000:
            return 'platinum'
        return 'standard'


class ContactPerson(models.Model):
    """
    Contact persons associated with a customer.
    
    Attributes:
        customer: Foreign key to Customer
        name: Contact person's name
        title: Job title
        email: Email address
        phone: Phone number
        is_primary: Whether this is the primary contact
    """
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='contact_persons'
    )
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'contact_persons'
        verbose_name = 'Contact Person'
        verbose_name_plural = 'Contact Persons'
    
    def __str__(self):
        """Return contact person name and title."""
        title = f" - {self.title}" if self.title else ""
        return f"{self.name}{title}"
    
    def save(self, *args, **kwargs):
        """Ensure only one primary contact per customer."""
        if self.is_primary:
            ContactPerson.objects.filter(
                customer=self.customer, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class CustomerCategory(models.Model):
    """
    Categories for segmenting customers.
    
    Attributes:
        name: Category name
        description: Category description
        discount_percent: Default discount for this category
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Default discount percentage for this category'
    )
    
    class Meta:
        db_table = 'customer_categories'
        verbose_name = 'Customer Category'
        verbose_name_plural = 'Customer Categories'
    
    def __str__(self):
        """Return category name."""
        return self.name
