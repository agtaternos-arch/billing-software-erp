"""
Decorators for role-based access control.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
import logging

logger = logging.getLogger(__name__)


def owner_required(view_func):
    """
    Decorator to restrict access to owner users only.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if hasattr(request.user, 'profile') and request.user.profile.role == 'owner':
            return view_func(request, *args, **kwargs)
        else:
            logger.warning(f"Unauthorized owner access attempt by: {request.user.username}")
            messages.error(request, 'You do not have permission to access this page.')
            return HttpResponseForbidden('Owner access required.')
    
    return wrapper


def manager_required(view_func):
    """
    Decorator to restrict access to manager and owner users.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if hasattr(request.user, 'profile') and request.user.profile.role in ['owner', 'manager']:
            return view_func(request, *args, **kwargs)
        else:
            logger.warning(f"Unauthorized manager access attempt by: {request.user.username}")
            messages.error(request, 'Management permission required.')
            return HttpResponseForbidden('Management permission required.')
    
    return wrapper


def active_user_required(view_func):
    """
    Decorator to ensure user is active.
    
    Args:
        view_func: The view function to decorate
        
    Returns:
        Decorated function that checks user active status
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if hasattr(request.user, 'profile') and not request.user.profile.is_active:
            messages.error(request, 'Your account has been deactivated.')
            return HttpResponseForbidden('Your account has been deactivated.')
            
        return view_func(request, *args, **kwargs)
    
    return wrapper
