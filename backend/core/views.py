"""
core/views.py — API views for the Ignite Buddy Admin Console.

This module contains all ViewSets and function-based views that make up the
REST API. The views are organized into:

  Authentication:
    login_view — POST /api/login/

  CRUD ViewSets (registered via DRF router in urls.py):
    UserViewSet          — /api/users/
    BroadcastViewSet     — /api/broadcasts/
    ScheduledLinkViewSet — /api/schedules/        (supports JSON + multipart FormData)
    ScheduleLocationViewSet  — /api/schedule-locations/
    ScheduleBatchViewSet     — /api/schedule-batches/    (auto-creates sub-batches)
    ScheduleSubBatchViewSet  — /api/schedule-subbatches/
    ScheduleTimeSlotViewSet  — /api/schedule-timeslots/
    ScheduleWeekDayViewSet   — /api/schedule-weekdays/   (blocks Saturday/Sunday)

  Function-based views:
    schedule_config_view       — GET  /api/schedule-config/
    schedule_excel_template_view — GET  /api/schedule-template/
    schedule_parse_excel_view  — POST /api/schedules/parse-excel/
    buddy_setting              — GET/PATCH /api/settings/buddy/
    dashboard_summary          — GET  /api/dashboard/

All endpoints currently use AllowAny or no explicit permission (for dev).
In production, add proper authentication/authorization.
"""

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
    """
    Authenticate a user and return their profile + mock token.

    POST /api/login/
    Body: { "username": "...", "password": "..." }

    Returns 200 with user data + token on success, 401 on bad credentials.
    Currently uses Django's built-in authenticate() and returns a mock token
    (not JWT). In production, replace with a proper token system.
    """
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
    """CRUD API for campus users. GET /api/users/, POST, PUT, PATCH, DELETE."""
    queryset = User.objects.all()
    serializer_class = UserSerializer


class BroadcastViewSet(viewsets.ModelViewSet):
    """CRUD API for broadcast announcements. Ordered by newest first."""
    queryset = Broadcast.objects.all()
    serializer_class = BroadcastSerializer


class ScheduledLinkViewSet(viewsets.ModelViewSet):
    """
    CRUD API for schedule items (timetables, links, Excel uploads).

    GET  /api/schedules/     — List all schedules (ordered by publish_at).
    POST /api/schedules/     — Create a new schedule.
    DELETE /api/schedules/N/ — Delete schedule with id=N.

    The create() method is overridden to support two payload formats:
      1. JSON body — for native grid schedules (schedule_type='grid').
      2. Multipart FormData — for Excel uploads (schedule_type='excel'),
         where the .xlsx file is in request.FILES['excel_file'].
    """
    queryset = ScheduledLink.objects.all()
    serializer_class = ScheduledLinkSerializer

    def create(self, request, *args, **kwargs):
        """
        Handle both JSON and multipart FormData schedule creation.

        For Excel uploads, the file is extracted from request.FILES,
        schedule_type is auto-set to 'excel', and file metadata is populated.
        For native grid, the payload is plain JSON with content_data as a
        JSON-stringified timetable object.
        """
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
    """CRUD API for timetable grid locations (Lab 1, Lab 2, ..., TR2)."""
    queryset = ScheduleLocation.objects.all()
    serializer_class = ScheduleLocationSerializer


