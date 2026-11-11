"""
Telemetry Models for Ignite Buddy
Stores trainee interaction history and application activity events in Django ORM for admin auditing.
"""
from django.db import models
from server.apps.accounts.models import User


class ChatLog(models.Model):
    """
    Central record of trainee conversational queries and assistant responses.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_logs")
    role = models.CharField(max_length=20)  # 'user', 'assistant', 'system'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.role}): {self.content[:40]}"


class ActivityEvent(models.Model):
    """
    Trainee application usage / active window sampling events.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_events")
    app = models.CharField(max_length=255)
    title = models.CharField(max_length=500, blank=True)
    start_ts = models.DateTimeField(db_index=True)
    end_ts = models.DateTimeField(null=True, blank=True)
    idle = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_ts"]
        indexes = [
            models.Index(fields=["user", "-start_ts"]),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.app}"


class ActivitySummary(models.Model):
    """
    Aggregated daily/weekly summaries for performance and attendance tracking.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_summaries")
    day = models.DateField(db_index=True)
    kind = models.CharField(max_length=50, default="daily")
    summary_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "day", "kind")
        ordering = ["-day"]

    def __str__(self):
        return f"{self.user.username} ({self.day})"

