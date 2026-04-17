#!/bin/bash

# Exit on error
set -o errexit

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
