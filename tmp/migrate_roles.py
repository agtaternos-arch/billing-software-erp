import os
import django
import sys

# Add project to path
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User
from apps.accounts.models import UserProfile

# Fix roles: Map old strings to new ones
ROLE_MAP = {
    'admin': 'owner',
    'staff': 'manager',
    'viewer': 'cashier',
}

profiles_updated = 0
for old_role, new_role in ROLE_MAP.items():
    count = UserProfile.objects.filter(role=old_role).update(role=new_role)
    profiles_updated += count
    if count > 0:
        print(f"Updated {count} profiles from '{old_role}' to '{new_role}'.")

# Also ensure 'admin' user is definitely 'owner'
try:
    admin_user = User.objects.get(username='admin')
    if hasattr(admin_user, 'profile'):
        if admin_user.profile.role != 'owner':
            admin_user.profile.role = 'owner'
            admin_user.profile.save()
            profiles_updated += 1
            print("Ensured admin user is owner.")
except User.DoesNotExist:
    pass

print(f"Migration Complete. Total Updated: {profiles_updated}")
