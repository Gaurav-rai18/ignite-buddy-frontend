from rest_framework import serializers
from .models import Broadcast, ScheduledLink, SiteSetting, User

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

class ScheduledLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledLink
        fields = ['id', 'title', 'onedrive_url', 'publish_at', 'created_at']

class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = ['key', 'value', 'updated_at']
