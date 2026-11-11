from django.contrib import admin
from .models import ChatLog, ActivityEvent, ActivitySummary


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "short_content", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("user__username", "content")

    def short_content(self, obj):
        return obj.content[:50]


@admin.register(ActivityEvent)
class ActivityEventAdmin(admin.ModelAdmin):
    list_display = ("user", "app", "title", "start_ts", "end_ts", "idle")
    list_filter = ("idle", "start_ts")
    search_fields = ("user__username", "app", "title")


@admin.register(ActivitySummary)
class ActivitySummaryAdmin(admin.ModelAdmin):
    list_display = ("user", "day", "kind", "created_at")
    list_filter = ("kind", "day")
    search_fields = ("user__username", "summary_text")

