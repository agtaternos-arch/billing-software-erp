# config/__init__.py
import sys
import os

# Skip Celery import when running as frozen desktop app (PyInstaller)
# Celery is only needed for server deployments with async task queues
if not getattr(sys, 'frozen', False) and os.environ.get('DJANGO_SETTINGS_MODULE') != 'config.desktop_settings':
    from .celery import app as celery_app
    __all__ = ('celery_app',)
else:
    __all__ = ()
