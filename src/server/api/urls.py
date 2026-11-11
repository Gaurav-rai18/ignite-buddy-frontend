"""URL routing for the Admin API (DRF ViewSets)."""
from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter(trailing_slash=False)
router.register(r"admin-api/assignments", views.AssignmentViewSet, basename="assignments")
router.register(r"admin-api/timetable", views.TimetableViewSet, basename="timetable")
router.register(r"admin-api/trainees", views.TraineeViewSet, basename="trainees")

urlpatterns = [
    path("health", views.HealthView.as_view(), name="health"),
    path("auth/login", views.LoginView.as_view(), name="auth-login"),
    *router.urls,
]
