"""
Admin Dashboard Views - Comprehensive metrics, staff management, expenses, and analytics.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q, Avg, F, DecimalField
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import json
from decimal import Decimal

from apps.billing.models import Invoice, Payment, Expense
from apps.inventory.models import Product, StockMovement
from apps.customers.models import Customer
from .models import Staff, SalaryRecord, UserProfile, AuditLog


def is_admin_or_manager(user):
    """Check if user is admin or manager."""
    if not user.is_authenticated:
        return False
    try:
        profile = user.profile
        return profile.role in ['owner', 'manager'] or user.is_staff
    except:
        return user.is_staff


@login_required
@user_passes_test(is_admin_or_manager)
def admin_dashboard(request):
    """
    Main admin dashboard with comprehensive metrics and analytics.
    """
    context = {}
    
    # ========== DATE RANGE CALCULATIONS ==========
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)
    start_of_week = today - timedelta(days=today.weekday())
    last_30_days = today - timedelta(days=30)
    
    # ========== SALES METRICS ==========
    # Total Revenue
    total_revenue = Invoice.objects.filter(status__in=['sent', 'partial', 'paid']).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Monthly Revenue
    monthly_revenue = Invoice.objects.filter(
        status__in=['sent', 'partial', 'paid'],
        invoice_date__gte=start_of_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Today's Revenue
    today_revenue = Invoice.objects.filter(
        status__in=['sent', 'partial', 'paid'],
        invoice_date=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Total Invoices
    total_invoices = Invoice.objects.count()
    paid_invoices = Invoice.objects.filter(status='paid').count()
    pending_invoices = Invoice.objects.filter(status__in=['draft', 'sent', 'partial']).count()
    overdue_invoices = Invoice.objects.filter(status='overdue').count()
    
    # Average Invoice Value
    avg_invoice = Invoice.objects.filter(status__in=['sent', 'partial', 'paid']).aggregate(
        avg=Avg('total_amount')
    )['avg'] or 0
    
    # ========== PAYMENTS METRICS ==========
    total_payments = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    monthly_payments = Payment.objects.filter(
        payment_date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # ========== EXPENSES METRICS ==========
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    monthly_expenses = Expense.objects.filter(
        expense_date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Expenses by category
    expense_categories = Expense.objects.filter(
        expense_date__gte=start_of_month
    ).values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # ========== INVENTORY METRICS ==========
    total_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(
        current_stock__lt=F('reorder_level'),
        is_active=True
    ).count()
    
    # Calculate stock value by summing (current_stock * cost_price)
    stock_value_qs = Product.objects.filter(is_active=True).aggregate(
        value=Sum(F('current_stock') * F('cost_price'), output_field=DecimalField())
    )
    total_stock_value = stock_value_qs['value'] or 0
    
    # ========== TOP PRODUCTS BY SALES ==========
    top_products = Invoice.objects.filter(
        status__in=['sent', 'partial', 'paid']
    ).values(
        'items__product__name'
    ).annotate(
        total_quantity=Sum('items__quantity'),
        total_revenue=Sum(F('items__quantity') * F('items__unit_price'))
    ).order_by('-total_revenue')[:10]
    
    # ========== CUSTOMER METRICS ==========
    total_customers = Customer.objects.count()
    active_customers = Customer.objects.filter(is_active=True).count()
    
    # Top customers by revenue
    top_customers = Invoice.objects.filter(
        status__in=['sent', 'partial', 'paid']
    ).values('customer__name').annotate(
        total_spent=Sum('total_amount'),
        invoice_count=Count('id')
    ).order_by('-total_spent')[:5]
    
    # ========== STAFF METRICS ==========
    total_staff = Staff.objects.filter(employment_status='active').count()
    staff_by_department = Staff.objects.filter(
        employment_status='active'
    ).values('department').annotate(count=Count('id'))
    
    # Monthly staff costs
    total_monthly_salary = Staff.objects.filter(
        employment_status='active'
    ).aggregate(total=Sum('base_salary'))['total'] or 0
    
    # Recent salary payments
    recent_salaries = SalaryRecord.objects.filter(
        payment_status='paid'
    ).select_related('staff').order_by('-payment_date')[:10]
    
    # ========== CHART DATA PREPARATION ==========
    # Revenue Trend (Last 30 days)
    revenue_trend = []
    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        revenue = Invoice.objects.filter(
            status__in=['sent', 'partial', 'paid'],
            invoice_date=date
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        revenue_trend.append({
            'date': date.strftime('%m-%d'),
            'revenue': float(revenue)
        })
    
    # Top 5 Products Sales
    top_5_products = list(top_products[:5])
    
    # Expense Category Distribution
    expense_dist = {
        'labels': [e['category'] for e in expense_categories[:7]],
        'data': [float(e['total']) for e in expense_categories[:7]]
    }
    
    # Payment Status Distribution
    payment_status_data = {
        'labels': ['Paid', 'Partial', 'Pending', 'Overdue'],
        'data': [paid_invoices, Invoice.objects.filter(status='partial').count(), 
                 pending_invoices, overdue_invoices]
    }
    
    # Staff by Department
    dept_names = [d['department'] for d in staff_by_department]
    dept_counts = [d['count'] for d in staff_by_department]
    
    # ========== CONTEXT DATA ==========
    context = {
        'page_title': 'Admin Dashboard',
        
        # Sales Metrics
        'total_revenue': float(total_revenue),
        'monthly_revenue': float(monthly_revenue),
        'today_revenue': float(today_revenue),
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'pending_invoices': pending_invoices,
        'overdue_invoices': overdue_invoices,
        'avg_invoice': float(avg_invoice),
        
        # Payments & Expenses
        'total_payments': float(total_payments),
        'monthly_payments': float(monthly_payments),
        'total_expenses': float(total_expenses),
        'monthly_expenses': float(monthly_expenses),
        'profit': float(total_revenue - total_expenses),
        'monthly_profit': float(monthly_revenue - monthly_expenses),
        'expense_categories': list(expense_categories),
        
        # Inventory Metrics
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'total_stock_value': float(total_stock_value),
        
        # Top Sales Products
        'top_products': top_products[:5],
        'top_customers': top_customers,
        
        # Staff Metrics
        'total_staff': total_staff,
        'staff_by_department': staff_by_department,
        'total_monthly_salary': float(total_monthly_salary),
        'recent_salaries': recent_salaries,
        
        # Chart Data (JSON Ready)
        'revenue_trend_labels': [r['date'] for r in revenue_trend],
        'revenue_trend_data': [r['revenue'] for r in revenue_trend],
        'top_products_labels': [p.get('items__product__name', 'Unknown')[:20] for p in top_5_products],
        'top_products_data': [float(p.get('total_revenue', 0)) for p in top_5_products],
        'expense_dist': json.dumps(expense_dist),
        'payment_status': json.dumps(payment_status_data),
        'staff_departments': json.dumps({
            'labels': dept_names or ['No Data'],
            'data': dept_counts or [0]
        }),
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def staff_management(request):
    """
    Staff management interface with add/edit/delete functionality.
    """
    staff_members = Staff.objects.all().select_related('user').order_by('-employment_status')
    
    context = {
        'page_title': 'Staff Management',
        'staff_members': staff_members,
        'total_staff': staff_members.filter(employment_status='active').count(),
        'inactive_staff': staff_members.filter(employment_status='inactive').count(),
    }
    
    return render(request, 'admin/staff_management.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def staff_detail(request, staff_id):
    """
    View staff member details and salary history.
    """
    staff = get_object_or_404(Staff, id=staff_id)
    salary_records = staff.salary_records.all().order_by('-month')
    shifts = staff.user.shifts.all().order_by('-clock_in')[:30]
    
    context = {
        'page_title': f'Staff: {staff.user.get_full_name()}',
        'staff': staff,
        'salary_records': salary_records[:12],
        'recent_shifts': shifts,
        'total_shifts_30d': shifts.count(),
    }
    
    return render(request, 'admin/staff_detail.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def staff_add(request):
    """
    Add new staff member and create associated user account.
    """
    if request.method == 'POST':
        # Create User
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            context = {'error': 'Username already exists', 'page_title': 'Add Staff'}
            return render(request, 'admin/staff_form.html', context, status=400)
        
        # Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create UserProfile
        UserProfile.objects.get_or_create(user=user)
        
        # Create Staff
        staff = Staff.objects.create(
            user=user,
            employee_id=f"EMP-{user.id:05d}",
            designation=request.POST.get('designation', 'Staff'),
            department=request.POST.get('department', 'Sales'),
            shift_type=request.POST.get('shift_type', 'full_day'),
            base_salary=request.POST.get('base_salary', 0),
            phone=request.POST.get('phone', ''),
            address=request.POST.get('address', ''),
            bank_name=request.POST.get('bank_name', ''),
            account_number=request.POST.get('account_number', ''),
        )
        
        return redirect('admin:staff_detail', staff_id=staff.id)
    
    context = {'page_title': 'Add New Staff Member'}
    return render(request, 'admin/staff_form.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def staff_edit(request, staff_id):
    """
    Edit staff member details.
    """
    staff = get_object_or_404(Staff, id=staff_id)
    
    if request.method == 'POST':
        staff.designation = request.POST.get('designation', staff.designation)
        staff.department = request.POST.get('department', staff.department)
        staff.shift_type = request.POST.get('shift_type', staff.shift_type)
        staff.base_salary = request.POST.get('base_salary', staff.base_salary)
        staff.bonus = request.POST.get('bonus', staff.bonus)
        staff.allowances = request.POST.get('allowances', staff.allowances)
        staff.deductions = request.POST.get('deductions', staff.deductions)
        staff.phone = request.POST.get('phone', staff.phone)
        staff.employment_status = request.POST.get('employment_status', staff.employment_status)
        staff.save()
        
        # Update user name if provided
        if request.POST.get('first_name') or request.POST.get('last_name'):
            staff.user.first_name = request.POST.get('first_name', staff.user.first_name)
            staff.user.last_name = request.POST.get('last_name', staff.user.last_name)
            staff.user.save()
        
        return redirect('admin:staff_detail', staff_id=staff.id)
    
    context = {
        'page_title': f'Edit: {staff.user.get_full_name()}',
        'staff': staff,
        'is_edit': True
    }
    return render(request, 'admin/staff_form.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def expense_management(request):
    """
    Expense management interface.
    """
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    expenses = Expense.objects.all().order_by('-expense_date')
    monthly_expenses = Expense.objects.filter(
        expense_date__gte=start_of_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    expense_by_category = Expense.objects.filter(
        expense_date__gte=start_of_month
    ).values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    context = {
        'page_title': 'Expense Management',
        'expenses': expenses[:100],
        'total_monthly_expenses': float(monthly_expenses),
        'expense_by_category': expense_by_category,
    }
    
    return render(request, 'admin/expense_management.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def audit_logs(request):
    """
    View audit trail of all system actions.
    """
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:500]
    
    # Group by action type
    action_counts = AuditLog.objects.values('action').annotate(count=Count('id'))
    
    context = {
        'page_title': 'Audit Logs',
        'logs': logs,
        'action_counts': action_counts,
        'total_logs': AuditLog.objects.count(),
    }
    
    return render(request, 'admin/audit_logs.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def user_management(request):
    """
    Manage system users and their roles.
    """
    users = User.objects.all().select_related('profile').order_by('-date_joined')
    
    context = {
        'page_title': 'User Management',
        'users': users,
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
    }
    
    return render(request, 'admin/user_management.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def user_add(request):
    """
    Add new user account.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role', 'cashier')
        
        if User.objects.filter(username=username).exists():
            context = {'error': 'Username already exists', 'page_title': 'Add User'}
            return render(request, 'admin/user_form.html', context, status=400)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        profile = UserProfile.objects.get_or_create(user=user)[0]
        profile.role = role
        profile.save()
        
        return redirect('admin:user_management')
    
    context = {'page_title': 'Add New User'}
    return render(request, 'admin/user_form.html', context)


@login_required
@user_passes_test(is_admin_or_manager)
def reports_analytics(request):
    """
    Comprehensive reports and analytics view.
    """
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)
    
    # Sales Report
    monthly_sales = Invoice.objects.filter(
        status__in=['sent', 'partial', 'paid'],
        invoice_date__gte=start_of_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    yearly_sales = Invoice.objects.filter(
        status__in=['sent', 'partial', 'paid'],
        invoice_date__gte=start_of_year
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Monthly breakdown
    monthly_breakdown = Invoice.objects.filter(
        status__in=['sent', 'partial', 'paid'],
        invoice_date__gte=start_of_year
    ).extra(
        select={'month': 'DATE_TRUNC(\'month\', invoice_date)'}
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')
    
    context = {
        'page_title': 'Reports & Analytics',
        'monthly_sales': float(monthly_sales),
        'yearly_sales': float(yearly_sales),
        'monthly_breakdown': monthly_breakdown,
    }
    
    return render(request, 'admin/reports.html', context)
