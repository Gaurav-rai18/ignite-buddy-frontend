from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Broadcast, ScheduledLink, SiteSetting, User
from .serializers import BroadcastSerializer, ScheduledLinkSerializer, UserSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'detail': 'Please provide both username and password.'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'batch': user.batch,
            'subbatch': user.subbatch,
            'status': user.status,
            'token': 'mock-server-token-' + str(user.id) # In real app, use JWT or Token
        })
    else:
        return Response({'detail': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

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
