"""Admin Panel ViewSets (Django REST Framework).

Replaces the previous function-based handlers in transport/admin_api.py while
keeping the same URL paths and behaviour (including live sync to connected
trainee PCs via notifier.sync_batch).
"""
from datetime import datetime

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from server.data.central import get_central
from server.realtime import notifier

from .auth import AdminTokenAuthentication
from .serializers import (
    AssignmentSerializer,
    TimetableSlotSerializer,
    TraineeBatchUpdateSerializer,
    TraineeSerializer,
    LoginSerializer,
    CreateTraineeSerializer,
)


def _due_ts(data: dict) -> float | None:
    if data.get("due_ts") is not None:
        return float(data["due_ts"])
    if data.get("due"):
        return datetime.fromisoformat(str(data["due"])).timestamp()
    return None


class AssignmentViewSet(viewsets.ViewSet):
    """CRUD for batch assignments published to trainee PCs."""

    authentication_classes = [AdminTokenAuthentication]
    permission_classes = []  # auth class already enforces the token

    def list(self, request):
        batch = request.query_params.get("batch")
        rows = get_central().assignments(batch)
        return Response({"assignments": rows})

    def create(self, request):
        ser = AssignmentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        batch = d.get("batch") or "default"
        new_id = get_central().upsert_assignment(
            batch, d["title"], d.get("description", ""), _due_ts(d)
        )
        notifier.sync_batch(batch)
        return Response({"id": new_id}, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        ser = AssignmentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        c = get_central()
        old = c.assignment_batch(pk)
        batch = d.get("batch") or old or "default"
        new_id = c.upsert_assignment(batch, d["title"], d.get("description", ""), _due_ts(d), pk)
        for b in {batch, old} - {None}:
            notifier.sync_batch(b)
        return Response({"id": new_id})

    def destroy(self, request, pk=None):
        batch = get_central().delete_assignment(pk)
        if batch:
            notifier.sync_batch(batch)
        return Response({"deleted": bool(batch)})


class TimetableViewSet(viewsets.ViewSet):
    """CRUD for weekly timetable slots."""

    authentication_classes = [AdminTokenAuthentication]
    permission_classes = []

    def list(self, request):
        batch = request.query_params.get("batch")
        rows = get_central().slots(batch)
        return Response({"timetable": rows})

    def create(self, request):
        ser = TimetableSlotSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        batch = d.get("batch") or "default"
        new_id = get_central().upsert_slot(
            batch, int(d["weekday"]), d["start"], d["end"], d["title"], d.get("location", "")
        )
        notifier.sync_batch(batch)
        loc = f" in {d.get('location')}" if d.get("location") else ""
        notifier.broadcast_batch(batch, f"Schedule update: {d['title']} at {d['start']}-{d['end']}{loc}.")
        return Response({"id": new_id}, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """Update an existing weekly timetable slot.

        Detects if the slot's batch assignment has changed, broadcasting sync notifications
        to both the previous and newly assigned batches so all affected trainee PCs stay in sync.
        """
        ser = TimetableSlotSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        c = get_central()
        old = c.slot_batch(pk) if hasattr(c, "slot_batch") else None
        batch = d.get("batch") or old or "default"
        new_id = c.upsert_slot(
            batch, int(d["weekday"]), d["start"], d["end"], d["title"], d.get("location", ""), pk
        )
        for b in {batch, old} - {None}:
            notifier.sync_batch(b)
        loc = f" in {d.get('location')}" if d.get("location") else ""
        notifier.broadcast_batch(batch, f"Schedule updated: {d['title']} at {d['start']}-{d['end']}{loc}.")
        return Response({"id": new_id})

    def destroy(self, request, pk=None):
        batch = get_central().delete_slot(pk)
        if batch:
            notifier.sync_batch(batch)
            notifier.broadcast_batch(batch, "A scheduled session has been updated in your timetable.")
        return Response({"deleted": bool(batch)})


class TraineeViewSet(viewsets.ViewSet):
    """List / create trainees and assign them to batches.

    Admin creates profiles with an optional password so the desktop app can
    obtain a JWT via POST /auth/login.
    """

    authentication_classes = [AdminTokenAuthentication]
    permission_classes = []

    def list(self, request):
        rows = get_central().trainees()
        return Response({"trainees": rows})

    def create(self, request):
        ser = CreateTraineeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        row = get_central().create_trainee(
            d["user_id"], d.get("name") or d["user_id"], d.get("batch") or "default", d.get("password") or ""
        )
        return Response(row, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        # batch and/or password reset
        data = request.data or {}
        if "batch" in data:
            ser = TraineeBatchUpdateSerializer(data=data)
            ser.is_valid(raise_exception=True)
            get_central().set_batch(pk, ser.validated_data["batch"])
        if data.get("password"):
            ok = get_central().set_password(pk, data["password"])
            if not ok:
                return Response({"error": "unknown trainee"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"ok": True})


class LoginView(APIView):
    """Public endpoint: exchange user_id + password for a JWT used by the desktop app."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from server.auth import issue_jwt
        from server import config as cfg
        from django.utils import timezone
        from django.contrib.auth import authenticate
        from server.apps.accounts.models import User as AccountUser

        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user_id_input = ser.validated_data["user_id"]
        password = ser.validated_data["password"]
        new_password = (ser.validated_data.get("new_password") or "").strip()

        # Authenticate against Django accounts.User strictly by unique Email or 7-digit Employee ID
        # Username login is removed because usernames can contain spaces and duplicate values.
        u_obj = (
            AccountUser.objects.filter(email__iexact=user_id_input).first()
            or AccountUser.objects.filter(employee_id__iexact=user_id_input).first()
        )
        user = u_obj if (u_obj and u_obj.check_password(password)) else None

        if user:
            # If user must change password on first login or after admin reset, require new_password
            if getattr(user, "must_change_password", False) and not new_password:
                print(f"[server] [auth] Trainee password change required: username='{user.username}'", flush=True)
                return Response({
                    "must_change_password": True,
                    "user_id": user.username,
                    "name": user.get_full_name() or user.username,
                    "message": "Password change required. Please set a new password to continue.",
                })

            if new_password:
                if len(new_password) < 8:
                    return Response(
                        {"error": "New password must be at least 8 characters long."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if new_password == password:
                    return Response(
                        {"error": "New password cannot be the same as your current/temporary password."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user.set_password(new_password)
                user.must_change_password = False
                print(f"[server] [auth] Trainee password updated successfully: username='{user.username}'", flush=True)

            user.last_active_at = timezone.now()
            user.save()
            batch_code = user.full_batch_name
            token = issue_jwt(user.username, user.get_full_name() or user.username, batch_code)
            # Ensure central.db is kept in sync with the trainee's batch assignment
            try:
                c = get_central()
                real_batch = user.sub_batch_code or user.full_batch_name or "default"
                c.create_trainee(user.username, user.get_full_name() or user.username, real_batch)
                c.set_batch(user.username, real_batch)
            except Exception as e:
                print(f"[server] [auth] Failed to sync trainee profile to central.db: {e}", flush=True)

            print(f"[server] [auth] Trainee signed in: username='{user.username}', employee_id='{user.employee_id}', batch='{batch_code}'", flush=True)
            return Response({
                "token": token,
                "user_id": user.username,
                "name": user.get_full_name() or user.username,
                "batch": batch_code,
                "cohort": user.cohort_code,
                "sub_batch": user.sub_batch_code,
                "expires_in_hours": cfg.JWT_TTL_HOURS,
                "must_change_password": False,
            })

        # Fallback to central.db if user only exists there
        row = None
        try:
            row = get_central().authenticate(user_id_input, password)
        except Exception:
            row = None
        if not row:
            print(f"[server] [auth] Failed trainee login attempt for: '{user_id_input}'", flush=True)
            return Response({"error": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        if not cfg.JWT_SECRET:
            return Response({"error": "JWT not configured on server (ASSISTANT_JWT_SECRET)"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        token = issue_jwt(row["user_id"], row["name"], row.get("batch") or "default")
        print(f"[server] [auth] Trainee signed in (legacy central): user_id='{row['user_id']}', batch='{row.get('batch') or 'default'}'", flush=True)
        return Response({
            "token": token,
            "user_id": row["user_id"],
            "name": row["name"],
            "batch": row.get("batch") or "default",
            "expires_in_hours": cfg.JWT_TTL_HOURS,
        })


class HealthView(APIView):
    """Unauthenticated liveness probe."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"ok": True})
