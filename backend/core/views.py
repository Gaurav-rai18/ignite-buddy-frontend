import json
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth import authenticate
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

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
from .serializers import (
    BroadcastSerializer,
    ScheduledLinkSerializer,
    UserSerializer,
    ScheduleLocationSerializer,
    ScheduleBatchSerializer,
    ScheduleSubBatchSerializer,
    ScheduleTimeSlotSerializer,
    ScheduleWeekDaySerializer,
)
from .excel_utils import generate_schedule_template, parse_schedule_excel

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
            'token': 'mock-server-token-' + str(user.id)
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

    def create(self, request, *args, **kwargs):
        # Support both standard json and multipart form data
        data = request.data.copy()
        excel_file = request.FILES.get('excel_file')
        if excel_file:
            data['excel_file'] = excel_file
            data['file_name'] = excel_file.name
            data['file_size'] = excel_file.size
            if not data.get('schedule_type'):
                data['schedule_type'] = 'excel'
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class ScheduleLocationViewSet(viewsets.ModelViewSet):
    queryset = ScheduleLocation.objects.all()
    serializer_class = ScheduleLocationSerializer

class ScheduleBatchViewSet(viewsets.ModelViewSet):
    queryset = ScheduleBatch.objects.prefetch_related('subbatches').all()
    serializer_class = ScheduleBatchSerializer

    def create(self, request, *args, **kwargs):
        name = request.data.get('name', '').strip()
        code = request.data.get('code', '').strip().upper()
        if not code and name:
            # Generate code from name (e.g. "Batch D" -> "D")
            code = name.replace('Batch', '').strip().upper()[:5] or name[:2].upper()
        if not name and code:
            name = f'Batch {code}'

        if ScheduleBatch.objects.filter(code__iexact=code).exists():
            return Response({'detail': f"Batch code '{code}' already exists."}, status=status.HTTP_400_BAD_REQUEST)
        if ScheduleBatch.objects.filter(name__iexact=name).exists():
            return Response({'detail': f"Batch name '{name}' already exists."}, status=status.HTTP_400_BAD_REQUEST)

        order = request.data.get('order')
        if order is None:
            order = ScheduleBatch.objects.count() + 1

        batch = ScheduleBatch.objects.create(name=name, code=code, order=order)

        # Auto-create initial subbatches if specified or create 4 by default
        initial_count = int(request.data.get('subbatches_count', 4))
        for i in range(1, initial_count + 1):
            ScheduleSubBatch.objects.create(
                batch=batch,
                name=f"{code}{i}",
                code=f"{code.lower()}{i}",
                order=i,
            )

        serializer = self.get_serializer(batch)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ScheduleSubBatchViewSet(viewsets.ModelViewSet):
    queryset = ScheduleSubBatch.objects.all()
    serializer_class = ScheduleSubBatchSerializer

    def create(self, request, *args, **kwargs):
        batch_id = request.data.get('batch')
        name = request.data.get('name', '').strip()
        code = request.data.get('code', '').strip().lower()

        try:
            batch = ScheduleBatch.objects.get(id=batch_id)
        except (ScheduleBatch.DoesNotExist, ValueError):
            return Response({'detail': 'Invalid batch ID provided.'}, status=status.HTTP_400_BAD_REQUEST)

        if not name:
            # Auto-assign next number (e.g. A5)
            next_num = batch.subbatches.count() + 1
            name = f"{batch.code}{next_num}"
        if not code:
            code = name.lower()

        if ScheduleSubBatch.objects.filter(batch=batch, code=code).exists():
            return Response(
                {'detail': f"Sub-batch '{name}' already exists in {batch.name}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order = request.data.get('order', batch.subbatches.count() + 1)
        subbatch = ScheduleSubBatch.objects.create(batch=batch, name=name, code=code, order=order)
        serializer = self.get_serializer(subbatch)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ScheduleTimeSlotViewSet(viewsets.ModelViewSet):
    queryset = ScheduleTimeSlot.objects.all()
    serializer_class = ScheduleTimeSlotSerializer

    def create(self, request, *args, **kwargs):
        start_time = request.data.get('start_time', '').strip()
        end_time = request.data.get('end_time', '').strip()
        label = request.data.get('label', '').strip()

        if not start_time or not end_time:
            return Response({'detail': 'Start time and end time are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not label:
            label = f"{start_time} – {end_time}"

        # Prevent duplicate label
        if ScheduleTimeSlot.objects.filter(label__iexact=label).exists():
            return Response({'detail': f"Time slot '{label}' already exists."}, status=status.HTTP_400_BAD_REQUEST)

        order = request.data.get('order', ScheduleTimeSlot.objects.count() + 1)
        timeslot = ScheduleTimeSlot.objects.create(
            start_time=start_time,
            end_time=end_time,
            label=label,
            order=order,
        )
        serializer = self.get_serializer(timeslot)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ScheduleWeekDayViewSet(viewsets.ModelViewSet):
    queryset = ScheduleWeekDay.objects.all()
    serializer_class = ScheduleWeekDaySerializer

    def create(self, request, *args, **kwargs):
        name = request.data.get('name', '').strip()
        if name.lower() in ['saturday', 'sunday']:
            return Response(
                {'detail': 'Saturday and Sunday cannot be added. Only Monday through Friday are working days.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

@api_view(['GET'])
def schedule_config_view(request):
    """
    Returns the complete dynamic configuration for schedule builder.
    """
    locations = ScheduleLocation.objects.all()
    batches = ScheduleBatch.objects.prefetch_related('subbatches').all()
    time_slots = ScheduleTimeSlot.objects.all()
    weekdays = ScheduleWeekDay.objects.all()

    return Response({
        'locations': ScheduleLocationSerializer(locations, many=True).data,
        'batches': ScheduleBatchSerializer(batches, many=True).data,
        'time_slots': ScheduleTimeSlotSerializer(time_slots, many=True).data,
        'weekdays': ScheduleWeekDaySerializer(weekdays, many=True).data,
    })

@api_view(['GET'])
def schedule_excel_template_view(request):
    """
    Generates and returns an Excel schedule template using current database locations and batches.
    """
    locations = list(ScheduleLocation.objects.values_list('name', flat=True))
    batches = list(ScheduleBatch.objects.values_list('name', flat=True))
    timeslots = list(ScheduleTimeSlot.objects.values_list('label', flat=True))

    file_bytes = generate_schedule_template(locations=locations, batches=batches, timeslots=timeslots)

    response = HttpResponse(
        file_bytes,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="ScheduleTemplate.xlsx"'
    return response

@api_view(['POST'])
def schedule_parse_excel_view(request):
    """
    Parses and validates an uploaded Excel schedule file.
    """
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({'detail': 'No file was uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check extension
    filename = uploaded_file.name.lower()
    if not (filename.endswith('.xlsx') or filename.endswith('.xls')):
        return Response(
            {'detail': 'Invalid file type. Please upload a valid Excel spreadsheet (.xlsx or .xls).'},
            status=status.HTTP_400_BAD_REQUEST
        )

    valid_locations = list(ScheduleLocation.objects.values_list('name', flat=True))
    result = parse_schedule_excel(uploaded_file.read(), valid_locations=valid_locations)

    if not result.get('valid'):
        return Response({
            'success': False,
            'errors': result.get('errors', ['Failed to parse Excel file.']),
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        'success': True,
        'file_name': uploaded_file.name,
        'file_size': uploaded_file.size,
        'total_rows_parsed': result.get('total_rows_parsed', 0),
        'days_found': result.get('days_found', []),
        'selected_day': result.get('selected_day', 'Monday'),
        'days_data': result.get('days_data', {}),
        'grid': result.get('grid', {}),
        'warnings': result.get('errors', []),
    })

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
