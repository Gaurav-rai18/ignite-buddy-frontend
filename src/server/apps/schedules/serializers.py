from rest_framework import serializers
from .models import Schedule
from server.apps.accounts.serializers import BatchSerializer, SubBatchSerializer, CohortSerializer


class ScheduleSerializer(serializers.ModelSerializer):
    batch_detail = BatchSerializer(source="target_batch", read_only=True)
    sub_batch_detail = SubBatchSerializer(source="target_sub_batch", read_only=True)
    cohort_detail = CohortSerializer(source="target_cohort", read_only=True)

    class Meta:
        model = Schedule
        fields = '__all__'

    def validate_onedrive_url(self, value):
        if value and "onedrive" not in value.lower() and "1drv.ms" not in value.lower() and "sharepoint" not in value.lower():
            raise serializers.ValidationError(
                "Please enter a valid OneDrive or SharePoint link"
            )
        return value
