"""
Knowledge Document Models for Ignite Buddy RAG.
Stores uploaded PDFs/text files, metadata, and handles ChromaDB vector purge on deletion.
"""
from django.db import models
from server.apps.accounts.models import User, Cohort, Batch


class KnowledgeDocument(models.Model):
    """
    RAG Knowledge Document.
    Tracks files uploaded by administrators to be parsed and indexed
    into the Ignite Buddy knowledge base vector store.
    """
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="knowledge_documents/", null=True, blank=True)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, default="PDF")
    size_bytes = models.BigIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(max_length=20, default="Ready")  # 'Processing' | 'Ready' | 'Failed'
    chunks = models.IntegerField(default=1)
    indexed = models.BooleanField(default=True)
    audience = models.CharField(max_length=100, default="All students")

    # Scoped access by TCS Ignite Cohort or Major Batch
    target_cohort = models.ForeignKey(Cohort, null=True, blank=True, on_delete=models.SET_NULL, related_name="documents")
    target_batch = models.ForeignKey(Batch, null=True, blank=True, on_delete=models.SET_NULL, related_name="documents")

    description = models.TextField(blank=True)
    vector_store = models.CharField(max_length=100, default="SQLite / ChromaDB knowledge base")
    vector_doc_id = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    content = models.TextField(blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.title} ({self.file_type})"
