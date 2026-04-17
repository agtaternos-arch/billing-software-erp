"""
Customers app configuration
"""
from django.apps import AppConfig


class CustomersConfig(AppConfig):
    """Configuration class for the customers app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.customers'
    verbose_name = 'Customer Management'
