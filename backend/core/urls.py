from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BroadcastViewSet, ScheduledLinkViewSet, buddy_setting, dashboard_summary

router = DefaultRouter()
router.register('broadcasts', BroadcastViewSet, basename='broadcast')
router.register('schedules', ScheduledLinkViewSet, basename='schedule')
urlpatterns = [
    path('', include(router.urls)),
    path('settings/buddy/', buddy_setting),
    path('dashboard/', dashboard_summary),
]
