"""
Assignment notification helpers.

Builds the structured, professional messages required by the assignment
feature and delivers them through the shared notification service:

  * ``notify_new_assignment``      -> "New Assignment Posted"
  * ``send_deadline_reminders``    -> "Assignment Due Tomorrow" / "Deadline Approaching"
  * ``notify_submission_received`` -> "Submission Received" (+ faculty copy)
  * ``notify_evaluated``           -> "Assignment Evaluated" / "Feedback Available"

Reminders are idempotent: the per-assignment ``reminder_*_sent_at`` stamps and the
per-recipient ``notified_*_at`` stamps (plus ``Notification.dedupe_key``) make sure
a trainee is never reminded twice, and submitted trainees are skipped unless the
submission was sent back for resubmission.
"""
import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from server.apps.notifications.services import create_notification

log = logging.getLogger("assignments.notifications")

REMINDER_24H_SECONDS = 24 * 3600
REMINDER_1H_SECONDS = 3600


# --------------------------------------------------------------------------- formatting
def format_due(dt):
    """Render a timezone-aware deadline as e.g. '13 Nov 2026, 05:30 PM' in server time."""
    if not dt:
        return ""
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return timezone.localtime(dt).strftime("%d %b %Y, %I:%M %p")


def greeting(user):
    if user is None:
        return "Hi Trainee!"
    name = (getattr(user, "first_name", "") or "").strip() or getattr(user, "username", "") or "Trainee"
    return f"Hi {name}!"


def faculty_name(assignment):
    creator = getattr(assignment, "created_by", None)
    if not creator:
        return "your faculty"
    full = f"{creator.first_name} {creator.last_name}".strip()
    return full or creator.username


def assignment_action_url(assignment):
    return f"/assignments/{assignment.id}"


# --------------------------------------------------------------------------- create / publish
def notify_new_assignment(assignment, users=None):
    """Notify every eligible trainee that a new assignment was published."""
    if users is None:
        users = [r.user for r in assignment.recipients.select_related("user")]
    users = [u for u in users if u is not None]
    due = format_due(assignment.due_at)
    author = faculty_name(assignment)
    created = 0
    for user in users:
        _, was_created = create_notification(
            title="New Assignment Posted",
            message=(
                f"{greeting(user)} A new assignment, {assignment.topic}, has been posted by {author}. "
                f"Please review the instructions and submit your work before {due}.\n\n"
                f"Subject: {assignment.subject}"
            ),
            users=[user],
            category="assignment",
            priority="high",
            action_url=assignment_action_url(assignment),
            action_label="Open assignment",
            dedupe_key=f"assignment:{assignment.id}:new:{user.id}",
            ws_kind="assignment",
        )
        created += 1 if was_created else 0
    return created


def notify_deadline_updated(assignment):
    """Tell already-notified trainees that the deadline moved (also re-arms reminders)."""
    due = format_due(assignment.due_at)
    created = 0
    stamp = timezone.now().isoformat()
    for recipient in assignment.recipients.select_related("user"):
        _, was_created = create_notification(
            title="Deadline Updated",
            message=(
                f"{greeting(recipient.user)} The deadline for '{assignment.topic}' has been updated to {due}. "
                "Please plan your submission accordingly."
            ),
            users=[recipient.user],
            category="assignment",
            priority="high",
            action_url=assignment_action_url(assignment),
            action_label="Open assignment",
            dedupe_key=f"assignment:{assignment.id}:deadline:{stamp}:{recipient.user_id}",
            ws_kind="assignment",
        )
        created += 1 if was_created else 0
    return created


# --------------------------------------------------------------------------- reminders
def _reminder_message(assignment, kind, user):
    due = format_due(assignment.due_at)
    if kind == "24h":
        return (
            "Assignment Due Tomorrow",
            f"{greeting(user)} Your assignment '{assignment.topic}' is due tomorrow. "
            f"Please complete and submit it by {due}.",
        )
    return (
        "Deadline Approaching",
        f"Reminder! Your assignment '{assignment.topic}' is due in 1 hour. "
        "Please submit your work before the deadline.",
    )


