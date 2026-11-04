"""
core/serializers.py — Django REST Framework (DRF) ModelSerializers.

Converts Django model instances into JSON representations and validates
incoming request data for write/update operations.

Serializers defined:
  - UserSerializer: Custom User model with password hashing on create/update.
  - BroadcastSerializer: Broadcast announcement messages.
  - ScheduleLocationSerializer: 7 timetable location columns.
  - ScheduleSubBatchSerializer: Individual sub-batches (e.g. A1, B2).
  - ScheduleBatchSerializer: Batch groups with nested subbatches list.
  - ScheduleTimeSlotSerializer: Configurable time slots.
  - ScheduleWeekDaySerializer: Mon-Fri schedule days.
  - ScheduledLinkSerializer: Main schedule timetable entries (JSON & files).
  - SiteSettingSerializer: Key-value app configuration flags.
"""

from rest_framework import serializers
from .models import (
    Broadcast,
    ScheduledLink,
    SiteSetting,
    User,
    ScheduleLocation,
    ScheduleBatch,
    ScheduleSubBatch,
    ScheduleTimeSlot,
    ScheduleWeekDay,
)

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the custom User model.
    Handles secure password hashing via set_password() on create and update.
    """
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'batch', 'subbatch', 'status', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class BroadcastSerializer(serializers.ModelSerializer):
    """Serializer for campus broadcast announcements."""
    class Meta:
        model = Broadcast
        fields = ['id', 'title', 'message', 'audience', 'created_at']

class ScheduleLocationSerializer(serializers.ModelSerializer):
    """Serializer for lab/room locations displayed as timetable grid columns."""
    class Meta:
        model = ScheduleLocation
        fields = ['id', 'name', 'badge', 'color', 'order']

class ScheduleSubBatchSerializer(serializers.ModelSerializer):
    """Serializer for dynamic sub-batches (e.g., A1, A2)."""
    class Meta:
        model = ScheduleSubBatch
        fields = ['id', 'batch', 'name', 'code', 'order']

class ScheduleBatchSerializer(serializers.ModelSerializer):
    """
    Serializer for batch groups (Batch A, B, etc.).
    Includes nested read-only subbatches array.
    """
    subbatches = ScheduleSubBatchSerializer(many=True, read_only=True)

    class Meta:
        model = ScheduleBatch
        fields = ['id', 'name', 'code', 'order', 'subbatches']

class ScheduleTimeSlotSerializer(serializers.ModelSerializer):
    """Serializer for dynamic timetable time slots."""
    class Meta:
        model = ScheduleTimeSlot
        fields = ['id', 'start_time', 'end_time', 'label', 'order']

class ScheduleWeekDaySerializer(serializers.ModelSerializer):
    """Serializer for working days (Monday-Friday)."""
    class Meta:
        model = ScheduleWeekDay
        fields = ['id', 'name', 'code', 'order']

class ScheduledLinkSerializer(serializers.ModelSerializer):
    """
    Main serializer for timetable schedules.
    Serializes native grid timetables (with content_data JSON),
    Excel uploads (with excel_file, file_name, file_size),
    and legacy OneDrive links.
    """
    class Meta:
        model = ScheduledLink
        fields = [
            'id',
            'title',
            'onedrive_url',
            'content_data',
            'schedule_type',
            'excel_file',
            'file_name',
            'file_size',
            'publish_at',
            'created_at',
        ]

class SiteSettingSerializer(serializers.ModelSerializer):
    """Serializer for global key-value configuration flags (e.g. buddy_enabled)."""
    class Meta:
        model = SiteSetting
        fields = ['key', 'value', 'updated_at']
