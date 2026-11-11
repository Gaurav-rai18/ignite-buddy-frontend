"""
Notification Models for Ignite Buddy
Supports campus-wide broadcasts, role-based announcements, and TCS Ignite Cohort/Batch targeting.
"""
from django.db import models
from server.apps.accounts.models import User, Cohort, Batch, SubBatch


class Notification(models.Model):
    """
    Master notification and broadcast record.
    Supports targeting across all levels of the TCS Ignite hierarchy.
    """
    RECIPIENT_CHOICES = (
        ("ALL", "All Users"),
        ("COHORT", "Cohort"),
        ("BATCH", "Batch"),
        ("SUB_BATCH", "Sub-Batch"),
        ("ROLE", "Role"),
        ("USERS", "Specific Users"),
    )

    title = models.CharField(max_length=255)
    message = models.TextField()
    recipient_type = models.CharField(
        max_length=20,
        choices=RECIPIENT_CHOICES,
        default="ALL",
    )

    # Scoped targeting filters
    target_role = models.CharField(max_length=20, null=True, blank=True)
    target_cohort = models.ForeignKey(Cohort, null=True, blank=True, on_delete=models.SET_NULL, related_name="notifications")
    target_batch = models.ForeignKey(Batch, null=True, blank=True, on_delete=models.SET_NULL, related_name="notifications")
    target_sub_batch = models.ForeignKey(SubBatch, null=True, blank=True, on_delete=models.SET_NULL, related_name="notifications")

    is_broadcast = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.recipient_type})"


class NotificationRecipient(models.Model):
    """
    Delivery and inbox tracking record per user.
    Tracks read/unread status without duplicating message bodies.
    """
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="recipients"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications_received"
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("notification", "user")
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.notification.title} -> {self.user.username} (Read: {self.is_read})"
