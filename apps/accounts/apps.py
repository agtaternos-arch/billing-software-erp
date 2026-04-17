"""
Django app configuration for accounts app.
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration class for the accounts app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'Accounts & Authentication'
    
    def ready(self):
        """Import signal handlers when app is ready."""
        import apps.accounts.signals  # noqa
