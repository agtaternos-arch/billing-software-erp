#!/bin/bash

# Exit on error
set -o errexit

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin1234')"

# Start gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
