from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Broadcast, ScheduledLink, SiteSetting
from .serializers import BroadcastSerializer, ScheduledLinkSerializer

class BroadcastViewSet(viewsets.ModelViewSet):
    queryset = Broadcast.objects.all()
    serializer_class = BroadcastSerializer

class ScheduledLinkViewSet(viewsets.ModelViewSet):
    queryset = ScheduledLink.objects.all()
    serializer_class = ScheduledLinkSerializer

@api_view(['GET', 'PATCH'])
def buddy_setting(request):
    setting, _ = SiteSetting.objects.get_or_create(key='buddy_enabled', defaults={'value': 'true'})
    if request.method == 'PATCH':
        enabled = request.data.get('enabled')
        if not isinstance(enabled, bool):
            return Response({'detail': 'enabled must be true or false'}, status=status.HTTP_400_BAD_REQUEST)
        setting.value = 'true' if enabled else 'false'
        setting.save(update_fields=['value', 'updated_at'])
    return Response({'enabled': setting.value == 'true', 'updated_at': setting.updated_at})

@api_view(['GET'])
def dashboard_summary(request):
    return Response({
        'broadcast_count': Broadcast.objects.count(),
        'scheduled_count': ScheduledLink.objects.count(),
        'upcoming_count': ScheduledLink.objects.filter(publish_at__gte=timezone.now()).count(),
        'buddy_enabled': SiteSetting.objects.filter(key='buddy_enabled', value='true').exists(),
    })
