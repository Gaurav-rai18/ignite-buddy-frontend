"""
Schedule Views for Ignite Buddy
Manages weekly timetable creation, JSON grid storage, Excel timetable parsing,
and real-time broadcast alerts to TCS Ignite batches.
"""
import uuid
import datetime
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Schedule
from .serializers import ScheduleSerializer
from .parser import parse_schedule_excel
from server.apps.accounts.permissions import IsUserManagementStaff
from server.data.central import get_central
from server.realtime import notifier


DAY_TO_INT = {
    "mon": 0, "monday": 0, "0": 0,
    "tue": 1, "tuesday": 1, "1": 1,
    "wed": 2, "wednesday": 2, "2": 2,
    "thu": 3, "thursday": 3, "3": 3,
    "fri": 4, "friday": 4, "4": 4,
    "sat": 5, "saturday": 5, "5": 5,
    "sun": 6, "sunday": 6, "6": 6,
}


def _find_changed_sub_batches(old_grid: dict | None, new_grid: dict | None) -> list[str]:
    """
    Compares two schedule grids and identifies which sub-batches had changes
    in their lecture titles, rooms, times, or test statuses.
    Returns list of sub-batch codes that were modified.
    If old_grid is empty/none, returns all sub-batches in new_grid.
    """
    if not new_grid or not isinstance(new_grid, dict):
        return []

    new_sbs = new_grid.get("sub_batches", {})
    if not isinstance(new_sbs, dict) or not new_sbs:
        return []

    if not old_grid or not isinstance(old_grid, dict):
        return list(new_sbs.keys())

    old_sbs = old_grid.get("sub_batches", {})
    if not isinstance(old_sbs, dict):
        return list(new_sbs.keys())

    changed = []
    for sb_code, new_days in new_sbs.items():
        if sb_code not in old_sbs:
            changed.append(sb_code)
            continue

        old_days = old_sbs[sb_code]
        sb_changed = False
        for day in ("mon", "tue", "wed", "thu", "fri", "sat"):
            new_slots = new_days.get(day, [])
            old_slots = old_days.get(day, [])
            if len(new_slots) != len(old_slots):
                sb_changed = True
                break
            for ns, os in zip(new_slots, old_slots):
                if (
                    ns.get("title") != os.get("title")
                    or ns.get("location") != os.get("location")
                    or ns.get("is_test") != os.get("is_test")
                    or ns.get("start") != os.get("start")
                    or ns.get("end") != os.get("end")
                ):
                    sb_changed = True
                    break
            if sb_changed:
                break

        if sb_changed:
            changed.append(sb_code)

    return changed


def _get_target_batch(instance: Schedule) -> str:
    target_batch = "*"
    if instance.target_type == "SUB_BATCH" and instance.target_sub_batch:
        target_batch = instance.target_sub_batch.full_code
    elif instance.target_type == "BATCH" and instance.target_batch:
        target_batch = instance.target_batch.full_code
    elif instance.target_type == "COHORT" and instance.target_cohort:
        target_batch = instance.target_cohort.code
    return target_batch


def _notify_schedule_update(target_batch: str, changed_sub_batches: list[str] | None, all_sub_batches: list[str] | None = None):
    """
    Intelligently sends alerts:
    - If specific sub-batches changed (subset), notifies ONLY those affected sub-batches.
    - If all or initial publish, notifies the overall target cohort/batch.
    """
    if changed_sub_batches is not None and len(changed_sub_batches) > 0:
        if all_sub_batches and len(changed_sub_batches) < len(all_sub_batches):
            for sb in changed_sub_batches:
                try:
                    notifier.broadcast_batch(
                        sb,
                        f"Timetable Update: Your weekly schedule for sub-batch {sb} has been updated. Please verify venue allocations.",
                    )
                except Exception:
                    pass
            return

    try:
        notifier.broadcast_batch(
            target_batch,
            f"Schedule Update: Master weekly timetable for {target_batch} has been published/updated.",
        )
    except Exception:
        pass


