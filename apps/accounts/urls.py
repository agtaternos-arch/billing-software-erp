"""
URL patterns for accounts app including admin panel.
"""
from django.urls import path
from apps.accounts import views
from apps.accounts import admin_views

app_name = 'accounts'

urlpatterns = [
    # Auth URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('staff/', views.user_list, name='user_list'),
    path('settings/', views.settings_view, name='settings'),
    path('audit-logs/', views.audit_log_view, name='audit_log'),
    
    # Legacy admin-dashboard (redirect)
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # Staff management actions
    path('staff/<int:profile_id>/delete/', views.delete_staff_view, name='delete_staff'),
]

# Admin Panel URLs (namespace: admin)
admin_urlpatterns = [
    # Main Dashboard
    path('', admin_views.admin_dashboard, name='dashboard'),
    
    # Staff Management
    path('staff/', admin_views.staff_management, name='staff_management'),
    path('staff/add/', admin_views.staff_add, name='staff_add'),
    path('staff/<int:staff_id>/', admin_views.staff_detail, name='staff_detail'),
    path('staff/<int:staff_id>/edit/', admin_views.staff_edit, name='staff_edit'),
    
    # User Management
    path('users-management/', admin_views.user_management, name='user_management'),
    path('users/add/', admin_views.user_add, name='user_add'),
    
    # Expense Management
    path('expenses/', admin_views.expense_management, name='expense_management'),
    
    # Audit & Logs
    path('audit-logs/', admin_views.audit_logs, name='audit_logs'),
    
    # Reports
    path('reports/', admin_views.reports_analytics, name='reports_analytics'),
]
