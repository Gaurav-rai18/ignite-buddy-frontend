from django.contrib import admin
from .models import Assignment, AssignmentRecipient


class AssignmentRecipientInline(admin.TabularInline):
    model = AssignmentRecipient
    extra = 0
    readonly_fields = ("user", "status", "submitted_at", "submission_link")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("topic", "subject", "start_date", "deadline", "recipient_type", "created_by", "created_at")
    list_filter = ("recipient_type", "subject", "created_at", "deadline")
    search_fields = ("topic", "subject", "message", "created_by__username")
    inlines = [AssignmentRecipientInline]


@admin.register(AssignmentRecipient)
class AssignmentRecipientAdmin(admin.ModelAdmin):
    list_display = ("assignment", "user", "status", "submitted_at", "grade", "evaluated_by")
    list_filter = ("status", "submitted_at")
    search_fields = ("user__username", "assignment__topic", "assignment__subject")
