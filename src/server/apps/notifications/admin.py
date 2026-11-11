"""
Django Admin registration for Notification models.
"""
from django.contrib import admin
from .models import Notification, NotificationRecipient


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient_type", "target_role", "target_cohort", "target_batch", "target_sub_batch", "created_at")
    list_filter = ("recipient_type", "target_role", "created_at")
    search_fields = ("title", "message")


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    list_display = ("notification", "user", "is_read", "read_at", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("notification__title", "user__username", "user__email")
