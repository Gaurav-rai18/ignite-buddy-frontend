"""
Accounts Views

This module contains all account-related APIs used
for authentication, authorization, user management,
password management, and bulk user operations.

Modules Covered:

Authentication:
    - Login
    - Logout

Password Management:
    - Change Password
    - Reset Password

User Management:
    - Create User
    - Retrieve User
    - Update User
    - Delete User

Bulk Operations:
    - Bulk User Upload

Security:
    - JWT Authentication
    - Role-Based Access Control (RBAC)

Roles:
    - ADMIN
    - TA
    - HR
    - MANAGER
    - TRAINEE

Author:
    Ignite Buddy Development Team
"""
import json
import csv
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Cohort, Batch, Lab, SubBatch
from .permissions import IsAdmin, IsUserManagementStaff
from .serializers import (
    LoginSerializer,
    UserCreateSerializer,
    UserListSerializer,
    UserUpdateSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    CohortSerializer,
    BatchSerializer,
    LabSerializer,
    SubBatchSerializer,
)

from .services import (
    create_user,
    change_password,
    reset_password,
)
from .services import bulk_create_users
class LoginView(APIView):
    """
    User Login API.

    Endpoint:
        POST /api/accounts/login/

    Purpose:
        Authenticates a user using
        email and password.

    Authentication:
        Public Endpoint

    Request Example:

        {
            "email": "user@example.com",
            "password": "Password@123"
        }

    Success Response:

        {
            "access": "jwt_access_token",
            "refresh": "jwt_refresh_token",
            "email": "user@example.com",
            "role": "TRAINEE"
        }

    Error Response:

        {
            "error": "Invalid credentials"
        }
    """
    permission_classes = []

    def post(self, request):
        """
        Validates user credentials and
        returns JWT access and refresh tokens.
        """

        serializer = LoginSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        login_id = serializer.validated_data["email"].strip()
        password = serializer.validated_data["password"]

        user = authenticate(
            request,
            username=login_id,
            password=password
        )

        if not user:
            user_obj = (
                User.objects.filter(email__iexact=login_id).first()
                or User.objects.filter(employee_id__iexact=login_id).first()
            )
            if user_obj and user_obj.check_password(password):
                user = user_obj

        if not user:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"error": "This account is inactive."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Ensure superuser/staff always has ADMIN role assigned
        if (user.is_superuser or user.is_staff) and user.role == "TRAINEE":
            user.role = "ADMIN"
            user.save()

        # The admin panel is accessible by all except trainees: ADMIN, MANAGER, TA, HR
        ALLOWED_ADMIN_ROLES = {"ADMIN", "MANAGER", "TA", "HR"}
        if user.role == "TRAINEE" or user.role not in ALLOWED_ADMIN_ROLES:
            return Response(
                {"error": "Access denied. Trainees are not authorized to access the Admin Console."},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)
        user_profile = UserProfileSerializer(user).data

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                **user_profile,
            },
            status=status.HTTP_200_OK
        )
class LogoutView(APIView):

    """
    User Logout API.

    Endpoint:
        POST /api/accounts/logout/

    Purpose:
        Blacklists the refresh token
        and logs out the user.

    Authentication:
        Required

    Headers:

        Authorization: Bearer <token>
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Invalidates refresh token and
        logs out the current user.
        """

        refresh_token = request.data.get("refresh")

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Logged out successfully"},
                status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                {"error": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )


class ChangePasswordView(APIView):
    """
    Change Password API.

    Endpoint:
        POST /api/accounts/change-password/

    Purpose:
        Allows authenticated users
        to change their own password.

    Authentication:
        Required

    Request Example:

        {
            "old_password": "OldPass123",
            "new_password": "NewPass123"
        }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Verifies old password and
        updates user's password.
        """

        serializer = ChangePasswordSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        user = request.user

        if not user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )

        change_password(user, new_password)

        return Response(
            {"message": "Password changed successfully"},
            status=status.HTTP_200_OK
        )


