"""
core/urls.py — URL Routing for the Core Backend Application.

Registers DRF ViewSets using DefaultRouter and defines standalone URL paths
for custom API endpoints:
  - DefaultRouter provides automatic RESTful endpoints:
      /api/users/
      /api/broadcasts/
      /api/schedules/
      /api/schedule-locations/
      /api/schedule-batches/
      /api/schedule-subbatches/
      /api/schedule-timeslots/
      /api/schedule-weekdays/
  - Custom Views:
      /api/schedule-config/   -> schedule_config_view (complete timetable metadata)
      /api/schedule-template/ -> schedule_excel_template_view (downloadable .xlsx)
      /api/schedules/parse-excel/ -> schedule_parse_excel_view (validate/parse file)
      /api/login/             -> login_view (authentication)
      /api/settings/buddy/    -> buddy_setting (toggle Buddy exam mode)
      /api/dashboard/         -> dashboard_summary (metrics counters)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BroadcastViewSet,
    ScheduledLinkViewSet,
    UserViewSet,
    ScheduleLocationViewSet,
    ScheduleBatchViewSet,
    ScheduleSubBatchViewSet,
    ScheduleTimeSlotViewSet,
    ScheduleWeekDayViewSet,
    buddy_setting,
    dashboard_summary,
    login_view,
    schedule_config_view,
    schedule_excel_template_view,
    schedule_parse_excel_view,
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('broadcasts', BroadcastViewSet, basename='broadcast')
router.register('schedules', ScheduledLinkViewSet, basename='schedule')
router.register('schedule-locations', ScheduleLocationViewSet, basename='schedule-location')
router.register('schedule-batches', ScheduleBatchViewSet, basename='schedule-batch')
router.register('schedule-subbatches', ScheduleSubBatchViewSet, basename='schedule-subbatch')
router.register('schedule-timeslots', ScheduleTimeSlotViewSet, basename='schedule-timeslot')
router.register('schedule-weekdays', ScheduleWeekDayViewSet, basename='schedule-weekday')

urlpatterns = [
    path('schedule-config/', schedule_config_view, name='schedule-config'),
    path('schedule-template/', schedule_excel_template_view, name='schedule-template'),
    path('schedules/parse-excel/', schedule_parse_excel_view, name='schedule-parse-excel'),
    path('', include(router.urls)),
    path('login/', login_view),
    path('settings/buddy/', buddy_setting),
    path('dashboard/', dashboard_summary),
]
