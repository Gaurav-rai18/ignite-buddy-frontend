"""
Assignment Models

Manages coursework assignments, student tasks, deadlines, and submissions
across the TCS Ignite hierarchy (Cohorts, Batches, Sub-batches/Labs, and Users).
"""
from datetime import datetime, time

from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_date

from server.apps.accounts.models import User, Cohort, Batch, SubBatch


class Assignment(models.Model):
    RECIPIENT_TYPE_CHOICES = [
        ("ALL", "All Users"),
        ("ROLE", "By Role"),
        ("COHORT", "By Cohort"),
        ("BATCH", "By Batch"),
        ("SUB_BATCH", "By Sub-Batch"),
        ("USERS", "Specific Users"),
    ]

    topic = models.CharField(max_length=200, help_text="Title or topic of the assignment")
    subject = models.CharField(max_length=100, help_text="Academic subject or module")
    platform_link = models.URLField(max_length=500, blank=True, null=True, help_text="External URL (HackerEarth, LeetCode, GitHub, etc.)")
    start_date = models.DateField(default=timezone.now)
    deadline = models.DateField(help_text="Submission deadline (date)")
    deadline_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Precise submission deadline (date and time, timezone-aware). Falls back to end of `deadline` day.",
    )
    message = models.TextField(help_text="Detailed assignment description and instructions")

    recipient_type = models.CharField(
        max_length=20,
        choices=RECIPIENT_TYPE_CHOICES,
        default="ALL",
    )
    target_role = models.CharField(max_length=20, blank=True, null=True)
    target_cohort = models.ForeignKey(
        Cohort,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments",
    )
    target_batch = models.ForeignKey(
        Batch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="single_batch_assignments",
    )
    target_sub_batch = models.ForeignKey(
        SubBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="single_subbatch_assignments",
    )
    target_batches = models.ManyToManyField(
        Batch,
        blank=True,
        related_name="targeted_assignments",
    )
    target_sub_batches = models.ManyToManyField(
        SubBatch,
        blank=True,
        related_name="targeted_assignments",
    )
    audience = models.CharField(max_length=200, default="All students")

    # Publish workflow: a draft is created without notifying anyone and becomes
    # visible/publishable later. Defaults to True so the historical behaviour
    # (create == publish) is preserved for existing callers.
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Deadline reminder bookkeeping — guarantees the 24h / 1h reminders fire at most once.
    reminder_24h_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_1h_sent_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"

    def __str__(self):
        return f"{self.topic} ({self.subject}) - Due {self.deadline}"

    @property
    def due_at(self):
        """Timezone-aware deadline instant.

        Uses the precise ``deadline_at`` when provided, otherwise the end of the
        ``deadline`` day (23:59:59) interpreted in the active timezone.
        """
        if self.deadline_at:
            if timezone.is_naive(self.deadline_at):
                return timezone.make_aware(self.deadline_at)
            return self.deadline_at
        deadline = self.deadline
        if isinstance(deadline, str):  # e.g. an instance built straight from JSON before reload
            deadline = parse_date(deadline)
        if not deadline:
            return None
        naive = datetime.combine(deadline, time(23, 59, 59))
        return timezone.make_aware(naive) if timezone.is_naive(naive) else naive

    @property
    def is_past_due(self):
        due = self.due_at
        if due is None:
            return False
        return timezone.now() > due


class AssignmentRecipient(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUBMITTED", "Submitted"),
        ("EVALUATED", "Evaluated"),
    ]

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_tasks",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )
    submission_link = models.URLField(max_length=500, blank=True, null=True)
    submission_text = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    grade = models.CharField(max_length=20, blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    resubmission_required = models.BooleanField(
        default=False,
        help_text="When set, deadline reminders are sent again even after a submission.",
    )
    notified_24h_at = models.DateTimeField(null=True, blank=True)
    notified_1h_at = models.DateTimeField(null=True, blank=True)
    evaluated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluated_tasks",
    )
    evaluated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("assignment", "user")
        ordering = ["-created_at"]
        verbose_name = "Assignment Recipient"
        verbose_name_plural = "Assignment Recipients"

    def __str__(self):
        return f"{self.user.username} - {self.assignment.topic} [{self.status}]"

    @property
    def needs_reminder(self):
        """Trainees who have not submitted (or whose submission was sent back) get deadline reminders."""
        if self.resubmission_required:
            return True
        return self.status == "PENDING"
