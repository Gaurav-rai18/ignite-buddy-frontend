"""
Assignment URL routing
"""
from django.urls import path
from .views import (
    AssignmentListCreateView,
    AssignmentDetailView,
    AssignmentSubmissionView,
    AssignmentEvaluateView,
)

urlpatterns = [
    path("", AssignmentListCreateView.as_view(), name="assignment-list-create"),
    path("<int:pk>/", AssignmentDetailView.as_view(), name="assignment-detail"),
    path("<int:pk>/submissions/", AssignmentSubmissionView.as_view(), name="assignment-submissions"),
    path("<int:pk>/evaluate/", AssignmentEvaluateView.as_view(), name="assignment-evaluate-body"),
    path("<int:pk>/evaluate/<int:recipient_id>/", AssignmentEvaluateView.as_view(), name="assignment-evaluate"),
]
