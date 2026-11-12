"""
Assignment Views

Provides endpoints for creating, retrieving, updating deadlines,
submitting, and evaluating coursework assignments in Ignite Buddy.
"""
import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import DateTimeField
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Assignment, AssignmentRecipient
from .notifications import (
    notify_new_assignment,
    notify_deadline_updated,
    notify_evaluated,
)
from .services import record_submission
from .serializers import (
    AssignmentSerializer,
    AssignmentDeadlineUpdateSerializer,
    AssignmentSubmitSerializer,
    AssignmentEvaluateSerializer,
    AssignmentRecipientSerializer,
)
from server.apps.accounts.models import User, Cohort, Batch, SubBatch
from server.apps.accounts.permissions import CanManageAssignments

log = logging.getLogger("assignments.views")


def _truthy(value, default=True):
    """Interpret a loosely-typed request flag (bool / 'true' / '1' / 'yes')."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in ("false", "0", "no", "off", "")


class AssignmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = Assignment.objects.all().prefetch_related("recipients", "target_batches", "target_sub_batches").select_related("target_cohort", "created_by")

        # If trainee, show only *published* assignments assigned to this student
        if user.role == "TRAINEE" and not (user.is_superuser or user.is_staff):
            qs = qs.filter(recipients__user=user, is_published=True).distinct()

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
        raw_deadline_at = data.get("deadline_at") or None
        try:
            deadline_at = DateTimeField().run_validation(raw_deadline_at) if raw_deadline_at else None
        except ValidationError as exc:
            return Response({"deadline_at": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        message = str(data.get("message") or "").strip()
        recipient_type = str(data.get("recipient_type") or "ALL").upper()
        # Drafts (is_published=False) are saved without notifying anyone; the
        # default preserves the previous create-and-publish behaviour.
        is_published = _truthy(data.get("is_published"), default=True)

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
            deadline_at=deadline_at,
            message=message,
            recipient_type=recipient_type,
            target_role=target_role,
            target_cohort=target_cohort_obj,
            target_batch=target_batch_obj,
            target_sub_batch=target_sub_batch_obj,
            audience=audience_label,
            is_published=is_published,
            published_at=timezone.now() if is_published else None,
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

        # Persist + push the structured "New Assignment Posted" notification to
        # every eligible trainee (reuses the shared notification infrastructure).
        if is_published:
            try:
                notify_new_assignment(assignment, users)
            except Exception:
                log.exception("Failed to send new-assignment notifications for assignment %s", assignment.id)

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

        was_published = assignment.is_published
        old_deadline = assignment.deadline
        old_deadline_at = assignment.deadline_at

        # Support fast deadline update or full partial edit
        if "deadline" in request.data and len(request.data) == 1:
            serializer = AssignmentDeadlineUpdateSerializer(assignment, data=request.data, partial=True)
        else:
            serializer = AssignmentSerializer(assignment, data=request.data, partial=True, context={"request": request})

        serializer.is_valid(raise_exception=True)
        serializer.save()

        now_published = assignment.is_published
        deadline_changed = assignment.deadline != old_deadline or assignment.deadline_at != old_deadline_at
        newly_published = now_published and not was_published

        # Record the first publication time for a previously saved draft.
        if newly_published:
            if not assignment.published_at:
                Assignment.objects.filter(pk=assignment.pk).update(published_at=timezone.now())
                assignment.published_at = timezone.now()

        # Retry missing announcement deliveries on edits to published assignments.
        # The notification service deduplicates by assignment and recipient.
        if now_published:
            try:
                notify_new_assignment(assignment)
            except Exception:
                log.exception("Failed to notify trainees about published assignment %s", assignment.id)

        # A moved deadline re-arms both reminders and tells trainees about the change.
        if deadline_changed and not newly_published:
            Assignment.objects.filter(pk=assignment.pk).update(
                reminder_24h_sent_at=None,
                reminder_1h_sent_at=None,
            )
            AssignmentRecipient.objects.filter(assignment=assignment).update(
                notified_24h_at=None,
                notified_1h_at=None,
            )
            try:
                notify_deadline_updated(assignment)
            except Exception:
                log.exception("Failed to notify trainees about deadline change for %s", assignment.id)

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

        serializer = AssignmentSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Shared code path with the trainee desktop WebSocket consumer.
        recipient = record_submission(
            assignment,
            request.user,
            submission_text=serializer.validated_data.get("submission_text"),
            submission_link=serializer.validated_data.get("submission_link"),
        )

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

        # Faculty can send the submission back for another attempt, which
        # re-arms the deadline reminders for that trainee.
        resubmission_required = _truthy(request.data.get("resubmission_required"), default=False)
        recipient.resubmission_required = resubmission_required
        recipient.save()

        if resubmission_required:
            AssignmentRecipient.objects.filter(pk=recipient.pk).update(
                notified_24h_at=None,
                notified_1h_at=None,
            )

        try:
            notify_evaluated(recipient)
        except Exception:
            log.exception("Failed to send evaluation notification for recipient %s", recipient.id)

        return Response(AssignmentRecipientSerializer(recipient).data, status=status.HTTP_200_OK)