class ScheduleBatchViewSet(viewsets.ModelViewSet):
    """
    CRUD API for batch groups (Batch A, Batch B, etc.).

    POST /api/schedule-batches/ — Creates a new batch and auto-generates
    sub-batches (4 by default, configurable via 'subbatches_count').

    Business rules:
      - Code is auto-derived from name if not provided (e.g., 'Batch D' → 'D').
      - Name is auto-derived from code if not provided (e.g., 'D' → 'Batch D').
      - Duplicate name or code → 400 Bad Request.
      - Order defaults to (current count + 1).

    DELETE /api/schedule-batches/N/ — Deletes batch and CASCADE-deletes
    all its sub-batches.
    """
    queryset = ScheduleBatch.objects.prefetch_related('subbatches').all()
    serializer_class = ScheduleBatchSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new batch with auto-generated sub-batches.

        Steps:
          1. Extract and normalize name/code from request.
          2. Check for duplicates (code and name, case-insensitive).
          3. Create the ScheduleBatch row.
          4. Auto-create N sub-batches (default 4): D1, D2, D3, D4.
          5. Return the full batch with nested subbatches.
        """
        name = request.data.get('name', '').strip()
        code = request.data.get('code', '').strip().upper()
        if not code and name:
            # Auto-derive code from name: "Batch D" → "D"
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

        # Auto-create initial subbatches (default 4: e.g., D1, D2, D3, D4)
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
    """
    CRUD API for individual sub-batches (A1, A2, B3, D5, etc.).

    POST /api/schedule-subbatches/ — Creates a sub-batch in a given batch.
    If name/code are omitted, auto-generates the next sequential number
    (e.g., if batch A has A1-A4, creates A5).

    Validates: parent batch exists, no duplicate code within the same batch.
    """
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
    """
    CRUD API for timetable time slots.

    POST  /api/schedule-timeslots/   — Create a new time slot.
    PATCH /api/schedule-timeslots/N/ — Update an existing time slot.
    DELETE /api/schedule-timeslots/N/ — Remove a time slot.

    Validation: duplicate label → 400. start_time and end_time required.
    The label is auto-generated as '{start} – {end}' if not provided.
    Overlap detection is done client-side (validation.js), not server-side.
    """
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
    """
    CRUD API for schedule weekdays.

    POST /api/schedule-weekdays/ — Create a weekday.
    IMPORTANT: Saturday and Sunday are explicitly rejected (400 error)
    to enforce the 5-day working schedule policy.
    """
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
    Return the complete dynamic configuration for the schedule builder.

    GET /api/schedule-config/

    This is the first API call the frontend makes when the Schedule page loads.
    It returns all four config arrays in a single response so the React grid
    knows what columns (locations), rows (time slots), day tabs (weekdays),
    and batch chip groups (batches + sub-batches) to render.

    Response shape:
    {
      "locations":  [{ id, name, badge, color, order }],
      "batches":    [{ id, name, code, order, subbatches: [{ id, batch, name, code, order }] }],
      "time_slots": [{ id, start_time, end_time, label, order }],
      "weekdays":   [{ id, name, code, order }]
    }
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
    Generate and download a styled Excel timetable template.

    GET /api/schedule-template/

    Dynamically reads current locations, batches, and time slots from the DB
    to create a pre-formatted .xlsx template with:
      - Correct column headers (Day, Start Time, End Time, Lab/Location, etc.)
      - Sample data rows using actual location names
      - An 'Instructions & Valid Values' reference sheet
      - Professional styling (header colors, borders, column widths)

    Returns the file as a downloadable attachment.
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
    Parse and validate an uploaded Excel timetable file.

    POST /api/schedules/parse-excel/
    Content-Type: multipart/form-data
    Body: { file: <uploaded .xlsx/.xls file> }

    Processing steps:
      1. Validate file presence and extension (.xlsx or .xls).
      2. Load valid location names from the database for matching.
      3. Call parse_schedule_excel() from excel_utils to extract grid data.
      4. Return parsed data or validation errors.

    Success response (200):
    {
      "success": true,
      "file_name": "schedule.xlsx",
      "file_size": 12480,
      "total_rows_parsed": 9,
      "days_found": ["Monday", "Tuesday"],
      "selected_day": "Monday",
      "days_data": { [day]: { [timeSlot]: { [location]: { topic, subbatches[] } } } },
      "grid": { ... Monday's data ... },
      "warnings": []
    }

    Error response (400):
    { "success": false, "errors": ["..."] }
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
    """
    Get or update the Buddy AI assistant availability status.

    GET   /api/settings/buddy/ — Returns { "enabled": true/false, "updated_at": "..." }
    PATCH /api/settings/buddy/ — Body: { "enabled": true/false }
                                 Updates site-wide setting in SiteSetting model.
    """
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
    """
    Aggregate metrics for the Admin Dashboard home screen.

    GET /api/dashboard/

    Returns counts of:
      - Total published broadcasts
      - Total schedules
      - Upcoming schedules (publish_at >= now)
      - Buddy AI active state
    """
    return Response({
        'broadcast_count': Broadcast.objects.count(),
        'scheduled_count': ScheduledLink.objects.count(),
        'upcoming_count': ScheduledLink.objects.filter(publish_at__gte=timezone.now()).count(),
        'buddy_enabled': SiteSetting.objects.filter(key='buddy_enabled', value='true').exists(),
    })
