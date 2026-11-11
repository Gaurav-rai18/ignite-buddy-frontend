from django.urls import path

from .views import (
    start_exam,
    end_exam,
    exam_status,
    get_or_update_buddy_setting,
)

urlpatterns = [
    path("start-exam/", start_exam),
    path("end-exam/", end_exam),
    path("status/", exam_status),
    path("setting/", get_or_update_buddy_setting),
]
