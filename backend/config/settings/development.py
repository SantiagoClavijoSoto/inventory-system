"""
Development Django settings.
"""
import os
from .base import *  # noqa: F401, F403

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# CORS - Allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Email backend for development:
# - Use SMTP if EMAIL_HOST_USER is configured (for testing real emails)
# - Otherwise fallback to console output
if not os.environ.get('EMAIL_HOST_USER'):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# In development, send emails synchronously by default (no Redis/Celery needed)
# This can be overridden by setting SEND_EMAILS_SYNC=False
if 'SEND_EMAILS_SYNC' not in os.environ:
    SEND_EMAILS_SYNC = True

# Debug toolbar (optional - uncomment if installed)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
# INTERNAL_IPS = ['127.0.0.1']

# Logging - more verbose in development
LOGGING['loggers']['django']['level'] = 'DEBUG'