def _sync_grid_to_central(grid_data: dict, target_batch: str, changed_sub_batches: list[str] | None = None):
    """Syncs a schedule's weekly grid slots into central.db and broadcasts to trainees."""
    if not grid_data:
        return

    central = get_central()
    cohort_str = str(grid_data.get("cohort") or "").strip()

    # Case A: Multi-sub-batch layout
    if "sub_batches" in grid_data and isinstance(grid_data["sub_batches"], dict):
        all_sbs = list(grid_data["sub_batches"].keys())
        target_sbs = changed_sub_batches if (changed_sub_batches is not None and len(changed_sub_batches) > 0) else all_sbs

        for sb_code in target_sbs:
            day_dict = grid_data["sub_batches"].get(sb_code)
            if not isinstance(day_dict, dict):
                continue
            for day_code, slots in day_dict.items():
                if not isinstance(slots, list):
                    continue
                w_int = DAY_TO_INT.get(str(day_code).lower(), 0)
                for slot in slots:
                    start_str = str(slot.get("start", "09:00"))
                    end_str = str(slot.get("end", "10:30"))
                    start_clean = start_str.replace(":", "")
                    end_clean = end_str.replace(":", "")
                    sid = str(slot.get("id") or f"{sb_code}_{w_int}_{start_clean}_{end_clean}")

                    title = str(slot.get("title", "Lecture"))
                    if slot.get("is_test") and "[TEST]" not in title:
                        title = f"[TEST] {title}"

                    loc = str(slot.get("location", "Home Lab"))

                    # Save under short sub-batch code (e.g. "B2")
                    central.upsert_slot(
                        batch=sb_code,
                        weekday=w_int,
                        start=start_str,
                        end=end_str,
                        title=title,
                        location=loc,
                        sid=sid,
                    )

                    # Also save under cohort-qualified code if available (e.g. "B50-B2")
                    if cohort_str and not sb_code.startswith(f"{cohort_str}-"):
                        full_code = f"{cohort_str}-{sb_code}"
                        central.upsert_slot(
                            batch=full_code,
                            weekday=w_int,
                            start=start_str,
                            end=end_str,
                            title=title,
                            location=loc,
                            sid=f"{full_code}_{w_int}_{start_clean}_{end_clean}",
                        )

            try:
                notifier.sync_batch(sb_code)
                if cohort_str:
                    notifier.sync_batch(f"{cohort_str}-{sb_code}")
            except Exception:
                pass

        try:
            notifier.sync_batch(target_batch)
            notifier.sync_batch("*")
        except Exception:
            pass
        return

    # Case B: Flat day-wise slots
    for day_code, slots in grid_data.items():
        if not isinstance(slots, list):
            continue
        w_int = DAY_TO_INT.get(str(day_code).lower(), 0)
        for slot in slots:
            batch_for_slot = slot.get("sub_batch") or target_batch
            start_str = str(slot.get("start", "09:00"))
            end_str = str(slot.get("end", "10:30"))
            start_clean = start_str.replace(":", "")
            end_clean = end_str.replace(":", "")
            sid = str(slot.get("id") or f"{batch_for_slot}_{w_int}_{start_clean}_{end_clean}")

            title = str(slot.get("title", "Lecture"))
            if slot.get("is_test") and "[TEST]" not in title:
                title = f"[TEST] {title}"

            central.upsert_slot(
                batch=batch_for_slot,
                weekday=w_int,
                start=start_str,
                end=end_str,
                title=title,
                location=str(slot.get("location", "Home Lab")),
                sid=sid,
            )

    try:
        notifier.sync_batch(target_batch)
        notifier.sync_batch("*")
    except Exception:
        pass


class ScheduleListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsUserManagementStaff]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        schedules = Schedule.objects.all().select_related("target_cohort", "target_batch", "target_sub_batch").order_by("-is_active", "-effective_from", "-created_at")

        batch_id = request.query_params.get("batch_id")
        cohort_id = request.query_params.get("cohort_id")
        target_type = request.query_params.get("target_type")

        if batch_id:
            schedules = schedules.filter(target_batch_id=batch_id)
        if cohort_id:
            schedules = schedules.filter(target_cohort_id=cohort_id)
        if target_type:
            schedules = schedules.filter(target_type=target_type.upper())

        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        if request.user.is_authenticated:
            data["created_by"] = request.user.id

        grid_data = data.get("grid_data")
        cohort_code = ""
        if isinstance(grid_data, dict):
            cohort_code = grid_data.get("cohort", "")

        effective_from_raw = data.get("effective_from")
        effective_from_date = None
        if effective_from_raw:
            try:
                effective_from_date = datetime.date.fromisoformat(str(effective_from_raw).split("T")[0])
            except Exception:
                effective_from_date = None

        today = datetime.date.today()
        is_future = effective_from_date is not None and effective_from_date > today

        if is_future:
            # Future week schedule: mark SCHEDULED, inactive
            data["is_active"] = False
            data["status"] = "SCHEDULED"
        else:
            if data.get("is_active", True):
                # Archive existing active schedules for the target cohort so history is preserved
                target_cohort_id = data.get("target_cohort")
                if target_cohort_id:
                    Schedule.objects.filter(target_cohort_id=target_cohort_id, is_active=True).update(is_active=False, status="ARCHIVED")
                else:
                    Schedule.objects.filter(is_active=True).update(is_active=False, status="ARCHIVED")
                data["is_active"] = True
                data["status"] = "PUBLISHED"

        serializer = ScheduleSerializer(data=data)
        if serializer.is_valid():
            instance = serializer.save()
            target_batch = _get_target_batch(instance)
            all_sbs = list(grid_data.get("sub_batches", {}).keys()) if isinstance(grid_data, dict) else []

            if instance.is_active:
                if instance.grid_data:
                    _sync_grid_to_central(instance.grid_data, target_batch)
                _notify_schedule_update(target_batch, None, all_sub_batches=all_sbs)
                msg = "Schedule created, published, and synchronized to trainees."
            else:
                msg = f"Schedule saved for upcoming week (effective from {effective_from_date or 'scheduled date'}). Trainees will not be notified until this schedule becomes active."

            return Response(
                {
                    "message": msg,
                    "data": serializer.data,
                    "is_future": is_future,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScheduleDetailView(APIView):
    permission_classes = [IsAuthenticated, IsUserManagementStaff]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self, pk):
        return Schedule.objects.filter(pk=pk).select_related("target_cohort", "target_batch", "target_sub_batch").first()

    def get(self, request, pk):
        schedule = self.get_object(pk)
        if not schedule:
            return Response({"error": "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ScheduleSerializer(schedule)
        return Response(serializer.data)

    def put(self, request, pk):
        schedule = self.get_object(pk)
        if not schedule:
            return Response({"error": "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)

        old_grid = schedule.grid_data or {}
        new_grid = request.data.get("grid_data", old_grid)
        all_sbs = list(new_grid.get("sub_batches", {}).keys()) if isinstance(new_grid, dict) else []
        changed_sbs = _find_changed_sub_batches(old_grid, new_grid)

        put_data = request.data.copy()
        effective_from_raw = put_data.get("effective_from", schedule.effective_from)
        effective_from_date = None
        if effective_from_raw:
            try:
                effective_from_date = datetime.date.fromisoformat(str(effective_from_raw).split("T")[0])
            except Exception:
                effective_from_date = None

        today = datetime.date.today()
        is_future = effective_from_date is not None and effective_from_date > today
        force_activate = bool(put_data.get("force_activate"))

        if is_future and not force_activate:
            put_data["is_active"] = False
            put_data["status"] = "SCHEDULED"

        if (put_data.get("is_active") is True and not is_future) or force_activate:
            target_cohort_id = put_data.get("target_cohort") or schedule.target_cohort_id
            if target_cohort_id:
                Schedule.objects.filter(target_cohort_id=target_cohort_id, is_active=True).exclude(pk=schedule.pk).update(is_active=False, status="ARCHIVED")
            else:
                Schedule.objects.filter(is_active=True).exclude(pk=schedule.pk).update(is_active=False, status="ARCHIVED")
            put_data["is_active"] = True
            put_data["status"] = "PUBLISHED"

        serializer = ScheduleSerializer(schedule, data=put_data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            target_batch = _get_target_batch(instance)

            if instance.is_active:
                if instance.grid_data:
                    _sync_grid_to_central(instance.grid_data, target_batch, changed_sub_batches=changed_sbs)
                _notify_schedule_update(target_batch, changed_sbs, all_sub_batches=all_sbs)
                msg = "Schedule updated and synced to trainees."
            else:
                msg = f"Schedule saved for upcoming week (effective from {effective_from_date or 'scheduled date'}). Trainees will not be notified until this schedule becomes active."

            return Response(
                {
                    "message": msg,
                    "data": serializer.data,
                    "changed_sub_batches": changed_sbs if instance.is_active else [],
                }
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        schedule = self.get_object(pk)
        if not schedule:
            return Response({"error": "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)

        target_batch = _get_target_batch(schedule)
        grid_data = schedule.grid_data or {}
        was_active = schedule.is_active

        schedule.delete()

        if was_active and grid_data:
            try:
                central = get_central()
                sbs = list(grid_data.get("sub_batches", {}).keys()) if isinstance(grid_data, dict) else []
                for sb in sbs:
                    central.delete_batch_slots(sb)
                    notifier.sync_batch(sb)
                if target_batch and target_batch != "*":
                    central.delete_batch_slots(target_batch)
                    notifier.sync_batch(target_batch)
                notifier.sync_batch("*")
            except Exception:
                pass

        return Response({"message": "Schedule deleted successfully"}, status=status.HTTP_200_OK)


class ScheduleActivateView(APIView):
    """
    Activates an existing scheduled or archived week schedule, archiving any
    previously active timetable for the cohort and immediately broadcasting to trainees.
    """
    permission_classes = [IsAuthenticated, IsUserManagementStaff]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, pk):
        return self._activate(request, pk)

    def put(self, request, pk):
        return self._activate(request, pk)

    def _activate(self, request, pk):
        schedule = Schedule.objects.filter(pk=pk).select_related("target_cohort", "target_batch").first()
        if not schedule:
            return Response({"error": "Schedule not found"}, status=status.HTTP_404_NOT_FOUND)

        # Deactivate other active schedules for the same cohort
        if schedule.target_cohort_id:
            Schedule.objects.filter(target_cohort_id=schedule.target_cohort_id, is_active=True).exclude(pk=schedule.pk).update(is_active=False, status="ARCHIVED")
        else:
            Schedule.objects.filter(is_active=True).exclude(pk=schedule.pk).update(is_active=False, status="ARCHIVED")

        schedule.is_active = True
        schedule.status = "PUBLISHED"
        schedule.save()

        target_batch = _get_target_batch(schedule)
        grid_data = schedule.grid_data or {}
        all_sbs = list(grid_data.get("sub_batches", {}).keys()) if isinstance(grid_data, dict) else []

        if grid_data:
            _sync_grid_to_central(grid_data, target_batch)
        _notify_schedule_update(target_batch, None, all_sub_batches=all_sbs)

        serializer = ScheduleSerializer(schedule)
        return Response(
            {
                "message": f"Schedule '{schedule.title}' is now active and synchronized to trainees.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ScheduleParseExcelView(APIView):
    """
    Parses an uploaded timetable Excel sheet into a JSON grid structure
    for immediate review and editing in the Admin UI before saving.
    """
    permission_classes = [IsAuthenticated, IsUserManagementStaff]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        excel_file = request.FILES.get("file") or request.FILES.get("excel_file")
        if not excel_file:
            return Response(
                {"error": "Please select a timetable Excel file (.xlsx) to upload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = parse_schedule_excel(excel_file)
        if not result["success"] and result.get("errors"):
            return Response(
                {"error": result["errors"][0] if result["errors"] else "Failed to parse schedule."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class BatchTimetableLiveView(APIView):
    """
    Returns the live active weekly timetable for a batch directly from central.db or Schedule model.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        batch = request.query_params.get("batch", "*")
        rows = get_central().timetable(batch)
        return Response({"batch": batch, "slots": rows})


def resolve_current_seating(sub_batch_code: str, stream_name: str = "", dt=None) -> dict:
    """
    Deterministically resolves where a trainee must sit right now based on active schedules.
    """
    if dt is None:
        dt = timezone.localtime()

    day_map = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
    day_code = day_map.get(dt.weekday(), "mon")
    time_str = dt.strftime("%H:%M")

    active_schedule = Schedule.objects.filter(is_active=True).first()
    if not active_schedule or not active_schedule.grid_data:
        return {
            "status": "no_schedule",
            "message": "No active schedule published yet."
        }

    grid = active_schedule.grid_data
    sub_batch_slots = grid.get("sub_batches", {}).get(sub_batch_code, {}).get(day_code, [])

    matched_slot = None
    for s in sub_batch_slots:
        if s.get("start", "") <= time_str < s.get("end", ""):
            matched_slot = s
            break

    if not matched_slot:
        return {
            "status": "off_hours",
            "sub_batch": sub_batch_code,
            "message": f"No active lecture scheduled right now for {sub_batch_code} ({time_str})."
        }

    title = matched_slot.get("title", "Lecture")
    loc = matched_slot.get("location", "Home Lab")
    is_test = matched_slot.get("is_test", False)

    # Stream Hour Resolution
    if title.lower() == "stream" and stream_name:
        stream_slots = grid.get("streams", {}).get(stream_name, {}).get(day_code, [])
        for ss in stream_slots:
            if ss.get("time") in matched_slot.get("time_label", ""):
                loc = ss.get("room", loc)
                break
        return {
            "status": "in_session",
            "sub_batch": sub_batch_code,
            "stream": stream_name,
            "subject": f"Stream: {stream_name}",
            "location": loc,
            "is_test": False,
            "time_label": matched_slot.get("time_label", ""),
            "message": f"Currently in session: Stream ({stream_name}) in {loc} ({matched_slot.get('time_label', '')}).",
        }

    return {
        "status": "in_session",
        "sub_batch": sub_batch_code,
        "subject": title,
        "location": loc,
        "is_test": is_test,
        "time_label": matched_slot.get("time_label", ""),
        "message": f"Currently in session: {title} in {loc} ({matched_slot.get('time_label', '')}).",
    }


class TraineeCurrentSeatingView(APIView):
    """
    Answers: 'Where do I sit right now?' deterministically for any trainee, TA or agent.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub_batch = request.query_params.get("sub_batch")
        stream = request.query_params.get("stream", "")

        # Fallback to authenticated trainee's profile
        if not sub_batch and request.user.is_authenticated and hasattr(request.user, "sub_batch") and request.user.sub_batch:
            sub_batch = request.user.sub_batch.name

        if not sub_batch:
            return Response(
                {"error": "Please specify sub_batch query parameter (e.g. ?sub_batch=A1)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        test_time = request.query_params.get("time")
        test_day = request.query_params.get("day")
        check_dt = None
        if test_time and test_day:
            day_num = {"mon": 9, "tue": 10, "wed": 11, "thu": 12, "fri": 13}.get(test_day.lower(), 9)
            h, m = [int(x) for x in test_time.split(":")]
            check_dt = timezone.make_aware(datetime.datetime(2026, 11, day_num, h, m, 0))

        result = resolve_current_seating(sub_batch, stream_name=stream, dt=check_dt)
        return Response(result, status=status.HTTP_200_OK)

