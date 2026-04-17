"""
Django admin configuration for accounts app.
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.accounts.models import UserProfile, AuditLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    list_display = [
        'user_full_name', 'username', 'role_badge', 'is_active', 
        'department', 'created_at'
    ]
    list_filter = ['role', 'is_active', 'created_at', 'department']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_active')
        }),
        ('Role & Department', {
            'fields': ('role', 'department')
        }),
        ('Contact Information', {
            'fields': ('phone', 'address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_full_name(self, obj):
        """Display user's full name."""
        return obj.user.get_full_name() or obj.user.username
    user_full_name.short_description = 'Full Name'
    
    def username(self, obj):
        """Display username."""
        return obj.user.username
    username.short_description = 'Username'
    
    def role_badge(self, obj):
        """Display role as a colored badge."""
        colors = {
            'admin': '#dc3545',
            'staff': '#007bff',
            'viewer': '#6c757d',
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; display: inline-block;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = 'Role'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model."""
    list_display = [
        'user_username', 'action_badge', 'model_name', 'object_id', 'timestamp', 'ip_address'
    ]
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'model_name', 'ip_address']
    readonly_fields = [
        'user', 'action', 'model_name', 'object_id', 'timestamp', 'ip_address', 'changes'
    ]
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Action Details', {
            'fields': ('user', 'action', 'model_name', 'object_id')
        }),
        ('Technical Information', {
            'fields': ('timestamp', 'ip_address', 'changes'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual addition of audit logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent changing audit logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs."""
        return False
    
    def user_username(self, obj):
        """Display username or 'System' if user is None."""
        return obj.user.username if obj.user else 'System'
    user_username.short_description = 'User'
    
    def action_badge(self, obj):
        """Display action as a colored badge."""
        colors = {
            'create': '#28a745',
            'update': '#ffc107',
            'delete': '#dc3545',
            'view': '#17a2b8',
            'export': '#6610f2',
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; display: inline-block;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Action'
