"""
Assignment domain services.

Small, shared helpers so the REST API (admin/faculty panel) and the trainee
desktop WebSocket consumer record a submission through exactly the same code
path — including the shared notification infrastructure.
"""
import logging

from django.utils import timezone

from .models import AssignmentRecipient
from .notifications import notify_submission_received

log = logging.getLogger("assignments.services")


def record_submission(assignment, user, submission_text=None, submission_link=None):
    """Record (or replace) ``user``'s submission for ``assignment``.

    Marks the recipient as SUBMITTED, clears any earlier send-back request and
    pushes the "Submission Received" notifications (trainee + faculty) through
    the shared notification service. Returns the ``AssignmentRecipient``.
    """
    recipient, _ = AssignmentRecipient.objects.get_or_create(
        assignment=assignment,
        user=user,
    )
    recipient.submission_text = submission_text or None
    recipient.submission_link = submission_link or None
    recipient.status = "SUBMITTED"
    recipient.submitted_at = timezone.now()
    recipient.resubmission_required = False
    recipient.save()

    try:
        notify_submission_received(recipient)
    except Exception:  # a notification failure must never lose the submission
        log.exception("Failed to send submission notifications for recipient %s", recipient.id)
    return recipient


def published_assignments_for(user):
    """Published assignments assigned to ``user`` (trainee visibility rule)."""
    from .models import Assignment

    return (
        Assignment.objects.filter(is_published=True, recipients__user=user)
        .select_related("created_by", "target_cohort", "target_batch", "target_sub_batch")
        .prefetch_related("recipients")
        .distinct()
        .order_by("deadline_at", "deadline")
    )


def assignment_payload_for(user):
    """Plain-dict assignment payload for the trainee desktop UI.

    Mirrors the trainee-visible fields of :class:`AssignmentSerializer` without
    needing a DRF request in context.
    """
    payload = []
    for assignment in published_assignments_for(user):
        recipient = next((r for r in assignment.recipients.all() if r.user_id == user.id), None)
        due = assignment.due_at
        author = assignment.created_by
        author_name = (
            f"{author.first_name} {author.last_name}".strip() or author.username
            if author else "Administrator"
        )
        payload.append({
            "id": assignment.id,
            "title": assignment.topic,
            "subject": assignment.subject,
            "instructions": assignment.message,
            "platform_link": assignment.platform_link or "",
            "deadline": assignment.deadline.isoformat() if assignment.deadline else "",
            "due_at": due.isoformat() if due else "",
            "author_name": author_name,
            "is_past_due": assignment.is_past_due,
            "status": recipient.status if recipient else "PENDING",
            "recipient_id": recipient.id if recipient else None,
            "submission_text": (recipient.submission_text or "") if recipient else "",
            "submission_link": (recipient.submission_link or "") if recipient else "",
            "submitted_at": recipient.submitted_at.isoformat() if recipient and recipient.submitted_at else "",
            "grade": (recipient.grade or "") if recipient else "",
            "feedback": (recipient.feedback or "") if recipient else "",
            "resubmission_required": bool(recipient.resubmission_required) if recipient else False,
        })
    return payload
