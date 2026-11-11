"""Serializers for Admin Panel resources."""
from rest_framework import serializers


class AssignmentSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    batch = serializers.CharField(required=False, allow_blank=True, default="default")
    title = serializers.CharField(max_length=500)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    due = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    due_ts = serializers.FloatField(required=False, allow_null=True, default=None)
    deleted = serializers.BooleanField(read_only=True, required=False)
    rev = serializers.IntegerField(read_only=True, required=False)

    def validate(self, data):
        # Prefer explicit due_ts; otherwise parse ISO due string upstream.
        return data


class TimetableSlotSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    batch = serializers.CharField(required=False, allow_blank=True, default="default")
    weekday = serializers.IntegerField(min_value=0, max_value=6)
    start = serializers.RegexField(regex=r"^\d{1,2}:\d{2}$")
    end = serializers.RegexField(regex=r"^\d{1,2}:\d{2}$")
    title = serializers.CharField(max_length=500)
    location = serializers.CharField(required=False, allow_blank=True, default="")
    deleted = serializers.BooleanField(read_only=True, required=False)
    rev = serializers.IntegerField(read_only=True, required=False)


class TraineeSerializer(serializers.Serializer):
    user_id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True, required=False)
    batch = serializers.CharField()


class TraineeBatchUpdateSerializer(serializers.Serializer):
    batch = serializers.CharField(max_length=200)


class LoginSerializer(serializers.Serializer):
    """Desktop app login: user_id + password → JWT, with optional first-login/reset new_password."""
    user_id = serializers.CharField(max_length=200)
    password = serializers.CharField(max_length=200, write_only=True)
    new_password = serializers.CharField(max_length=200, required=False, allow_blank=True, default="", write_only=True)


class CreateTraineeSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=200)
    name = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    batch = serializers.CharField(max_length=200, required=False, allow_blank=True, default="default")
    password = serializers.CharField(max_length=200, required=False, allow_blank=True, default="", write_only=True)
