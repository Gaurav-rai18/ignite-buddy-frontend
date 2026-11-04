"""
Core application configuration for the Ignite Buddy system.
Defines default auto field settings and the core application name for Django.
"""
from django.apps import AppConfig
class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
