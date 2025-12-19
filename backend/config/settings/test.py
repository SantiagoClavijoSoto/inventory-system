"""
Test Django settings - uses SQLite for faster tests.
"""
from .base import *  # noqa: F401, F403

DEBUG = False

# Use SQLite for tests (faster and no permissions needed)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable password hashers for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Email backend for tests (no actual emails)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Set very high throttle rates for tests (effectively unlimited)
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '10000/minute',
    'user': '10000/minute',
    'login': '10000/minute',
    'verification': '10000/minute',
}

# Disable Celery during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
