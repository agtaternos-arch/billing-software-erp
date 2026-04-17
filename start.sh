#!/bin/bash

# Exit on error
set -o errexit

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create or update superuser and FORCE owner role
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
from apps.accounts.models import UserProfile
u, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True})
u.set_password('admin@123456')
u.is_staff = True
u.is_superuser = True
u.save()
profile, p_created = UserProfile.objects.update_or_create(user=u, defaults={'role': 'owner', 'is_active': True})
print(f'Admin user ready. Profile role={profile.role}, created={p_created}')
"

# Start gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
