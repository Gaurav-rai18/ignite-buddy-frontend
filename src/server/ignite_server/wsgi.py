"""
WSGI config for Ignite Buddy server.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.ignite_server.settings")
application = get_wsgi_application()

