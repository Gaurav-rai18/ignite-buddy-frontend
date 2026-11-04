# Admin site registration for core app models
# This file registers the Django admin interfaces for the models defined in core/models.py.
# It allows staff users to manage schedules, locations, batches, etc. via the default
# Django admin UI.

from django.contrib import admin
from .models import Broadcast, ScheduledLink, SiteSetting
admin.site.register(Broadcast)
admin.site.register(ScheduledLink)
admin.site.register(SiteSetting)
