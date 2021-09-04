import os
from django.core.wsgi import get_wsgi_application


DJANGO_SETTINGS_MODULE = os.environ['DJANGO_SETTINGS_MODULE']
os.environ.setdefault('DJANGO_SETTINGS_MODULE', DJANGO_SETTINGS_MODULE)

application = get_wsgi_application()
