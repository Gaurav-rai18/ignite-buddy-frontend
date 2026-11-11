"""
Automated Test Lockdown Engine
Monitors published schedules and automatically disables the Trainee Buddy
assistant during scheduled assessment/exit test hours (including configurable
buffers before and after the test).
"""
import datetime
from django.utils import timezone
from .models import SystemSetting


DAY_CODE_MAP = {
    0: "mon",
    1: "tue",
    2: "wed",
    3: "thu",
    4: "fri",
    5: "sat",
    6: "sun",
}


def parse_hm(time_str: str) -> tuple[int, int]:
    """Parses 'HH:MM' into (hour, minute)."""
    try:
        parts = str(time_str).strip().split(":")
        return int(parts[0]), int(parts[1])
    except Exception:
        return 9, 0


def get_active_test_lock(user=None, check_dt=None) -> dict:
    """
    Evaluates whether the Trainee Buddy assistant is currently locked due to
    an active assessment/test in the weekly schedule.

    Parameters:
        user: Optional User instance. If provided, evaluates tests for their sub_batch/batch.
        check_dt: Optional datetime for simulation/testing. Defaults to current local time.

    Returns:
        dict: {
            "is_locked": bool,
            "test_title": str,
            "target_sub_batch": str,
            "target_batch": str,
            "location": str,
            "start_time": str,
            "end_time": str,
            "lock_start": str,
            "lock_end": str,
            "buffer_before": int,
            "buffer_after": int,
            "reason": str,
            "auto_lock_enabled": bool,
        }
    """
    auto_lock_enabled = SystemSetting.get_bool("test_auto_lock_enabled", default=True)
    buffer_before = SystemSetting.get_int("test_buffer_before_minutes", default=15)
    buffer_after = SystemSetting.get_int("test_buffer_after_minutes", default=15)

    base_response = {
        "is_locked": False,
        "test_title": "",
        "target_sub_batch": "",
        "target_batch": "",
        "location": "",
        "start_time": "",
        "end_time": "",
        "lock_start": "",
        "lock_end": "",
        "buffer_before": buffer_before,
        "buffer_after": buffer_after,
        "reason": "",
        "auto_lock_enabled": auto_lock_enabled,
    }

    if not auto_lock_enabled:
        return base_response

    if check_dt is None:
        check_dt = timezone.localtime()

    weekday_code = DAY_CODE_MAP.get(check_dt.weekday(), "mon")

    # Lazy import to prevent circular dependencies
    try:
        from server.apps.schedules.models import Schedule
    except ImportError:
        return base_response

    # Retrieve all active schedules
    active_schedules = Schedule.objects.filter(is_active=True)
    if not active_schedules.exists():
        return base_response

    # User context
    user_sb_code = ""
    user_batch_code = ""
    if user and hasattr(user, "sub_batch") and user.sub_batch:
        user_sb_code = user.sub_batch.name
        if hasattr(user.sub_batch, "batch") and user.sub_batch.batch:
            user_batch_code = user.sub_batch.batch.name

    for schedule in active_schedules:
        grid_data = schedule.grid_data or {}
        candidate_slots = []

        # 1. Sub-batch-wise lookup
        if "sub_batches" in grid_data and isinstance(grid_data["sub_batches"], dict):
            if user_sb_code and user_sb_code in grid_data["sub_batches"]:
                candidate_slots.extend(grid_data["sub_batches"][user_sb_code].get(weekday_code, []))
            else:
                for sb_dict in grid_data["sub_batches"].values():
                    if isinstance(sb_dict, dict):
                        candidate_slots.extend(sb_dict.get(weekday_code, []))

        # 2. Check test_slots array if present
        if "test_slots" in grid_data and isinstance(grid_data["test_slots"], list):
            for t_slot in grid_data["test_slots"]:
                if t_slot.get("day") == weekday_code:
                    if not user_sb_code or t_slot.get("sub_batch") == user_sb_code or not t_slot.get("sub_batch"):
                        candidate_slots.append(t_slot)

        # 3. Flat day grid fallback
        if weekday_code in grid_data and isinstance(grid_data[weekday_code], list):
            for f_slot in grid_data[weekday_code]:
                if f_slot.get("is_test"):
                    if not user_sb_code or f_slot.get("sub_batch") == user_sb_code or not f_slot.get("sub_batch"):
                        candidate_slots.append(f_slot)

        for slot in candidate_slots:
            if not slot.get("is_test"):
                continue

            start_str = slot.get("start")
            end_str = slot.get("end")
            if not start_str or not end_str:
                continue

            start_h, start_m = parse_hm(start_str)
            end_h, end_m = parse_hm(end_str)

            test_start = check_dt.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
            test_end = check_dt.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

            lock_start = test_start - datetime.timedelta(minutes=buffer_before)
            lock_end = test_end + datetime.timedelta(minutes=buffer_after)

            if lock_start <= check_dt <= lock_end:
                title = slot.get("title", "Assessment")
                sb = slot.get("sub_batch") or user_sb_code or "All Sub-Batches"
                batch = slot.get("batch") or user_batch_code or "All Batches"
                loc = slot.get("location") or "Testing Venue"

                reason = (
                    f"Assessment in progress ({title} in {loc}). "
                    f"Buddy assistant is automatically disabled from {lock_start.strftime('%I:%M %p')} "
                    f"to {lock_end.strftime('%I:%M %p')} "
                    f"({buffer_before}m preparation and {buffer_after}m wrap-up buffers)."
                )

                return {
                    "is_locked": True,
                    "test_title": title,
                    "target_sub_batch": sb,
                    "target_batch": batch,
                    "location": loc,
                    "start_time": start_str,
                    "end_time": end_str,
                    "lock_start": lock_start.strftime("%I:%M %p"),
                    "lock_end": lock_end.strftime("%I:%M %p"),
                    "buffer_before": buffer_before,
                    "buffer_after": buffer_after,
                    "reason": reason,
                    "auto_lock_enabled": True,
                }

    return base_response

