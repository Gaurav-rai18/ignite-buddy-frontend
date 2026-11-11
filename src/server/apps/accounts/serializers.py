"""
Accounts Serializers
Serializers for Authentication, User Management, and TCS Ignite Hierarchy.
"""
import re
from rest_framework import serializers
from .models import User, Cohort, Batch, Lab, SubBatch


class CohortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = ["id", "code", "name", "start_date", "end_date", "is_active", "created_at"]


class BatchSerializer(serializers.ModelSerializer):
    cohort_code = serializers.CharField(source="cohort.code", read_only=True)
    full_code = serializers.CharField(read_only=True)

    class Meta:
        model = Batch
        fields = ["id", "cohort", "cohort_code", "name", "description", "full_code", "created_at"]


class LabSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = ["id", "name", "capacity", "location"]


class SubBatchSerializer(serializers.ModelSerializer):
    batch_name = serializers.CharField(source="batch.name", read_only=True)
    cohort_code = serializers.CharField(source="batch.cohort.code", read_only=True)
    full_code = serializers.CharField(read_only=True)
    lab_name = serializers.CharField(source="lab.name", read_only=True)

    class Meta:
        model = SubBatch
        fields = ["id", "batch", "batch_name", "cohort_code", "name", "full_code", "lab", "lab_name", "created_at"]


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    employee_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    accops_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "role",
            "sub_batch",
            "employee_id",
            "accops_id",
        ]

    def validate_employee_id(self, value):
        if value is None or str(value).strip() == "":
            return None
        s = str(value).strip()
        if not re.match(r"^\d{7}$", s):
            raise serializers.ValidationError("Employee ID must be exactly a 7-digit integer (e.g. 1234567).")
        if User.objects.filter(employee_id=s).exists():
            raise serializers.ValidationError(f"Employee ID '{s}' is already assigned to another user.")
        return s

    def validate_email(self, value):
        s = str(value).strip().lower()
        if User.objects.filter(email__iexact=s).exists():
            raise serializers.ValidationError(f"Email '{s}' already exists.")
        return s

    def validate(self, data):
        role = data.get("role", "TRAINEE")
        emp_id = data.get("employee_id")
        if role == "TRAINEE" and not emp_id:
            raise serializers.ValidationError({"employee_id": "Employee ID (7-digit integer) is required for trainees."})
        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        if not validated_data.get("employee_id"):
            validated_data["employee_id"] = None
        if validated_data.get("accops_id") is None:
            validated_data["accops_id"] = ""
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    cohort_code = serializers.CharField(read_only=True)
    batch_code = serializers.CharField(read_only=True)
    sub_batch_code = serializers.CharField(read_only=True)
    full_batch_name = serializers.CharField(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "role",
            "sub_batch",
            "cohort_code",
            "batch_code",
            "sub_batch_code",
            "full_batch_name",
            "employee_id",
            "accops_id",
            "phone_number",
            "department",
            "designation",
            "profile_picture",
            "is_active",
            "must_change_password",
            "last_active_at",
            "date_joined",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.username or obj.email


class UserProfileSerializer(serializers.ModelSerializer):
    cohort_code = serializers.CharField(read_only=True)
    batch_code = serializers.CharField(read_only=True)
    sub_batch_code = serializers.CharField(read_only=True)
    full_batch_name = serializers.CharField(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "role",
            "employee_id",
            "phone_number",
            "department",
            "designation",
            "profile_picture",
            "accops_id",
            "sub_batch",
            "cohort_code",
            "batch_code",
            "sub_batch_code",
            "full_batch_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "role",
            "employee_id",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "cohort_code",
            "batch_code",
            "sub_batch_code",
            "full_batch_name",
        ]

    def get_full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.username or obj.email


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "phone_number",
            "department",
            "designation",
            "profile_picture",
        ]

    def validate_email(self, value):
        s = str(value).strip().lower()
        qs = User.objects.filter(email__iexact=s)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError(f"Email '{s}' already in use by another account.")
        return s

    def update(self, instance, validated_data):
        first_name = validated_data.get("first_name", instance.first_name)
        last_name = validated_data.get("last_name", instance.last_name)
        # If username is empty or matches previous composite, keep in sync with first and last name
        if "first_name" in validated_data or "last_name" in validated_data:
            full = f"{first_name} {last_name}".strip()
            if full and (not instance.username or instance.username == f"{instance.first_name} {instance.last_name}".strip()):
                validated_data.setdefault("username", full)
        return super().update(instance, validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    employee_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    accops_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "sub_batch",
            "employee_id",
            "accops_id",
            "phone_number",
            "department",
            "designation",
            "profile_picture",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate_employee_id(self, value):
        if value is None or str(value).strip() == "":
            return None
        s = str(value).strip()
        if not re.match(r"^\d{7}$", s):
            raise serializers.ValidationError("Employee ID must be exactly a 7-digit integer (e.g. 1234567).")
        qs = User.objects.filter(employee_id=s)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError(f"Employee ID '{s}' is already assigned to another user.")
        return s

    def validate_email(self, value):
        s = str(value).strip().lower()
        qs = User.objects.filter(email__iexact=s)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError(f"Email '{s}' already exists.")
        return s

    def update(self, instance, validated_data):
        if "employee_id" in validated_data and not validated_data["employee_id"]:
            validated_data["employee_id"] = None
        if "accops_id" in validated_data and validated_data["accops_id"] is None:
            validated_data["accops_id"] = ""
        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, min_length=8)
