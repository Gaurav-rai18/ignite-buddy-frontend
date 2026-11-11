import datetime
import pytest
from django.utils import timezone
from server.apps.accounts.models import Cohort, Batch, SubBatch, User
from server.apps.buddy_controller.models import SystemSetting
from server.apps.buddy_controller.test_lock import get_active_test_lock
from server.apps.schedules.models import Schedule
from server.domain import policy


def test_active_test_lock_detection():
    # Setup cohort and sub-batch
    cohort, _ = Cohort.objects.get_or_create(code="B50_TEST", name="Batch 50 Test")
    batch, _ = Batch.objects.get_or_create(cohort=cohort, name="A")
    sb, _ = SubBatch.objects.get_or_create(batch=batch, name="A1")
    trainee, _ = User.objects.get_or_create(username="trainee_test_lock", sub_batch=sb)

    # Create active schedule with a test on Friday at 14:30 - 15:30
    grid = {
        "sub_batches": {
            "A1": {
                "fri": [
                    {
                        "id": "slot_a1_fri_0",
                        "day": "fri",
                        "start": "14:30",
                        "end": "15:30",
                        "title": "IO Exit Assessment",
                        "location": "WA",
                        "is_test": True,
                        "session_type": "test",
                    }
                ]
            }
        }
    }
    Schedule.objects.all().delete()
    Schedule.objects.create(
        title="Week 15 Schedule",
        grid_data=grid,
        is_active=True,
    )

    # Configure buffer to 15 mins before and 15 mins after
    SystemSetting.set_bool("test_auto_lock_enabled", True)
    SystemSetting.set_int("test_buffer_before_minutes", 15)
    SystemSetting.set_int("test_buffer_after_minutes", 15)

    # Pick a Friday datetime
    # 2026-11-13 is a Friday
    base_friday = timezone.make_aware(datetime.datetime(2026, 11, 13, 12, 0, 0))

    # 1. At 14:10 (20m before test) -> Should NOT be locked
    dt_1410 = base_friday.replace(hour=14, minute=10)
    res_1410 = get_active_test_lock(user=trainee, check_dt=dt_1410)
    assert res_1410["is_locked"] is False

    # 2. At 14:15 (Exactly 15m before test - start of lock window) -> Should be LOCKED
    dt_1415 = base_friday.replace(hour=14, minute=15)
    res_1415 = get_active_test_lock(user=trainee, check_dt=dt_1415)
    assert res_1415["is_locked"] is True
    assert "IO Exit Assessment" in res_1415["reason"]
    assert res_1415["buffer_before"] == 15

    # 3. At 15:00 (During test) -> Should be LOCKED
    dt_1500 = base_friday.replace(hour=15, minute=0)
    res_1500 = get_active_test_lock(user=trainee, check_dt=dt_1500)
    assert res_1500["is_locked"] is True

    # 4. At 15:45 (15m after test - end of lock window) -> Should be LOCKED
    dt_1545 = base_friday.replace(hour=15, minute=45)
    res_1545 = get_active_test_lock(user=trainee, check_dt=dt_1545)
    assert res_1545["is_locked"] is True

    # 5. At 15:46 (16m after test) -> Should NOT be locked
    dt_1546 = base_friday.replace(hour=15, minute=46)
    res_1546 = get_active_test_lock(user=trainee, check_dt=dt_1546)
    assert res_1546["is_locked"] is False

    # 6. Admin disables auto lock -> At 15:00 should NOT be locked
    SystemSetting.set_bool("test_auto_lock_enabled", False)
    res_disabled = get_active_test_lock(user=trainee, check_dt=dt_1500)
    assert res_disabled["is_locked"] is False
