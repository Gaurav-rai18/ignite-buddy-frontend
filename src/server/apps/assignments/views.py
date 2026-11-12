"""
Assignment Views

Provides endpoints for creating, retrieving, updating deadlines,
submitting, and evaluating coursework assignments in Ignite Buddy.
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Assignment, AssignmentRecipient
from .serializers import (
    AssignmentSerializer,
    AssignmentDeadlineUpdateSerializer,
    AssignmentSubmitSerializer,
    AssignmentEvaluateSerializer,
    AssignmentRecipientSerializer,
)
from server.apps.accounts.models import User, Cohort, Batch, SubBatch
from server.apps.accounts.permissions import CanManageAssignments
from server.channels_push import send_channel_message
from server.realtime import notifier


class AssignmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Assignment.objects.all().prefetch_related("recipients", "target_batches", "target_sub_batches").select_related("target_cohort", "created_by")

        # If trainee, show only assignments assigned to this student
        if user.role == "TRAINEE" and not (user.is_superuser or user.is_staff):
            qs = qs.filter(recipients__user=user).distinct()

        # Optional query filters
        subject = request.query_params.get("subject")
        if subject:
            qs = qs.filter(subject__iexact=subject)

        filter_by = request.query_params.get("filter_by")
        if filter_by == "mine":
            qs = qs.filter(created_by=user)
        elif filter_by == "others":
            qs = qs.exclude(created_by=user)

        serializer = AssignmentSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        # Only faculty / admins can create assignments
        perm = CanManageAssignments()
        if not perm.has_permission(request, self):
            return Response(
                {"error": "Access denied. Only instructors and administrators can create assignments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data
        topic = str(data.get("topic") or "").strip()
        subject = str(data.get("subject") or "").strip()
        platform_link = data.get("platform_link") or None
        start_date = data.get("start_date")
        deadline = data.get("deadline")
        message = str(data.get("message") or "").strip()
        recipient_type = str(data.get("recipient_type") or "ALL").upper()

        if not topic:
            return Response({"error": "Topic is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not subject:
            return Response({"error": "Subject is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not start_date:
            return Response({"error": "Start date is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not deadline:
            return Response({"error": "Deadline date is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not message:
            return Response({"error": "Assignment message / instructions are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Audience resolution
        target_role = data.get("target_role")
        target_usernames = data.get("target_usernames", [])
        cohort_id = data.get("cohort_id") or data.get("target_cohort")
        batch_id = data.get("batch_id") or data.get("target_batch")
        sub_batch_id = data.get("sub_batch_id") or data.get("target_sub_batch")

        batch_ids = data.get("batch_ids") or []
        if not batch_ids and batch_id:
            batch_ids = [batch_id]

        sub_batch_ids = data.get("sub_batch_ids") or []
        if not sub_batch_ids and sub_batch_id:
            sub_batch_ids = [sub_batch_id]

        target_cohort_obj = None
        target_batch_obj = None
        target_sub_batch_obj = None
        target_batches = []
        target_sub_batches = []
        audience_label = "All students"

        if recipient_type == "ALL":
            users = User.objects.filter(is_active=True, role="TRAINEE")
            audience_label = "All students"
        elif recipient_type == "ROLE":
            if not target_role:
                return Response({"error": "target_role is required for ROLE recipient type."}, status=status.HTTP_400_BAD_REQUEST)
            users = User.objects.filter(role=target_role, is_active=True)
            audience_label = f"Role: {target_role}"
        elif recipient_type == "COHORT":
            target_cohort_obj = Cohort.objects.filter(id=cohort_id).first()
            if not target_cohort_obj:
                return Response({"error": "Valid cohort_id is required."}, status=status.HTTP_400_BAD_REQUEST)
            users = User.objects.filter(sub_batch__batch__cohort=target_cohort_obj, is_active=True)
            audience_label = f"Cohort {target_cohort_obj.code}"
        elif recipient_type == "BATCH":
            if not batch_ids:
                return Response({"error": "At least one batch must be selected."}, status=status.HTTP_400_BAD_REQUEST)
            target_batches = list(Batch.objects.filter(id__in=batch_ids))
            if not target_batches:
                return Response({"error": "Selected batch(es) do not exist."}, status=status.HTTP_400_BAD_REQUEST)
            users = User.objects.filter(sub_batch__batch__in=target_batches, is_active=True)
            if len(target_batches) == 1:
                target_batch_obj = target_batches[0]
                audience_label = f"Batch {target_batch_obj.name}"
            else:
                audience_label = f"{len(target_batches)} batches"
        elif recipient_type == "SUB_BATCH":
            if not sub_batch_ids:
                return Response({"error": "At least one sub-batch must be selected."}, status=status.HTTP_400_BAD_REQUEST)
            target_sub_batches = list(SubBatch.objects.filter(id__in=sub_batch_ids))
            if not target_sub_batches:
                return Response({"error": "Selected sub-batch(es) do not exist."}, status=status.HTTP_400_BAD_REQUEST)
            users = User.objects.filter(sub_batch__in=target_sub_batches, is_active=True)
            if len(target_sub_batches) == 1:
                target_sub_batch_obj = target_sub_batches[0]
                audience_label = f"Sub-batch {target_sub_batch_obj.name}"
            else:
                audience_label = f"{len(target_sub_batches)} sub-batches"
        elif recipient_type == "USERS":
            if not target_usernames:
                return Response({"error": "Select at least one recipient user."}, status=status.HTTP_400_BAD_REQUEST)
            users = User.objects.filter(username__in=target_usernames)
            if users.count() != len(target_usernames):
                return Response({"error": "One or more target usernames do not exist."}, status=status.HTTP_400_BAD_REQUEST)
            audience_label = f"Selected users ({len(target_usernames)})"
        else:
            return Response({"error": f"Invalid recipient type '{recipient_type}'."}, status=status.HTTP_400_BAD_REQUEST)

        assignment = Assignment.objects.create(
            topic=topic,
            subject=subject,
            platform_link=platform_link,
            start_date=start_date,
            deadline=deadline,
            message=message,
            recipient_type=recipient_type,
            target_role=target_role,
            target_cohort=target_cohort_obj,
            target_batch=target_batch_obj,
            target_sub_batch=target_sub_batch_obj,
            audience=audience_label,
            created_by=request.user,
        )

        if target_batches:
            assignment.target_batches.set(target_batches)
        if target_sub_batches:
            assignment.target_sub_batches.set(target_sub_batches)

        # Create recipient tracking records
        recipients_to_create = [
            AssignmentRecipient(assignment=assignment, user=u)
            for u in users
        ]
        if recipients_to_create:
            AssignmentRecipient.objects.bulk_create(recipients_to_create, ignore_conflicts=True)

        # Dispatch real-time WebSocket toast to trainee desktop assistants
        msg_payload = {
            "type": "trainee.notification",
            "kind": "assignment",
            "assignment_id": assignment.id,
            "title": f"New Assignment: {topic}",
            "message": f"[{subject}] {topic} — Due {deadline}. {message[:120]}",
            "text": f"New Assignment: {topic} ({subject})",
            "created_at": timezone.now().isoformat(),
        }

        if recipient_type == "ALL":
            send_channel_message(notifier.ALL_GROUP, msg_payload)
        elif recipient_type == "BATCH" and target_batches:
            for b in target_batches:
                send_channel_message(notifier.batch_group(b.full_code), msg_payload)
        elif recipient_type == "SUB_BATCH" and target_sub_batches:
            for sb in target_sub_batches:
                send_channel_message(notifier.batch_group(sb.full_code), msg_payload)
        else:
            delivered = set()
            for u in users:
                ug = notifier.user_group(u.username)
                if ug not in delivered:
                    send_channel_message(ug, msg_payload)
                    delivered.add(ug)

        serializer = AssignmentSerializer(assignment, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AssignmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Assignment.objects.get(pk=pk)
        except Assignment.DoesNotExist:
            return None

    def get(self, request, pk):
        assignment = self.get_object(pk)
        if not assignment:
            return Response({"error": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AssignmentSerializer(assignment, context={"request": request})
        return Response(serializer.data)

    def patch(self, request, pk):
        # Update assignment (e.g. deadline update or details edit)
        perm = CanManageAssignments()
        if not perm.has_permission(request, self):
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        assignment = self.get_object(pk)
        if not assignment:
            return Response({"error": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

        # Support fast deadline update or full partial edit
        if "deadline" in request.data and len(request.data) == 1:
            serializer = AssignmentDeadlineUpdateSerializer(assignment, data=request.data, partial=True)
        else:
            serializer = AssignmentSerializer(assignment, data=request.data, partial=True, context={"request": request})

        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Send deadline change notification to trainees if deadline updated
        if "deadline" in request.data:
            msg_payload = {
                "type": "trainee.notification",
                "kind": "assignment",
                "assignment_id": assignment.id,
                "title": f"Deadline Updated: {assignment.topic}",
                "message": f"The deadline for {assignment.topic} has been updated to {assignment.deadline}.",
                "text": f"Deadline updated: {assignment.topic}",
                "created_at": timezone.now().isoformat(),
            }
            send_channel_message(notifier.ALL_GROUP, msg_payload)

        return Response(AssignmentSerializer(assignment, context={"request": request}).data)

    def delete(self, request, pk):
        perm = CanManageAssignments()
        if not perm.has_permission(request, self):
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        assignment = self.get_object(pk)
        if not assignment:
            return Response({"error": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

        assignment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssignmentSubmissionView(APIView):
    """
    Trainee submission endpoint and instructor submission listing.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Instructors view all submissions; Trainees view their own
        try:
            assignment = Assignment.objects.get(pk=pk)
        except Assignment.DoesNotExist:
            return Response({"error": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == "TRAINEE" and not (request.user.is_superuser or request.user.is_staff):
            recipients = assignment.recipients.filter(user=request.user)
        else:
            recipients = assignment.recipients.all().select_related("user", "evaluated_by")

        serializer = AssignmentRecipientSerializer(recipients, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        # Trainee submitting their coursework response
        try:
            assignment = Assignment.objects.get(pk=pk)
        except Assignment.DoesNotExist:
            return Response({"error": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

        recipient, _ = AssignmentRecipient.objects.get_or_create(
            assignment=assignment,
            user=request.user,
        )

        serializer = AssignmentSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipient.submission_link = serializer.validated_data.get("submission_link")
        recipient.submission_text = serializer.validated_data.get("submission_text")
        recipient.status = "SUBMITTED"
        recipient.submitted_at = timezone.now()
        recipient.save()

        return Response(AssignmentRecipientSerializer(recipient).data, status=status.HTTP_200_OK)


class AssignmentEvaluateView(APIView):
    """
    Instructor grading/evaluation endpoint.
    """
    permission_classes = [IsAuthenticated, CanManageAssignments]

    def post(self, request, pk, recipient_id=None):
        data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        if recipient_id and "recipient_id" not in data:
            data["recipient_id"] = recipient_id
        serializer = AssignmentEvaluateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        target_id = recipient_id or d.get("recipient_id")
        try:
            recipient = AssignmentRecipient.objects.get(id=target_id, assignment_id=pk)
        except AssignmentRecipient.DoesNotExist:
            return Response({"error": "Submission record not found."}, status=status.HTTP_404_NOT_FOUND)

        recipient.grade = d["grade"]
        recipient.feedback = d.get("feedback", "")
        recipient.status = "EVALUATED"
        recipient.evaluated_by = request.user
        recipient.evaluated_at = timezone.now()
        recipient.save()

        return Response(AssignmentRecipientSerializer(recipient).data, status=status.HTTP_200_OK)
