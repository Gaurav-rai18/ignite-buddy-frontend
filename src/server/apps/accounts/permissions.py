from rest_framework.permissions import BasePermission

class IsUserManagementStaff(BasePermission):
    """
    Allows ADMIN, TA, HR, and MANAGER to access
    user-management endpoints.
    Superusers and staff always have access.
    """

    message = "You do not have permission to manage users."

    ALLOWED_ROLES = {"ADMIN", "TA", "HR", "MANAGER"}

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.is_staff
                or request.user.role in self.ALLOWED_ROLES
            )
        )
        
class IsAdmin(BasePermission):
    """
    Custom permission to allow access to users
    with the ADMIN role or superusers.
    """

    message = "Only admin users are allowed to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.role == "ADMIN"
            )
        )

class CanManageBroadcasts(BasePermission):
    """
    Allows admin/support roles to create broadcasts.
    Superusers and staff always have access.
    """

    message = "You do not have permission to manage broadcasts."

    ALLOWED_ROLES = {
        "ADMIN",
        "TA",
        "HR",
        "MANAGER",
    }

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.is_staff
                or request.user.role in self.ALLOWED_ROLES
            )
        )
