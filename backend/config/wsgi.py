"""
WSGI config for the Ignite Buddy backend project.

It exposes the WSGI callable as a module-level variable named `application`.
Used by WSGI-compliant web servers (such as Gunicorn or uWSGI) in production.
"""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()
