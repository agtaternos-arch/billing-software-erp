"""
Authentication views for login, registration, and user management.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from apps.accounts.forms import (
    LoginForm, RegistrationForm, UserProfileForm, AuditLogModelForm
)
from apps.accounts.models import UserProfile, AuditLog, ShiftRecord
from apps.accounts.decorators import owner_required, manager_required, active_user_required
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import timedelta
import json
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Handle user login.
    
    GET: Display login form
    POST: Authenticate user and create session
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    # Use get_or_create to avoid crash when profile missing
                    profile, created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={'role': 'cashier'}
                    )
                    if profile.is_active:
                        login(request, user)
                        logger.info(f"User {username} logged in successfully")
                        
                        # Log the login action
                        AuditLog.objects.create(
                            user=user,
                            action='view',
                            model_name='Authentication',
                            ip_address=get_client_ip(request),
                        )
                        
                        messages.success(request, f'Welcome back, {user.first_name or username}!')
                        
                        # Route based on role
                        if profile.role in ['owner', 'manager']:
                            return redirect('dashboard')
                        else:
                            # Staff/cashier go directly to POS
                            return redirect('billing:pos_terminal')
                    else:
                        messages.error(request, 'Your account has been deactivated. Contact administrator.')
                        logger.warning(f"Login attempt by deactivated user: {username}")
                else:
                    messages.error(request, 'Your account is disabled.')
                    logger.warning(f"Login attempt by disabled user: {username}")
            else:
                messages.error(request, 'Invalid username or password.')
                logger.warning(f"Failed login attempt for username: {username}")
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    Handle user registration (Admin creates staff from dashboard).
    
    GET: Display registration form
    POST: Create new user account
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data.get('first_name', ''),
                    last_name=form.cleaned_data.get('last_name', ''),
                )
                
                # Create user profile with role and shift/wage data
                UserProfile.objects.create(
                    user=user,
                    role=form.cleaned_data.get('role', 'cashier'),
                    phone=form.cleaned_data.get('phone', ''),
                    department=form.cleaned_data.get('department', ''),
                    base_wage=form.cleaned_data.get('base_wage') or 0,
                    shift_start=form.cleaned_data.get('shift_start'),
                    shift_end=form.cleaned_data.get('shift_end'),
                )
                
                logger.info(f"New user registered: {user.username}")
                
                # If admin is creating staff, redirect back to admin dashboard
                if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'owner':
                    AuditLog.objects.create(
                        user=request.user,
                        action='create',
                        model_name='UserProfile',
                        object_id=user.id,
                        ip_address=get_client_ip(request),
                    )
                    messages.success(request, f'Staff account "{user.username}" created successfully!')
                    return redirect('accounts:admin_dashboard')
                else:
                    messages.success(request, 'Registration successful! You can now log in.')
                    return redirect('accounts:login')
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                messages.error(request, f'Registration error: {str(e)}')
        else:
            # Collect form errors and display them
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{error}")
            if error_messages:
                messages.error(request, ' | '.join(error_messages))
            
            # If admin is creating staff, redirect back with error
            if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'owner':
                return redirect('accounts:admin_dashboard')
    else:
        form = RegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required(login_url='accounts:login')
@owner_required
@require_http_methods(["POST"])
def delete_staff_view(request, profile_id):
    """Soft delete a staff member."""
    from django.shortcuts import get_object_or_404
    profile = get_object_or_404(UserProfile, id=profile_id)
    
    # Don't allow users to delete themselves
    if profile.user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('accounts:admin_dashboard')
        
    profile.is_active = False
    profile.user.is_active = False
    profile.save()
    profile.user.save()
    
    AuditLog.objects.create(
        user=request.user,
        action='delete',
        model_name='UserProfile',
        object_id=profile.id,
        ip_address=get_client_ip(request),
    )
    
    messages.success(request, f'Staff member {profile.user.username} has been deactivated.')
    return redirect('accounts:admin_dashboard')


@login_required(login_url='accounts:login')
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """
    Display and update user profile.
    
    GET: Display user profile
    POST: Update user profile information
    """
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            logger.info(f"User {request.user.username} updated their profile")
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/profile.html', {'form': form, 'profile': profile})


@login_required(login_url='accounts:login')
def logout_view(request):
    """Handle user logout."""
    username = request.user.username
    logout(request)
    logger.info(f"User {username} logged out")
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required(login_url='accounts:login')
@owner_required
def user_list(request):
    """
    List all users (Admin only).
    
    Displays all registered users with their roles and status.
    """
    users = User.objects.select_related('profile').all()
    
    # Search and filtering
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    if request.method == 'POST':
        # Quick inline staff edit logic
        user_id = request.POST.get('user_id')
        wage = request.POST.get('wage')
        shift_start = request.POST.get('shift_start')
        shift_end = request.POST.get('shift_end')
        date_of_birth = request.POST.get('date_of_birth')
        if user_id:
            u = User.objects.get(id=user_id)
            if wage: u.profile.base_wage = wage
            if shift_start: u.profile.shift_start = shift_start
            if shift_end: u.profile.shift_end = shift_end
            if date_of_birth: u.profile.date_of_birth = date_of_birth
            if 'first_name' in request.POST: u.first_name = request.POST.get('first_name')
            if 'last_name' in request.POST: u.last_name = request.POST.get('last_name')
            u.save()
            u.profile.save()
            messages.success(request, f"Updated staff details for {u.username}")
            return redirect('accounts:user_list')

    return render(request, 'accounts/user_list.html', {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'role_choices': UserProfile.ROLE_CHOICES,
    })


@login_required(login_url='accounts:login')
@owner_required
def audit_log_view(request):
    """
    Display audit logs (Admin only).
    
    Shows history of all user actions in the system.
    """
    logs = AuditLog.objects.select_related('user').all().order_by('-timestamp')
    
    # Search and filtering
    user_filter = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    if action_filter:
        logs = logs.filter(action=action_filter)
    if model_filter:
        logs = logs.filter(model_name__icontains=model_filter)
    
    return render(request, 'accounts/audit_log.html', {
        'logs': logs,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'action_choices': AuditLog.ACTION_CHOICES,
    })


@login_required(login_url='accounts:login')
@owner_required
def admin_dashboard_view(request):
    """
    Powerful Admin Command Center with deep metrics and management.
    """
    from apps.billing.models import Invoice, Payment, Expense, InvoiceItem
    from apps.inventory.models import Product, Category
    from apps.customers.models import Customer
    
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    
    # 1. CORE METRICS (This Month)
    monthly_invoices = Invoice.objects.filter(invoice_date__gte=start_of_month, status='paid')
    monthly_revenue = monthly_invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    monthly_expenses = Expense.objects.filter(date__gte=start_of_month).aggregate(Sum('amount'))['amount__sum'] or 0
    net_profit = monthly_revenue - monthly_expenses
    
    # 2. PRODUCT RANKING (Top 10 by Revenue)
    product_ranking = InvoiceItem.objects.values(
        'product__name'
    ).annotate(
        total_revenue=Sum(F('quantity') * F('unit_price')),
        total_qty=Sum('quantity')
    ).order_by('-total_revenue')[:10]
    
    # 3. CATEGORY BREAKDOWN
    category_sales = InvoiceItem.objects.values(
        'product__category__name'
    ).annotate(
        total=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total')
    
    # 4. STAFF PERFORMANCE & WAGES
    staff_profiles = UserProfile.objects.select_related('user').all()
    
    # 5. SECURITY & AUDIT
    recent_logs = AuditLog.objects.select_related('user').all().order_by('-timestamp')[:10]
    
    # 6. CHART DATA (Sales Trend - Last 30 Days)
    sales_labels = []
    sales_values = []
    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        sales_labels.append(date.strftime('%b %d'))
        val = Invoice.objects.filter(invoice_date=date, status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        sales_values.append(float(val))

    context = {
        'title': 'Admin Command Center',
        'monthly_revenue': monthly_revenue,
        'monthly_expenses': monthly_expenses,
        'net_profit': net_profit,
        'product_ranking': product_ranking,
        'top_products': product_ranking,
        'category_sales': category_sales,
        'staff_profiles': staff_profiles,
        'recent_logs': recent_logs,
        'sales_labels': sales_labels,
        'sales_values': sales_values,
        'today': today,
        'products': Product.objects.filter(is_active=True).order_by('name'),
        'active_tab': 'overview'
    }
    return render(request, 'accounts/admin_dashboard.html', context)


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
@login_required
@manager_required
def settings_view(request):
    """Business settings and configuration."""
    context = {
        'title': 'System Settings',
        'business_name': 'Torvix POS Core',
        'currency': '₹',
        'tax_rate': 18,
    }
    if request.method == 'POST':
        # Placeholder for saving settings logic
        messages.success(request, "Settings updated successfully!")
        return redirect('accounts:settings')
    return render(request, 'accounts/settings_page.html', context)
