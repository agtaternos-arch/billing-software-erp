#!/bin/bash

# Exit on error
set -o errexit

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
# Create or update superuser
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); from apps.accounts.models import UserProfile; u, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}); u.set_password('admin@123456'); u.save(); UserProfile.objects.get_or_create(user=u, defaults={'role': 'owner'}); print('Admin user and profile updated/created successfully')"

# Start gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
