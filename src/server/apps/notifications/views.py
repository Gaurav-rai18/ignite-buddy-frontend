"""
Notification Views
Manages creation, broadcast history, and user inbox notifications across the TCS Ignite hierarchy.
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationRecipient
from .serializers import NotificationSerializer
from server.apps.accounts.models import User, Cohort, Batch, SubBatch
from server.apps.accounts.permissions import CanManageBroadcasts
from server.channels_push import send_channel_message
from server.realtime import notifier


class BroadcastCreateView(APIView):
    permission_classes = [IsAuthenticated, CanManageBroadcasts]

    def post(self, request):
        title = request.data.get("title", "").strip()
        message = request.data.get("message", "").strip()
        recipient_type = request.data.get("recipient_type", "ALL").upper()
        target_role = request.data.get("target_role")
        target_usernames = request.data.get("target_usernames", [])
        cohort_id = request.data.get("cohort_id") or request.data.get("target_cohort")
        batch_id = request.data.get("batch_id") or request.data.get("target_batch")
        sub_batch_id = request.data.get("sub_batch_id") or request.data.get("target_sub_batch")

        # Multi-select support for batches and sub-batches
        batch_ids = request.data.get("batch_ids") or []
        if not batch_ids and batch_id:
            batch_ids = [batch_id]

        sub_batch_ids = request.data.get("sub_batch_ids") or []
        if not sub_batch_ids and sub_batch_id:
            sub_batch_ids = [sub_batch_id]

        if not title:
            return Response({"error": "Title is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        target_cohort_obj = None
        target_batch_obj = None
        target_sub_batch_obj = None
        target_batches = []
        target_sub_batches = []

        if recipient_type == "ALL":
            users = User.objects.filter(is_active=True)
        elif recipient_type == "ROLE":
            if not target_role:
                return Response({"error": "target_role is required for ROLE recipient type"}, status=status.HTTP_400_BAD_REQUEST)
            users = User.objects.filter(role=target_role, is_active=True)
        elif recipient_type == "COHORT":
            target_cohort_obj = Cohort.objects.filter(id=cohort_id).first()
            if not target_cohort_obj:
                return Response({"error": "Valid cohort_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            users = User.objects.filter(sub_batch__batch__cohort=target_cohort_obj, is_active=True)
        elif recipient_type == "BATCH":
            if not batch_ids:
                return Response({"error": "At least one batch must be selected"}, status=status.HTTP_400_BAD_REQUEST)
            target_batches = list(Batch.objects.filter(id__in=batch_ids))
            if not target_batches:
                return Response({"error": "Selected batch(es) do not exist"}, status=status.HTTP_400_BAD_REQUEST)
            users = User.objects.filter(sub_batch__batch__in=target_batches, is_active=True)
            if len(target_batches) == 1:
                target_batch_obj = target_batches[0]
        elif recipient_type == "SUB_BATCH":
            if not sub_batch_ids:
                return Response({"error": "At least one sub-batch must be selected"}, status=status.HTTP_400_BAD_REQUEST)
            target_sub_batches = list(SubBatch.objects.filter(id__in=sub_batch_ids))
            if not target_sub_batches:
                return Response({"error": "Selected sub-batch(es) do not exist"}, status=status.HTTP_400_BAD_REQUEST)
            users = User.objects.filter(sub_batch__in=target_sub_batches, is_active=True)
            if len(target_sub_batches) == 1:
                target_sub_batch_obj = target_sub_batches[0]
        elif recipient_type == "USERS":
            if not target_usernames:
                return Response({"error": "Select at least one user"}, status=status.HTTP_400_BAD_REQUEST)
            users = User.objects.filter(username__in=target_usernames)
            if users.count() != len(target_usernames):
                return Response({"error": "One or more usernames do not exist"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": f"Invalid recipient type '{recipient_type}'"}, status=status.HTTP_400_BAD_REQUEST)

        # Create master notification record
        notification = Notification.objects.create(
            title=title,
            message=message,
            recipient_type=recipient_type,
            target_role=target_role,
            target_cohort=target_cohort_obj,
            target_batch=target_batch_obj,
            target_sub_batch=target_sub_batch_obj,
            is_broadcast=True,
        )

        # Deliver to recipients
        recipients_to_create = [
            NotificationRecipient(notification=notification, user=user)
            for user in users
        ]
        if recipients_to_create:
            NotificationRecipient.objects.bulk_create(recipients_to_create, ignore_conflicts=True)

        # Broadcast real-time toast to target connected trainee clients
        msg_payload = {
            "type": "trainee.notification",
            "kind": "broadcast",
            "notification_id": notification.id,
            "title": title,
            "message": message,
            "text": f"{title}: {message}",
            "created_at": timezone.now().isoformat(),
        }

        if recipient_type == "ALL":
            # Single dispatch to all trainees group
            send_channel_message(notifier.ALL_GROUP, msg_payload)
        elif recipient_type == "BATCH" and target_batches:
            for b in target_batches:
                send_channel_message(notifier.batch_group(b.full_code), msg_payload)
        elif recipient_type == "SUB_BATCH" and target_sub_batches:
            for sb in target_sub_batches:
                send_channel_message(notifier.batch_group(sb.full_code), msg_payload)
        else:
            # Deliver to target users directly via their unique user groups (for USERS, ROLE, COHORT)
            delivered_groups = set()
            for u in users:
                ug = notifier.user_group(u.username)
                if ug not in delivered_groups:
                    send_channel_message(ug, msg_payload)
                    delivered_groups.add(ug)

        return Response(
            {
                "success": True,
                "notification_id": notification.id,
                "recipient_count": users.count(),
            },
            status=status.HTTP_201_CREATED,
        )


class BroadcastHistoryView(APIView):
    permission_classes = [IsAuthenticated, CanManageBroadcasts]

    def get(self, request):
        notifications = Notification.objects.all().order_by("-created_at")
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class UserNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recipients = (
            NotificationRecipient.objects
            .filter(user=request.user)
            .select_related("notification")
            .order_by("-created_at")
        )
        data = [
            {
                "id": item.id,
                "notification_id": item.notification_id,
                "title": item.notification.title,
                "message": item.notification.message,
                "is_read": item.is_read,
                "created_at": item.created_at,
            }
            for item in recipients
        ]
        return Response(data)


class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        try:
            recipient = NotificationRecipient.objects.get(id=notification_id, user=request.user)
            recipient.is_read = True
            recipient.read_at = timezone.now()
            recipient.save()
            return Response({"success": True, "message": "Notification marked as read"}, status=status.HTTP_200_OK)
        except NotificationRecipient.DoesNotExist:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)
