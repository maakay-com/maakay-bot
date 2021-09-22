import os
from .base import *  # noqa: F401


# Project Artitecture Constants
DEBUG = False
ALLOWED_HOSTS = ['*']

# Business Logic Constants
BANK_IP = '54.183.16.194'
MIN_TNBC_ALLOWED = 100  # In TNBC

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['POSTGRES_DB'],
        'USER': os.environ['POSTGRES_USER'],
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST': os.environ['POSTGRES_HOST'],
        'PORT': os.environ['POSTGRES_PORT']
    }
}
