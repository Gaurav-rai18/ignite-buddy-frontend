from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone

from server.domain import policy


class DashboardSummaryView(APIView):
    """
    Returns summary metrics for the Admin Dashboard:
      - broadcast_count
      - scheduled_count
      - upcoming_count
      - buddy_enabled
      - total_users
      - total_trainees
      - total_cohorts
      - total_batches
      - total_sub_batches
    """
    def get(self, request):
        now = timezone.now()

        broadcast_count = 0
        try:
            from server.apps.notifications.models import Notification
            broadcast_count = Notification.objects.filter(is_broadcast=True).count()
        except Exception:
            pass

        scheduled_count = 0
        upcoming_count = 0
        try:
            from server.apps.schedules.models import Schedule
            scheduled_count = Schedule.objects.count()
            upcoming_count = Schedule.objects.filter(publish_at__gte=now).count()
        except Exception:
            pass

        total_users = 0
        total_trainees = 0
        total_cohorts = 0
        total_batches = 0
        total_sub_batches = 0
        try:
            from server.apps.accounts.models import User, Cohort, Batch, SubBatch
            total_users = User.objects.count()
            total_trainees = User.objects.filter(role="TRAINEE").count()
            total_cohorts = Cohort.objects.count()
            total_batches = Batch.objects.count()
            total_sub_batches = SubBatch.objects.count()
        except Exception:
            pass

        buddy_enabled = not policy.is_blocked()
        try:
            from server.apps.buddy_controller.models import SystemSetting
            buddy_enabled = SystemSetting.get_bool("buddy_enabled", default=buddy_enabled)
        except Exception:
            pass

        return Response({
            "broadcast_count": broadcast_count,
            "scheduled_count": scheduled_count,
            "upcoming_count": upcoming_count,
            "buddy_enabled": buddy_enabled,
            "total_users": total_users,
            "total_trainees": total_trainees,
            "total_cohorts": total_cohorts,
            "total_batches": total_batches,
            "total_sub_batches": total_sub_batches,
        })
