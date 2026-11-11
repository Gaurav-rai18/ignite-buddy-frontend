from django.urls import path
from .views import (
    ScheduleListCreateView,
    ScheduleDetailView,
    ScheduleActivateView,
    ScheduleParseExcelView,
    BatchTimetableLiveView,
    TraineeCurrentSeatingView,
)

urlpatterns = [
    path('', ScheduleListCreateView.as_view(), name='schedule-list-create'),
    path('<int:pk>/', ScheduleDetailView.as_view(), name='schedule-detail'),
    path('<int:pk>/activate/', ScheduleActivateView.as_view(), name='schedule-activate'),
    path('parse-excel/', ScheduleParseExcelView.as_view(), name='schedule-parse-excel'),
    path('live-timetable/', BatchTimetableLiveView.as_view(), name='schedule-live-timetable'),
    path('current-seating/', TraineeCurrentSeatingView.as_view(), name='schedule-current-seating'),
]
