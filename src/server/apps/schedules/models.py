"""
Schedule Models for Ignite Buddy
Stores timetable links and OneDrive schedules scoped by TCS Ignite Cohort/Batch.
"""
from django.db import models
from server.apps.accounts.models import User, Cohort, Batch, SubBatch


class Schedule(models.Model):
    title = models.CharField(max_length=255)
    onedrive_url = models.URLField(blank=True, default="")
    publish_at = models.DateTimeField(null=True, blank=True)

    TARGET_CHOICES = (
        ("ALL", "All Cohorts"),
        ("COHORT", "Specific Cohort"),
        ("BATCH", "Specific Batch"),
        ("SUB_BATCH", "Specific Sub-Batch"),
    )
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, default="ALL")
    target_cohort = models.ForeignKey(Cohort, null=True, blank=True, on_delete=models.SET_NULL, related_name="schedules")
    target_batch = models.ForeignKey(Batch, null=True, blank=True, on_delete=models.SET_NULL, related_name="schedules")
    target_sub_batch = models.ForeignKey(SubBatch, null=True, blank=True, on_delete=models.SET_NULL, related_name="schedules")

    # JSON-backed structured timetable grid (e.g. {"mon": [...], "tue": [...]})
    grid_data = models.JSONField(default=dict, blank=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    status = models.CharField(max_length=20, default="PENDING")
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-publish_at"]

    def __str__(self):
        return f"{self.title} ({self.target_type})"
