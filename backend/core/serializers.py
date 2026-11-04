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
    class Meta:
        model = Broadcast
        fields = ['id', 'title', 'message', 'audience', 'created_at']

class ScheduleLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleLocation
        fields = ['id', 'name', 'badge', 'color', 'order']

class ScheduleSubBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleSubBatch
        fields = ['id', 'batch', 'name', 'code', 'order']

class ScheduleBatchSerializer(serializers.ModelSerializer):
    subbatches = ScheduleSubBatchSerializer(many=True, read_only=True)

    class Meta:
        model = ScheduleBatch
        fields = ['id', 'name', 'code', 'order', 'subbatches']

class ScheduleTimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleTimeSlot
        fields = ['id', 'start_time', 'end_time', 'label', 'order']

class ScheduleWeekDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleWeekDay
        fields = ['id', 'name', 'code', 'order']

class ScheduledLinkSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = SiteSetting
        fields = ['key', 'value', 'updated_at']