def _send_reminder(assignment, kind, now):
    flag = "reminder_24h_sent_at" if kind == "24h" else "reminder_1h_sent_at"
    recipient_flag = "notified_24h_at" if kind == "24h" else "notified_1h_at"
    title, _ = _reminder_message(assignment, kind, None)

    sent = 0
    recipients = assignment.recipients.select_related("user").filter(
        Q(status__in=["PENDING", "SUBMITTED"]) | Q(resubmission_required=True)
    )
    for recipient in recipients:
        if not recipient.needs_reminder:
            continue
        if getattr(recipient, recipient_flag) is not None:
            continue
        # A send-back for resubmission opens a new reminder cycle, so its dedupe
        # key differs from the first cycle and the reminder may legitimately fire again.
        cycle = "first"
        if recipient.resubmission_required and recipient.evaluated_at:
            cycle = recipient.evaluated_at.isoformat()
        _, was_created = create_notification(
            title=title,
            message=_reminder_message(assignment, kind, recipient.user)[1],
            users=[recipient.user],
            category="assignment",
            priority="urgent" if kind == "1h" else "high",
            action_url=assignment_action_url(assignment),
            action_label="Open assignment",
            dedupe_key=f"assignment:{assignment.id}:{kind}:{recipient.user_id}:{cycle}",
            ws_kind="assignment",
        )
        type(recipient).objects.filter(pk=recipient.pk).update(**{recipient_flag: now})
        sent += 1 if was_created else 0

    type(assignment).objects.filter(pk=assignment.pk).update(**{flag: now})
    return sent


def send_deadline_reminders(now=None):
    """Send the 24-hour and 1-hour deadline reminders.

    Idempotent — safe to call on every scheduler tick. The per-recipient
    ``notified_*_at`` stamps + ``Notification.dedupe_key`` guarantee a trainee is
    reminded at most once per reminder cycle, so this returns the number of
    reminder notifications actually created.
    """
    from .models import Assignment

    now = now or timezone.now()
    horizon_start = (now - timedelta(days=1)).date()
    total = 0
    assignments = Assignment.objects.filter(
        is_published=True,
        deadline__gte=horizon_start,
    ).only(
        "id", "topic", "deadline", "deadline_at",
        "reminder_24h_sent_at", "reminder_1h_sent_at",
    )
    for assignment in assignments:
        due = assignment.due_at
        if not due or now > due:
            continue
        seconds_left = (due - now).total_seconds()
        if seconds_left <= REMINDER_1H_SECONDS:
            total += _send_reminder(assignment, "1h", now)
        elif seconds_left <= REMINDER_24H_SECONDS:
            total += _send_reminder(assignment, "24h", now)
    return total


# --------------------------------------------------------------------------- submission / evaluation
def notify_submission_received(recipient):
    """Confirm receipt to the trainee and alert the faculty member who posted it."""
    assignment = recipient.assignment
    stamp = recipient.submitted_at.isoformat() if recipient.submitted_at else timezone.now().isoformat()
    due = format_due(assignment.due_at)

    create_notification(
        title="Submission Received",
        message=(
            f"{greeting(recipient.user)} Your submission for '{assignment.topic}' was received successfully. "
            f"Due date: {due}."
        ),
        users=[recipient.user],
        category="assignment",
        priority="normal",
        action_url=assignment_action_url(assignment),
        action_label="View assignment",
        dedupe_key=f"assignment:{assignment.id}:submitted:{recipient.user_id}:{stamp}",
        ws_kind="assignment",
    )

    faculty = assignment.created_by
    if faculty:
        create_notification(
            title="New Submission Received",
            message=(
                f"{greeting(faculty)} {recipient.user.username} submitted work for '{assignment.topic}'. "
                "You can now review and evaluate the submission."
            ),
            users=[faculty],
            category="assignment",
            priority="normal",
            action_url=assignment_action_url(assignment),
            action_label="Review submission",
            dedupe_key=f"assignment:{assignment.id}:faculty-submit:{recipient.user_id}:{stamp}",
            ws_kind="assignment",
        )


def notify_evaluated(recipient):
    """Tell the trainee their submission was graded; surface feedback when present."""
    assignment = recipient.assignment
    has_feedback = bool((recipient.feedback or "").strip())
    title = "Feedback Available" if has_feedback else "Assignment Evaluated"
    parts = [f"{greeting(recipient.user)} Your submission for '{assignment.topic}' has been evaluated."]
    if recipient.grade:
        parts.append(f"Grade: {recipient.grade}.")
    if has_feedback:
        parts.append(f"Feedback: {recipient.feedback.strip()}")
    stamp = recipient.evaluated_at.isoformat() if recipient.evaluated_at else timezone.now().isoformat()

    create_notification(
        title=title,
        message=" ".join(parts),
        users=[recipient.user],
        category="assignment",
        priority="high",
        action_url=assignment_action_url(assignment),
        action_label="View feedback",
        dedupe_key=f"assignment:{assignment.id}:evaluated:{recipient.user_id}:{stamp}",
        ws_kind="assignment",
    )
