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

    # Presentation / routing metadata (used by assignment + system notifications).
    category = models.CharField(max_length=32, default="general", db_index=True)
    priority = models.CharField(max_length=16, default="normal")  # normal | high | urgent
    action_url = models.CharField(max_length=500, blank=True, default="", help_text="Deep link opened when the notification is clicked")
    action_label = models.CharField(max_length=120, blank=True, default="")
    dedupe_key = models.CharField(
        max_length=180,
        blank=True,
        default="",
        db_index=True,
        help_text="When set, at most one notification is ever created for this key.",
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
