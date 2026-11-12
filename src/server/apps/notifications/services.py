"""
Reusable notification creation service.

Every feature (broadcasts, assignments, deadline reminders, submissions,
evaluations) funnels through :func:`create_notification` so there is a single
code path that:

  * persists the master ``Notification`` row,
  * creates one ``NotificationRecipient`` inbox row per user,
  * pushes a real-time ``trainee.notification`` toast over the channel layer,
  * optionally guards against duplicates through ``dedupe_key``.

This reuses the existing notification infrastructure instead of introducing a
parallel messaging system.
"""
from django.utils import timezone

from .models import Notification, NotificationRecipient
from server.channels_push import send_channel_message
from server.realtime import notifier


def _group_for(user) -> str:
    identifier = getattr(user, "username", None) or getattr(user, "id", None) or str(user)
    return notifier.user_group(str(identifier))


def create_notification(
    *,
    title,
    message,
    users=None,
    recipient_type="USERS",
    target_role=None,
    target_cohort=None,
    target_batch=None,
    target_sub_batch=None,
    category="general",
    priority="normal",
    action_url="",
    action_label="",
    dedupe_key="",
    is_broadcast=True,
    ws_kind="broadcast",
    broadcast_group=None,
    push=True,
):
    """Create a notification and deliver it to ``users``.

    Returns ``(notification, created)``. When ``dedupe_key`` is supplied and a
    notification with that key already exists, the existing row is returned and
    nothing else is created or sent — this is the duplicate-prevention guard.
    """
    if dedupe_key:
        existing = Notification.objects.filter(dedupe_key=dedupe_key).first()
        if existing:
            return existing, False

    notification = Notification.objects.create(
        title=str(title)[:255],
        message=str(message),
        recipient_type=recipient_type,
        target_role=target_role,
        target_cohort=target_cohort,
        target_batch=target_batch,
        target_sub_batch=target_sub_batch,
        category=category,
        priority=priority,
        action_url=(action_url or "")[:500],
        action_label=(action_label or "")[:120],
        dedupe_key=dedupe_key or "",
        is_broadcast=is_broadcast,
    )

    user_list = [u for u in (users or []) if u is not None]
    if user_list:
        NotificationRecipient.objects.bulk_create(
            [NotificationRecipient(notification=notification, user=u) for u in user_list],
            ignore_conflicts=True,
        )

    if push:
        payload = {
            "type": "trainee.notification",
            "kind": ws_kind,
            "notification_id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "text": f"{notification.title}: {notification.message}",
            "priority": priority,
            "category": category,
            "action_url": notification.action_url,
            "action_label": notification.action_label,
            "created_at": timezone.now().isoformat(),
        }
        delivered = set()
        for user in user_list:
            group = _group_for(user)
            if group not in delivered:
                send_channel_message(group, payload)
                delivered.add(group)
        if not user_list and broadcast_group:
            send_channel_message(broadcast_group, payload)

    return notification, True
