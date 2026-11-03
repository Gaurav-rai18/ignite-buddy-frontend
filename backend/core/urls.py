from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BroadcastViewSet, ScheduledLinkViewSet, UserViewSet, buddy_setting, dashboard_summary, login_view

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('broadcasts', BroadcastViewSet, basename='broadcast')
router.register('schedules', ScheduledLinkViewSet, basename='schedule')
urlpatterns = [
    path('', include(router.urls)),
    path('login/', login_view),
    path('settings/buddy/', buddy_setting),
    path('dashboard/', dashboard_summary),
]
