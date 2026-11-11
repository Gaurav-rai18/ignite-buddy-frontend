from django.contrib import admin
from .models import Schedule


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("title", "target_type", "target_cohort", "target_batch", "target_sub_batch", "publish_at", "status", "created_at")
    list_filter = ("target_type", "status", "publish_at")
    search_fields = ("title", "onedrive_url")
