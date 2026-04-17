import os
import sys
from pathlib import Path
from .settings import *

# When running as a PyInstaller bundle, sys._MEIPASS is the path to the temporary folder
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = Path(sys._MEIPASS).resolve()
    # Use a persistent directory for user data (DB, Media, Logs)
    appdata = os.environ.get('APPDATA')
    if appdata:
        DATA_DIR = Path(appdata).resolve() / 'BillingERP'
    else:
        # Fallback to User Home if APPDATA is somehow missing
        DATA_DIR = Path.home().resolve() / '.torvix_erp'
else:
    BUNDLE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BUNDLE_DIR.resolve()

# Ensure DATA_DIR exists
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / 'logs').mkdir(exist_ok=True)
(DATA_DIR / 'media').mkdir(exist_ok=True)

# Override BASE_DIR for templates and static files inside the bundle
BASE_DIR = BUNDLE_DIR

# Database - Move to persistent DATA_DIR
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DATA_DIR / 'db.sqlite3',
    }
}

# Static and Media files
STATIC_URL = '/static/'
STATIC_ROOT = BUNDLE_DIR / 'staticfiles'
MEDIA_ROOT = DATA_DIR / 'media'

# Disable Whitenoise manifest storage for desktop to avoid relative path errors in 3rd party CSS
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Security Settings for Desktop
DEBUG = False
ALLOWED_HOSTS = ['*']

# Logging to persistent folder
LOGGING['handlers']['file']['filename'] = DATA_DIR / 'logs' / 'erp.log'

# Whitenoise is already in settings.py MIDDLEWARE, but ensure it works
