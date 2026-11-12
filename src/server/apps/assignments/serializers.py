from rest_framework import serializers
from .models import Assignment, AssignmentRecipient
from server.apps.accounts.models import User, Cohort, Batch, SubBatch


class AssignmentRecipientSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.SerializerMethodField()
    employee_id = serializers.CharField(source="user.employee_id", read_only=True)
    evaluator_name = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentRecipient
        fields = [
            "id",
            "assignment",
            "user",
            "username",
            "full_name",
            "employee_id",
            "status",
            "submission_link",
            "submission_text",
            "submitted_at",
            "grade",
            "feedback",
            "evaluated_by",
            "evaluator_name",
            "evaluated_at",
            "created_at",
        ]
        read_only_fields = ["id", "assignment", "user", "created_at"]

    def get_full_name(self, obj):
        name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return name if name else obj.user.username

    def get_evaluator_name(self, obj):
        if obj.evaluated_by:
            name = f"{obj.evaluated_by.first_name} {obj.evaluated_by.last_name}".strip()
            return name if name else obj.evaluated_by.username
        return None


class AssignmentSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="topic", read_only=True)
    author_name = serializers.SerializerMethodField()
    posted_by_me = serializers.SerializerMethodField()
    target_cohort_code = serializers.SerializerMethodField()
    target_batch_code = serializers.SerializerMethodField()
    target_sub_batch_code = serializers.SerializerMethodField()
    target_username = serializers.SerializerMethodField()
    recipients_count = serializers.SerializerMethodField()
    submissions_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "topic",
            "title",
            "subject",
            "platform_link",
            "start_date",
            "deadline",
            "message",
            "recipient_type",
            "target_role",
            "target_cohort",
            "target_cohort_code",
            "target_batch_code",
            "target_sub_batch_code",
            "target_username",
            "audience",
            "author_name",
            "posted_by_me",
            "recipients_count",
            "submissions_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "title",
            "created_at",
            "updated_at",
            "author_name",
            "posted_by_me",
            "target_cohort_code",
            "target_batch_code",
            "target_sub_batch_code",
            "target_username",
            "recipients_count",
            "submissions_count",
        ]

    def get_author_name(self, obj):
        if not obj.created_by:
            return "Administrator"
        name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return name if name else obj.created_by.username

    def get_posted_by_me(self, obj):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            return obj.created_by_id == request.user.id
        return True

    def get_target_cohort_code(self, obj):
        return obj.target_cohort.code if obj.target_cohort else None

    def get_target_batch_code(self, obj):
        if obj.target_batch:
            return obj.target_batch.name
        first_b = obj.target_batches.first()
        return first_b.name if first_b else None

    def get_target_sub_batch_code(self, obj):
        if obj.target_sub_batch:
            return obj.target_sub_batch.name
        first_sb = obj.target_sub_batches.first()
        return first_sb.name if first_sb else None

    def get_target_username(self, obj):
        first_rec = obj.recipients.first()
        return first_rec.user.username if first_rec else None

    def get_recipients_count(self, obj):
        return obj.recipients.count()

    def get_submissions_count(self, obj):
        return obj.recipients.filter(status__in=["SUBMITTED", "EVALUATED"]).count()


class AssignmentDeadlineUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ["deadline"]

    def validate_deadline(self, value):
        if self.instance and value < self.instance.start_date:
            raise serializers.ValidationError("Deadline cannot be set earlier than the assignment start date.")
        return value


class AssignmentSubmitSerializer(serializers.Serializer):
    submission_link = serializers.URLField(max_length=500, required=False, allow_blank=True, allow_null=True)
    submission_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        if not data.get("submission_link") and not data.get("submission_text"):
            raise serializers.ValidationError("Please provide either a submission link or text/code response.")
        return data


class AssignmentEvaluateSerializer(serializers.Serializer):
    recipient_id = serializers.IntegerField(required=True)
    grade = serializers.CharField(max_length=20, required=True)
    feedback = serializers.CharField(required=False, allow_blank=True, default="")
