# from rest_framework import serializers
# from .models import Notification

# class NotificationSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = Notification
#         fields = "__all__"


"""
Notification Serializers

This file contains serializers used to convert
Notification model instances into JSON responses
and validate incoming request data.

Serializers:
    - NotificationSerializer

Purpose:
    Provides serialization support for Notification APIs,
    including broadcast history and notification retrieval.
"""

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Notification Model Serializer.

    Converts Notification model instances
    into JSON format for API responses.

    Used In:
        - Broadcast History API
        - Notification Retrieval APIs

    Example Response:

    {
        "id": 1,
        "title": "Training Update",
        "message": "New training schedule published",
        "recipient_type": "ROLE",
        "target_role": "TRAINEE",
        "is_broadcast": true,
        "created_at": "2026-11-06T10:30:00Z"
    }
    """

    class Meta:
        """
        Serializer configuration.

        Model:
            Notification

        Fields:
            Includes all fields from the
            Notification model.
        """

        model = Notification
        fields = "__all__"
