"""
config/urls.py — Root URL Routing Configuration.

Routes all '/api/' requests to the core application URLs and serves
media files (e.g. uploaded Excel spreadsheets) in development.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [path('django-admin/', admin.site.urls), path('api/', include('core.urls'))]
