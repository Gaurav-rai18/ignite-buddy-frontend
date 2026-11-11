import io
import pytest
import openpyxl
from server.apps.schedules.parser import parse_schedule_excel


def test_parse_row_based_schedule():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Timetable"

    # Header rows
    ws.append(["TCS Ignite Training Program - Batch 1"])
    ws.append(["Day", "Start Time", "End Time", "Subject", "Room / Lab", "Faculty"])
    ws.append(["Monday", "09:00", "10:30", "Core Java & Spring", "Lab 3", "Dr. A. Sharma"])
    ws.append(["Monday", "11:00", "12:30", "DBMS & SQL", "Lab 2", "Prof. R. Verma"])
    ws.append(["Tuesday", "09:00", "10:30", "Python ML", "Lab 1", "Dr. S. Iyer"])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    result = parse_schedule_excel(buf)
    assert result["success"] is True
    assert result["slot_count"] == 3
    assert len(result["grid_data"]["mon"]) == 2
    assert result["grid_data"]["mon"][0]["title"] == "Core Java & Spring"
    assert result["grid_data"]["mon"][0]["location"] == "Lab 3"
    assert result["grid_data"]["mon"][0]["faculty"] == "Dr. A. Sharma"
    assert len(result["grid_data"]["tue"]) == 1
    assert result["grid_data"]["tue"][0]["title"] == "Python ML"


def test_parse_matrix_schedule():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Weekly Timetable"

    # Header with weekdays
    ws.append(["Time Slot", "Monday", "Tuesday", "Wednesday"])
    ws.append(["09:00 - 10:30", "Web Dev\nLab 2\nTrainer Rao", "Python\nLab 3\nTrainer Roy", "Cloud Computing\nLab 1"])
    ws.append(["11:00 - 12:30", "Algorithms\nLab 4", "System Design\nLab 2", "Testing & QA\nLab 3"])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    result = parse_schedule_excel(buf)
    assert result["success"] is True
    assert result["slot_count"] == 6
    assert len(result["grid_data"]["mon"]) == 2
    assert result["grid_data"]["mon"][0]["start"] == "09:00"
    assert result["grid_data"]["mon"][0]["end"] == "10:30"
    assert "Web Dev" in result["grid_data"]["mon"][0]["title"]


def test_parse_ignite_campus_workbook():
    import os
    path = os.path.join("data", "Batch50_Week15_Schedule.xlsx")
    if not os.path.exists(path):
        pytest.skip("Sample schedule file not present")

    result = parse_schedule_excel(path)
    assert result["success"] is True
    assert result["cohort"] == "B50"
    assert "A" in result["batches"]
    assert "B" in result["batches"]
    assert "C" in result["batches"]
    assert "A1" in result["sub_batches"]
    assert "C4" in result["sub_batches"]
    assert len(result["sub_batches"]) == 12
    assert result["slot_count"] == 480
    assert len(result["test_slots"]) > 0

    # Verify test detection
    test_slot = result["test_slots"][0]
    assert test_slot["is_test"] is True
    assert test_slot["session_type"] == "test"


def test_sync_grid_to_central_and_delta(monkeypatch):
    from unittest.mock import MagicMock
    import server.realtime.notifier as notifier_module
    monkeypatch.setattr(notifier_module, "sync_batch", MagicMock(return_value=True))
    monkeypatch.setattr(notifier_module, "broadcast_batch", MagicMock(return_value=True))

    from server.apps.schedules.views import _sync_grid_to_central, _find_changed_sub_batches
    from server.data.central import get_central

    grid_v1 = {
        "cohort": "B51",
        "sub_batches": {
            "A1": {
                "mon": [
                    {"start": "09:00", "end": "10:30", "title": "Java Fundamentals", "location": "Lab 1", "is_test": False}
                ]
            },
            "A2": {
                "mon": [
                    {"start": "09:00", "end": "10:30", "title": "Python Basics", "location": "Lab 2", "is_test": False}
                ]
            }
        }
    }

    # 1. Sync v1 to central without error
    _sync_grid_to_central(grid_v1, "B51")
    central = get_central()
    a1_slots = central.slots("A1")
    assert any(s["title"] == "Java Fundamentals" for s in a1_slots)

    # 2. Modify only A2
    grid_v2 = {
        "cohort": "B51",
        "sub_batches": {
            "A1": {
                "mon": [
                    {"start": "09:00", "end": "10:30", "title": "Java Fundamentals", "location": "Lab 1", "is_test": False}
                ]
            },
            "A2": {
                "mon": [
                    {"start": "09:00", "end": "10:30", "title": "Advanced Python", "location": "TR1", "is_test": True}
                ]
            }
        }
    }

    changed = _find_changed_sub_batches(grid_v1, grid_v2)
    assert changed == ["A2"]

    # 3. Delta sync only A2
    _sync_grid_to_central(grid_v2, "B51", changed_sub_batches=changed)
    a2_slots = central.slots("A2")
    assert any("[TEST] Advanced Python" in s["title"] and s["location"] == "TR1" for s in a2_slots)