class UserListCreateView(APIView):
    """
    User Management API.

    Endpoint:
        GET  /api/accounts/users/
        POST /api/accounts/users/

    Permissions:
        ADMIN
        TA
        HR
        MANAGER

    Purpose:
        - Retrieve all users
        - Create new users
    """
    permission_classes = [
        IsAuthenticated,
        IsUserManagementStaff,
    ]

    def get(self, request):
        """
        Retrieves all users available
        in the system.
        """
        users = User.objects.all()

        serializer = UserListSerializer(
            users,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        """
        Creates a new user account.
        """
        serializer = UserCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        user = create_user(
            serializer.validated_data
        )

        return Response(
            UserListSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )

class UserDetailView(APIView):
    """
    User Detail API.

    Endpoint:
        GET    /api/accounts/users/<id>/
        PATCH  /api/accounts/users/<id>/
        DELETE /api/accounts/users/<id>/

    Permissions:

        GET:
            ADMIN
            TA
            HR
            MANAGER

        PATCH:
            ADMIN only

        DELETE:
            ADMIN only
    """

    def get_permissions(self):
        """
        Dynamically assigns permissions
        based on HTTP request method.
        """
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            permission_classes = [
                IsAuthenticated,
                IsAdmin,
            ]
        else:
            permission_classes = [
                IsAuthenticated,
                IsUserManagementStaff,
            ]

        return [
            permission()
            for permission in permission_classes
        ]

        return [
            permission()
            for permission in permission_classes
        ]

    def get(self, request, id):
        """
        Retrieves information for
        a single user.
        """ 
        try:
            user = User.objects.get(id=id)

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserListSerializer(user)

        return Response(serializer.data)

    def patch(self, request, id):
        """
        Updates user profile information.
        """
        try:
            user = User.objects.get(id=id)

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        if request.data.get("password"):
            updated_user.set_password(str(request.data["password"]))
            if updated_user.role == "TRAINEE" or not updated_user.is_staff:
                updated_user.must_change_password = True
            updated_user.save()

        # Keep central.db trainee batch in sync with Django accounts
        try:
            from server.data.central import get_central
            from server.realtime import notifier
            real_b = updated_user.sub_batch_code or updated_user.full_batch_name or "default"
            c = get_central()
            c.set_batch(updated_user.username, real_b)
            notifier.sync_batch(real_b)
            if updated_user.sub_batch_code:
                notifier.sync_batch(updated_user.sub_batch_code)
        except Exception:
            pass

        return Response(UserListSerializer(updated_user).data)
    def delete(self, request, id):
        """
        Deletes a user account.

        Restriction:
        Users cannot delete
        their own account.
        """ 
        try:
            user = User.objects.get(id=id)

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.id == request.user.id:
            return Response(
                {"error": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.delete()

        return Response(
            {"message": "User deleted successfully"},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    """
    Admin Password Reset API.

    Endpoint:
        POST /api/accounts/users/<id>/reset-password/

    Permissions:
        ADMIN only

    Purpose:
        Allows administrators
        to reset another user's password.
    """
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def post(self, request, id):
        """
        Resets password for
        the selected user.
        """
        try:
            user = User.objects.get(id=id)

        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ResetPasswordSerializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data[
            "new_password"
        ]

        reset_password(
            user,
            new_password,
        )

        return Response(
            {"message": "Password reset successfully"},
            status=status.HTTP_200_OK,
        )
class BulkUploadUsersView(APIView):
    """
    Bulk User Upload API.

    Endpoint:
        POST /api/accounts/users/bulk-upload/

    Permissions:
        ADMIN
        TA
        HR
        MANAGER

    Purpose:
        Upload users in bulk
        through Excel files.

    Supported File Type:
        .xlsx

    Expected Columns:
        - username
        - email
        - role

    Response Example:

        {
            "created_count": 100,
            "failed_count": 3,
            "errors": []
        }
    """
    permission_classes = [
        IsAuthenticated,
        IsUserManagementStaff,
    ]

    def post(self, request):
        """
        Processes uploaded Excel file
        and creates users in bulk.
        """

        file = request.FILES.get(
            "file"
        )

        if not file:

            return Response(
                {
                    "message":
                    "No file uploaded"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        result = bulk_create_users(
            file
        )

        return Response(
            result,
            status=status.HTTP_200_OK
        )


class CohortListView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        cohorts = Cohort.objects.all().order_by("-code")
        return Response(CohortSerializer(cohorts, many=True).data)

    def post(self, request):
        ser = CohortSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        c = ser.save()
        return Response(CohortSerializer(c).data, status=status.HTTP_201_CREATED)


class BatchListView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        cohort_id = request.query_params.get("cohort")
        batches = Batch.objects.all()
        if cohort_id:
            batches = batches.filter(cohort_id=cohort_id)
        return Response(BatchSerializer(batches, many=True).data)

    def post(self, request):
        ser = BatchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        b = ser.save()
        return Response(BatchSerializer(b).data, status=status.HTTP_201_CREATED)


class SubBatchListView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        batch_id = request.query_params.get("batch")
        sub_batches = SubBatch.objects.all()
        if batch_id:
            sub_batches = sub_batches.filter(batch_id=batch_id)
        return Response(SubBatchSerializer(sub_batches, many=True).data)

    def post(self, request):
        ser = SubBatchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        sb = ser.save()
        return Response(SubBatchSerializer(sb).data, status=status.HTTP_201_CREATED)


class LabListView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        labs = Lab.objects.all().order_by("name")
        return Response(LabSerializer(labs, many=True).data)

    def post(self, request):
        ser = LabSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        lab = ser.save()
        return Response(LabSerializer(lab).data, status=status.HTTP_201_CREATED)


class CohortDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        try:
            cohort = Cohort.objects.get(pk=pk)
        except Cohort.DoesNotExist:
            return Response({"error": "Cohort not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(CohortSerializer(cohort).data)

    def patch(self, request, pk):
        try:
            cohort = Cohort.objects.get(pk=pk)
        except Cohort.DoesNotExist:
            return Response({"error": "Cohort not found"}, status=status.HTTP_404_NOT_FOUND)
        ser = CohortSerializer(cohort, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        cohort = ser.save()
        return Response(CohortSerializer(cohort).data)

    def delete(self, request, pk):
        try:
            cohort = Cohort.objects.get(pk=pk)
        except Cohort.DoesNotExist:
            return Response({"error": "Cohort not found"}, status=status.HTTP_404_NOT_FOUND)
        cohort.delete()
        return Response({"message": "Cohort deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class BatchDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        try:
            batch = Batch.objects.get(pk=pk)
        except Batch.DoesNotExist:
            return Response({"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(BatchSerializer(batch).data)

    def patch(self, request, pk):
        try:
            batch = Batch.objects.get(pk=pk)
        except Batch.DoesNotExist:
            return Response({"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND)
        ser = BatchSerializer(batch, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        batch = ser.save()
        return Response(BatchSerializer(batch).data)

    def delete(self, request, pk):
        try:
            batch = Batch.objects.get(pk=pk)
        except Batch.DoesNotExist:
            return Response({"error": "Batch not found"}, status=status.HTTP_404_NOT_FOUND)
        batch.delete()
        return Response({"message": "Batch deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class SubBatchDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        try:
            sub_batch = SubBatch.objects.get(pk=pk)
        except SubBatch.DoesNotExist:
            return Response({"error": "Sub-batch not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(SubBatchSerializer(sub_batch).data)

    def patch(self, request, pk):
        try:
            sub_batch = SubBatch.objects.get(pk=pk)
        except SubBatch.DoesNotExist:
            return Response({"error": "Sub-batch not found"}, status=status.HTTP_404_NOT_FOUND)
        ser = SubBatchSerializer(sub_batch, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        sub_batch = ser.save()
        return Response(SubBatchSerializer(sub_batch).data)

    def delete(self, request, pk):
        try:
            sub_batch = SubBatch.objects.get(pk=pk)
        except SubBatch.DoesNotExist:
            return Response({"error": "Sub-batch not found"}, status=status.HTTP_404_NOT_FOUND)
        sub_batch.delete()
        return Response({"message": "Sub-batch deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class LabDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        try:
            lab = Lab.objects.get(pk=pk)
        except Lab.DoesNotExist:
            return Response({"error": "Lab not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(LabSerializer(lab).data)

    def patch(self, request, pk):
        try:
            lab = Lab.objects.get(pk=pk)
        except Lab.DoesNotExist:
            return Response({"error": "Lab not found"}, status=status.HTTP_404_NOT_FOUND)
        ser = LabSerializer(lab, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        lab = ser.save()
        return Response(LabSerializer(lab).data)

    def delete(self, request, pk):
        try:
            lab = Lab.objects.get(pk=pk)
        except Lab.DoesNotExist:
            return Response({"error": "Lab not found"}, status=status.HTTP_404_NOT_FOUND)
        lab.delete()
        return Response({"message": "Lab deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class UserProfileView(APIView):
    """
    Profile API for currently authenticated user.
    GET   /api/accounts/me/
    PATCH /api/accounts/me/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        return Response(UserProfileSerializer(updated_user).data)


DEFAULT_ROLE_PERMISSIONS = {
    "ADMIN": {
        "label": "Campus Administrator & Workspace Owner",
        "description": "Full administrative ownership and configuration authority across all modules.",
        "is_immutable": True,
        "permissions": {
            "dashboard": True,
            "broadcast": True,
            "schedule": True,
            "buddy": True,
            "users": True,
            "documents": True,
            "assignments": True,
            "hierarchy": True,
            "roles_permissions": True,
            "system_preferences": True,
        },
    },
    "TA": {
        "label": "Faculty & Teaching Assistants",
        "description": "Instructional team managing announcements, course timetables, and learning material.",
        "is_immutable": False,
        "permissions": {
            "dashboard": True,
            "broadcast": True,
            "schedule": True,
            "buddy": False,
            "users": False,
            "documents": True,
            "assignments": True,
            "hierarchy": False,
            "roles_permissions": False,
            "system_preferences": False,
        },
    },
    "MANAGER": {
        "label": "Campus Manager & HR",
        "description": "Operations and HR leads managing cohort cohorts, batches, and user directories.",
        "is_immutable": False,
        "permissions": {
            "dashboard": True,
            "broadcast": True,
            "schedule": True,
            "buddy": False,
            "users": True,
            "documents": False,
            "assignments": True,
            "hierarchy": True,
            "roles_permissions": False,
            "system_preferences": False,
        },
    },
    "HR": {
        "label": "Human Resources Coordinator",
        "description": "Campus HR operations overseeing trainee cohorts, rosters, and administrative records.",
        "is_immutable": False,
        "permissions": {
            "dashboard": True,
            "broadcast": True,
            "schedule": False,
            "buddy": False,
            "users": True,
            "documents": False,
            "assignments": True,
            "hierarchy": True,
            "roles_permissions": False,
            "system_preferences": False,
        },
    },
    "TRAINEE": {
        "label": "Student Trainee",
        "description": "Enrolled TCS Ignite learners accessing real-time AI mentoring and learning assets.",
        "is_immutable": True,
        "permissions": {
            "dashboard": False,
            "broadcast": False,
            "schedule": False,
            "buddy": False,
            "users": False,
            "documents": False,
            "assignments": False,
            "hierarchy": False,
            "roles_permissions": False,
            "system_preferences": False,
        },
    },
}


class RolesPermissionsView(APIView):
    """
    Role-Based Access Control configuration.
    GET  /api/accounts/roles-permissions/
    POST /api/accounts/roles-permissions/
    """
    permission_classes = [IsAuthenticated]

    def _get_stored_matrix(self):
        from server.apps.buddy_controller.models import SystemSetting
        raw = SystemSetting.get_str("rbac_role_permissions", "")
        if raw:
            try:
                stored = json.loads(raw)
                matrix = json.loads(json.dumps(DEFAULT_ROLE_PERMISSIONS))
                for role_key, data in stored.items():
                    if role_key in matrix:
                        matrix[role_key]["permissions"].update(data.get("permissions", {}))
                return matrix
            except Exception:
                pass
        return DEFAULT_ROLE_PERMISSIONS

    def get(self, request):
        matrix = self._get_stored_matrix()
        user_counts = {}
        for role_key in DEFAULT_ROLE_PERMISSIONS:
            user_counts[role_key] = User.objects.filter(role=role_key, is_active=True).count()

        is_admin = bool(request.user.is_superuser or request.user.role == "ADMIN")
        return Response({
            "roles": matrix,
            "user_counts": user_counts,
            "current_user_role": request.user.role,
            "can_manage": is_admin,
        })

    def post(self, request):
        if not (request.user.is_superuser or request.user.role == "ADMIN"):
            return Response(
                {"error": "Only Workspace Owners and Administrators can modify role permissions."},
                status=status.HTTP_403_FORBIDDEN
            )

        from server.apps.buddy_controller.models import SystemSetting
        incoming_roles = request.data.get("roles", {})
        matrix = self._get_stored_matrix()

        for role_key, role_data in incoming_roles.items():
            if role_key in matrix:
                # Do not permit downgrading the Workspace Owner / ADMIN role
                if role_key == "ADMIN":
                    continue
                incoming_perms = role_data.get("permissions", {})
                for perm_key, val in incoming_perms.items():
                    if perm_key in matrix[role_key]["permissions"]:
                        matrix[role_key]["permissions"][perm_key] = bool(val)

        SystemSetting.set_str(
            "rbac_role_permissions",
            json.dumps(matrix),
            description="RBAC Module Access Matrix",
            user=request.user
        )

        return Response({
            "success": True,
            "roles": matrix,
            "message": "Role permissions updated and saved to persistent database.",
        })


DEFAULT_SYSTEM_PREFERENCES = {
    # General Settings
    "workspace_name": "TCS Ignite Workspace",
    "timezone": "Asia/Kolkata",
    "date_format": "DD/MM/YYYY",
    "time_format": "12-hour",
    # Appearance
    "theme": "light",
    "sidebar_default_expanded": True,
    # Notification Preferences
    "notify_announcements": True,
    "notify_schedules": True,
    "notify_system_alerts": True,
    # Security Settings
    "session_timeout_minutes": 15,
    "password_min_length": 8,
    "require_special_char": True,
    # Data Management
    "data_retention_days": 365,
    "auto_archive_broadcasts": True,
}


class SystemPreferencesView(APIView):
    """
    Persistent System Preferences API.
    GET  /api/settings/preferences/
    POST /api/settings/preferences/
    """
    permission_classes = [IsAuthenticated]

    def _get_stored_preferences(self):
        from server.apps.buddy_controller.models import SystemSetting
        raw = SystemSetting.get_str("system_preferences", "")
        prefs = dict(DEFAULT_SYSTEM_PREFERENCES)
        if raw:
            try:
                stored = json.loads(raw)
                prefs.update(stored)
            except Exception:
                pass
        return prefs

    def get(self, request):
        prefs = self._get_stored_preferences()
        return Response(prefs)

    def post(self, request):
        from server.apps.buddy_controller.models import SystemSetting
        prefs = self._get_stored_preferences()
        incoming = request.data or {}

        # Whitelist allowed preference keys
        for key, val in incoming.items():
            if key in prefs:
                prefs[key] = val

        SystemSetting.set_str(
            "system_preferences",
            json.dumps(prefs),
            description="Global System Preferences",
            user=request.user
        )

        return Response({
            "success": True,
            "preferences": prefs,
            "message": "System preferences successfully updated.",
        })


class DataExportView(APIView):
    """
    Export System Data API.
    GET /api/settings/export/?type=users|audit
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        export_type = request.query_params.get("type", "users").lower()

        if export_type == "users":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="ignite_users_export.csv"'
            writer = csv.writer(response)
            writer.writerow([
                "ID",
                "Employee ID",
                "Full Name",
                "Username",
                "Email",
                "Role",
                "Department",
                "Designation",
                "Batch / Hierarchy",
                "Active Status",
                "Date Joined",
            ])

            for u in User.objects.all().order_by("id"):
                name = f"{u.first_name} {u.last_name}".strip() or u.username
                writer.writerow([
                    u.id,
                    u.employee_id or "",
                    name,
                    u.username,
                    u.email,
                    u.role,
                    u.department or "",
                    u.designation or "",
                    u.full_batch_name or "Unassigned",
                    "ACTIVE" if u.is_active else "INACTIVE",
                    u.date_joined.strftime("%Y-%m-%d %H:%M") if u.date_joined else "",
                ])
            return response

        # Default audit summary export
        from server.apps.buddy_controller.models import SystemSetting
        summary = {
            "total_users": User.objects.count(),
            "active_users": User.objects.filter(is_active=True).count(),
            "admin_count": User.objects.filter(role="ADMIN").count(),
            "trainee_count": User.objects.filter(role="TRAINEE").count(),
            "cohort_count": Cohort.objects.count(),
            "batch_count": Batch.objects.count(),
            "sub_batch_count": SubBatch.objects.count(),
            "preferences": json.loads(SystemSetting.get_str("system_preferences", "{}") or "{}"),
            "exported_at": timezone.now().isoformat(),
        }
        return Response(summary)


