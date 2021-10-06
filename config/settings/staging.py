from .base import *  # noqa: F401


# Project Artitecture Constants
DEBUG = True
ALLOWED_HOSTS = ['*']

# Business Logic Constants
BANK_IP = '54.183.16.194'
MIN_TNBC_ALLOWED = 5  # In TNBC

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
