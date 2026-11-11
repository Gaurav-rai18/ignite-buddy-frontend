from django.contrib import admin
from .models import SystemSetting, ExamControl


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "updated_at", "updated_by")
    search_fields = ("key", "value", "description")


@admin.register(ExamControl)
class ExamControlAdmin(admin.ModelAdmin):
    list_display = ("trainee_name", "device_id", "sub_batch", "batch", "lab", "exam_mode", "last_seen")
    list_filter = ("exam_mode", "sub_batch", "batch", "lab")
    search_fields = ("trainee_name", "device_id", "user__username")
