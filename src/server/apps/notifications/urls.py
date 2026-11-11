# from django.urls import path

# from .views import (
#     BroadcastCreateView,
#     BroadcastHistoryView,
#     UserNotificationView,
#     MarkNotificationReadView,
# )

# urlpatterns = [
#     path(
#         "broadcast/",
#         BroadcastCreateView.as_view()
#     ),

#     path(
#         "broadcast/history/",
#         BroadcastHistoryView.as_view()
#     ),

#     path(
#         "user-notifications/",
#         UserNotificationView.as_view()
#     ),

#     path(
#     "read/<int:notification_id>/",
#     MarkNotificationReadView.as_view()
#     ),
# ]


"""
Notification URL Configuration

This file contains all API routes related to
notification management and broadcast functionality.

Available APIs:

1. Create Broadcast Notification
   POST /api/notifications/broadcast/

2. Retrieve Broadcast History
   GET /api/notifications/broadcast/history/

3. Retrieve User Notifications
   GET /api/notifications/user-notifications/

4. Mark Notification as Read
   PATCH /api/notifications/read/<notification_id>/

Author:
    Ignite Buddy Development Team
"""

from django.urls import path

from .views import (
    BroadcastCreateView,
    BroadcastHistoryView,
    UserNotificationView,
    MarkNotificationReadView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Broadcast Notification API
    # ------------------------------------------------------------------
    # Purpose:
    #   Creates and sends notifications to:
    #       1. All users
    #       2. Users belonging to a specific role
    #       3. Selected users
    #
    # Method:
    #   POST
    #
    # Endpoint:
    #   /api/notifications/broadcast/
    #
    # Permissions:
    #   ADMIN
    #   TA
    #   HR
    #   MANAGER
    # ------------------------------------------------------------------
    path(
        "broadcast/",
        BroadcastCreateView.as_view(),
        name="create-broadcast"
    ),

    # ------------------------------------------------------------------
    # Broadcast History API
    # ------------------------------------------------------------------
    # Purpose:
    #   Retrieves all previously sent broadcast
    #   notifications in descending order.
    #
    # Method:
    #   GET
    #
    # Endpoint:
    #   /api/notifications/broadcast/history/
    #
    # Response:
    #   List of broadcast notifications.
    # ------------------------------------------------------------------
    path(
        "broadcast/history/",
        BroadcastHistoryView.as_view(),
        name="broadcast-history"
    ),

    # ------------------------------------------------------------------
    # User Notification API
    # ------------------------------------------------------------------
    # Purpose:
    #   Retrieves notifications assigned
    #   to a specific user.
    #
    # Method:
    #   GET
    #
    # Endpoint:
    #   /api/notifications/user-notifications/
    #
    # Query Parameter:
    #   user_id
    #
    # Example:
    #   /api/notifications/user-notifications/?user_id=5
    # ------------------------------------------------------------------
    path(
        "user-notifications/",
        UserNotificationView.as_view(),
        name="user-notifications"
    ),

    # ------------------------------------------------------------------
    # Mark Notification as Read API
    # ------------------------------------------------------------------
    # Purpose:
    #   Updates the notification status
    #   from unread to read.
    #
    # Method:
    #   PATCH
    #
    # Endpoint:
    #   /api/notifications/read/<notification_id>/
    #
    # Example:
    #   /api/notifications/read/10/
    # ------------------------------------------------------------------
    path(
        "read/<int:notification_id>/",
        MarkNotificationReadView.as_view(),
        name="mark-notification-read"
    ),
]
