"""
Signal handlers for accounts app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile when a new User is created.
    
    Args:
        sender: The model class (User)
        instance: The actual instance being saved
        created: Boolean indicating if a new object was created
        **kwargs: Additional keyword arguments
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when the User is saved.
    
    Args:
        sender: The model class (User)
        instance: The actual instance being saved
        **kwargs: Additional keyword arguments
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
