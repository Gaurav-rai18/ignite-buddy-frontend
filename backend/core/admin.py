from django.contrib import admin
from .models import Broadcast, ScheduledLink, SiteSetting
admin.site.register(Broadcast)
admin.site.register(ScheduledLink)
admin.site.register(SiteSetting)
