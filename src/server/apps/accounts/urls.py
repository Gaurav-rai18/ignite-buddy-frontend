"""
Accounts URL Configuration

This module defines all API routes related to:

    - Authentication
    - User Management
    - Password Management
    - Bulk User Upload

Available APIs:

Authentication:
    POST /api/accounts/login/
    POST /api/accounts/logout/

Password Management:
    POST /api/accounts/change-password/
    POST /api/accounts/users/<id>/reset-password/

User Management:
    GET    /api/accounts/users/
    POST   /api/accounts/users/
    GET    /api/accounts/users/<id>/
    PATCH  /api/accounts/users/<id>/
    DELETE /api/accounts/users/<id>/

Bulk Upload:
    POST /api/accounts/users/bulk-upload/

Security:
    - JWT Authentication
    - Role-Based Authorization

Author:
    Ignite Buddy Development Team
"""

from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    ChangePasswordView,
    UserListCreateView,
    UserDetailView,
    ResetPasswordView,
    BulkUploadUsersView,
    CohortListView,
    CohortDetailView,
    BatchListView,
    BatchDetailView,
    SubBatchListView,
    SubBatchDetailView,
    LabListView,
    LabDetailView,
    UserProfileView,
    RolesPermissionsView,
)

urlpatterns = [

    # -----------------------------------------------------
    # Current User Profile API
    # -----------------------------------------------------
    path(
        "me/",
        UserProfileView.as_view(),
        name="user-profile"
    ),

    # -----------------------------------------------------
    # Roles & Permissions API
    # -----------------------------------------------------
    path(
        "roles-permissions/",
        RolesPermissionsView.as_view(),
        name="roles-permissions"
    ),

    # -----------------------------------------------------
    # Login API
    # -----------------------------------------------------
    # Purpose:
    #   Authenticates a user and returns
    #   JWT access and refresh tokens.
    #
    # Method:
    #   POST
    #
    # Endpoint:
    #   /api/accounts/login/
    # -----------------------------------------------------
    path(
        "login/",
        LoginView.as_view(),
        name="login"
    ),

    # -----------------------------------------------------
    # Logout API
    # -----------------------------------------------------
    # Purpose:
    #   Invalidates refresh token and
    #   logs out an authenticated user.
    #
    # Method:
    #   POST
    #
    # Endpoint:
    #   /api/accounts/logout/
    # -----------------------------------------------------
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout"
    ),

    # -----------------------------------------------------
    # Change Password API
    # -----------------------------------------------------
    # Purpose:
    #   Allows authenticated users
    #   to update their own password.
    #
    # Method:
    #   POST
    #
    # Endpoint:
    #   /api/accounts/change-password/
    # -----------------------------------------------------
    path(
        "change-password/",
        ChangePasswordView.as_view(),
        name="change-password"
    ),

    # -----------------------------------------------------
    # User List & Create API
    # -----------------------------------------------------
    # Purpose:
    #   GET  - Retrieve all users
    #   POST - Create a new user
    #
    # Methods:
    #   GET
    #   POST
    #
    # Endpoint:
    #   /api/accounts/users/
    #
    # Access:
    #   ADMIN
    #   TA
    #   HR
    #   MANAGER
    # -----------------------------------------------------
    path(
        "users/",
        UserListCreateView.as_view(),
        name="users"
    ),

    # -----------------------------------------------------
    # User Detail API
    # -----------------------------------------------------
    # Purpose:
    #   Retrieve, update, or delete
    #   a specific user.
    #
    # Methods:
    #   GET
    #   PATCH
    #   DELETE
    #
    # Endpoint:
    #   /api/accounts/users/<id>/
    #
    # Example:
    #   /api/accounts/users/5/
    # -----------------------------------------------------
    path(
        "users/<int:id>/",
        UserDetailView.as_view(),
        name="user-detail",
    ),

    # -----------------------------------------------------
    # Reset Password API
    # -----------------------------------------------------
    # Purpose:
    #   Allows administrator to reset
    #   another user's password.
    #
    # Method:
    #   POST
    #
    # Endpoint:
    #   /api/accounts/users/<id>/reset-password/
    #
    # Access:
    #   ADMIN only
    # -----------------------------------------------------
    path(
        "users/<int:id>/reset-password/",
        ResetPasswordView.as_view(),
        name="reset-password",
    ),

    # -----------------------------------------------------
    # Bulk Upload Users API
    # -----------------------------------------------------
    # Purpose:
    #   Upload and create multiple users
    #   from an Excel (.xlsx) file.
    #
    # Method:
    #   POST
    #
    # Endpoint:
    #   /api/accounts/users/bulk-upload/
    #
    # Access:
    #   ADMIN
    #   TA
    #   HR
    #   MANAGER
    #
    # File Format:
    #   username | email | role
    # -----------------------------------------------------
    path(
        "users/bulk-upload/",
        BulkUploadUsersView.as_view(),
        name="bulk-upload-users"
    ),
    # -----------------------------------------------------
    # TCS Ignite Hierarchy APIs
    # -----------------------------------------------------
    path("cohorts/", CohortListView.as_view(), name="cohort-list"),
    path("cohorts/<int:pk>/", CohortDetailView.as_view(), name="cohort-detail"),
    path("batches/", BatchListView.as_view(), name="batch-list"),
    path("batches/<int:pk>/", BatchDetailView.as_view(), name="batch-detail"),
    path("sub-batches/", SubBatchListView.as_view(), name="sub-batch-list"),
    path("sub-batches/<int:pk>/", SubBatchDetailView.as_view(), name="sub-batch-detail"),
    path("labs/", LabListView.as_view(), name="lab-list"),
    path("labs/<int:pk>/", LabDetailView.as_view(), name="lab-detail"),
]
