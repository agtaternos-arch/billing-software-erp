import os
import django
import sys

# Add project to path
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User

try:
    u = User.objects.get(username='admin')
    if hasattr(u, 'profile'):
        print(f"ROLE_IS:{u.profile.role}")
    else:
        print("No Profile")
except Exception as e:
    print(f"Error: {e}")
