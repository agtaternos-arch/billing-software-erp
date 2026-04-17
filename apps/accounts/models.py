"""
Accounts app models for authentication and role management.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class UserProfile(models.Model):
    """
    Extended user profile with role information.
    
    Attributes:
        user: One-to-one relationship with Django User model
        role: User role (Admin, Staff, Viewer)
        department: Department affiliation
        phone: Contact phone number
        address: Physical address
        is_active: Whether the user account is active
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    ROLE_CHOICES = [
        ('owner', 'Business Owner'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='cashier')
    department = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Staff / Employment Details
    base_wage = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Base wage or hourly rate')
    shift_start = models.TimeField(null=True, blank=True)
    shift_end = models.TimeField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True, help_text='Staff age/DOB tracking')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        """Return user full name with role."""
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"
    
    def is_owner(self):
        """Check if user has full owner privileges."""
        return self.role == 'owner'
    
    def is_manager(self):
        """Check if user is a manager."""
        return self.role == 'manager'
    
    def is_cashier(self):
        """Check if user is a cashier."""
        return self.role == 'cashier'


class AuditLog(models.Model):
    """
    Audit trail for tracking user actions.
    
    Attributes:
        user: User who performed the action
        action: Description of the action
        model_name: Name of the model that was affected
        object_id: ID of the affected object
        timestamp: When the action occurred
        ip_address: IP address from which action was performed
        changes: JSON of what was changed
    """
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('view', 'Viewed'),
        ('export', 'Exported'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    changes = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', '-timestamp']),
        ]
    
    def __str__(self):
        """Return action description."""
        return f"{self.get_action_display()} {self.model_name} by {self.user} at {self.timestamp}"


class ShiftRecord(models.Model):
    """
    To track working hours for wage calculations.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shifts')
    clock_in = models.DateTimeField(auto_now_add=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'shift_records'
        verbose_name = 'Shift Record'
        verbose_name_plural = 'Shift Records'
        ordering = ['-clock_in']
    
    def __str__(self):
        return f"Shift: {self.user.username} on {self.clock_in.date()}"


class Staff(models.Model):
    """
    Enhanced staff management for payroll and scheduling.
    """
    EMPLOYMENT_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ]
    
    SHIFT_TYPE = [
        ('morning', 'Morning (6 AM - 2 PM)'),
        ('afternoon', 'Afternoon (2 PM - 10 PM)'),
        ('night', 'Night (10 PM - 6 AM)'),
        ('full_day', 'Full Day'),
        ('part_time', 'Part Time'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100, default='Sales')
    
    # Employment Details
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS, default='active')
    date_of_joining = models.DateField(auto_now_add=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Shift Information
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPE, default='full_day')
    shift_start = models.TimeField(null=True, blank=True, help_text='Default shift start time')
    shift_end = models.TimeField(null=True, blank=True, help_text='Default shift end time')
    
    # Salary Information
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Contact Information
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    
    # Banking Details
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'staff'
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Staff Members'
        ordering = ['user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.designation}"
    
    def get_total_earnings(self):
        """Calculate total monthly earnings."""
        total = self.base_salary + float(self.bonus) + float(self.allowances) - float(self.deductions)
        return total
    
    def get_net_salary(self):
        """Calculate net salary after all deductions."""
        total_earnings = self.get_total_earnings()
        return max(total_earnings, 0)


class SalaryRecord(models.Model):
    """
    Monthly salary records for staff members.
    """
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('on_hold', 'On Hold'),
    ]
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='salary_records')
    month = models.DateField(help_text='First day of month for this salary record')
    
    # Salary Components
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Calculations
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Payment Details
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True, default='bank_transfer')
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'salary_records'
        verbose_name = 'Salary Record'
        verbose_name_plural = 'Salary Records'
        unique_together = ('staff', 'month')
        ordering = ['-month']
    
    def __str__(self):
        return f"{self.staff.employee_id} - {self.month.strftime('%B %Y')}"
