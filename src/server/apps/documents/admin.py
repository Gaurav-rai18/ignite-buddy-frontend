from django.contrib import admin
from .models import KnowledgeDocument


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "file_name", "file_type", "size_bytes", "status", "chunks", "target_cohort", "target_batch", "uploaded_at")
    list_filter = ("file_type", "status", "indexed", "target_cohort")
    search_fields = ("title", "file_name", "description")

