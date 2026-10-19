from rest_framework import serializers
from .models import Broadcast, ScheduledLink, SiteSetting

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
