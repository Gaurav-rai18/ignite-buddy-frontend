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
