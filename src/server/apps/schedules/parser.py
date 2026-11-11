"""
Timetable Excel Parser
Parses campus schedules from Excel workbooks into normalized JSON grid formats.
Supports:
  1. TCS Ignite Multi-Sheet Campus Workbooks (Schedule, Stream, Faculty, TA Mapping, Proctoring).
  2. Sub-batch and batch-wise matrix schedules with interleaved or single-row layouts.
  3. Row-based lecture lists.
  4. Standard weekday matrix grids.
"""
import re
import uuid
import openpyxl

WEEKDAY_MAP = {
    "monday": "mon", "mon": "mon", "m": "mon",
    "tuesday": "tue", "tue": "tue", "tues": "tue", "t": "tue",
    "wednesday": "wed", "wed": "wed", "w": "wed",
    "thursday": "thu", "thu": "thu", "thur": "thu", "thurs": "thu", "th": "thu",
    "friday": "fri", "fri": "fri", "f": "fri",
    "saturday": "sat", "sat": "sat", "s": "sat",
}

TIME_PATTERN = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", re.IGNORECASE)


def normalize_time(val: str) -> str:
    """Normalizes string time representations to HH:MM format."""
    if not val:
        return ""
    val_str = str(val).strip().lower()
    match = TIME_PATTERN.search(val_str)
    if not match:
        return val_str[:5]
    hours = int(match.group(1))
    minutes = int(match.group(2) or 0)
    meridiem = match.group(3)

    if meridiem == "pm" and hours < 12:
        hours += 12
    elif meridiem == "am" and hours == 12:
        hours = 0
    return f"{hours:02d}:{minutes:02d}"


def parse_time_range(raw: str) -> tuple[str, str]:
    """Splits '09:00 - 10:30' or '9am to 10:30am' into (start, end)."""
    if not raw:
        return "", ""
    parts = re.split(r"[-–—to]+", str(raw), maxsplit=1)
    if len(parts) == 2:
        return normalize_time(parts[0]), normalize_time(parts[1])
    return normalize_time(parts[0]), ""


def _parse_ignite_campus_workbook(wb) -> dict:
    """
    Parses a TCS Ignite master schedule workbook containing sub-batches, batches,
    streams, TA mappings, and exit tests.
    """
    ws = wb["Schedule"] if "Schedule" in wb.sheetnames else wb.active

    # 1. Unfold all merged cells so every coordinate has correct value and fill
    merged_map = {}
    for rng in ws.merged_cells.ranges:
        min_col, min_row, max_col, max_row = rng.min_col, rng.min_row, rng.max_col, rng.max_row
        top_cell = ws.cell(min_row, min_col)
        top_val = top_cell.value
        top_fill = top_cell.fill
        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                merged_map[(r, c)] = (top_val, top_fill)

    def get_cell(r, c):
        if (r, c) in merged_map:
            return merged_map[(r, c)]
        cell = ws.cell(r, c)
        return (cell.value, cell.fill)

    # 2. Extract TA mapping (Home Labs, Primary/Backup TAs, Batch Owners)
    ta_mapping = {}
    detected_cohort_ta = ""
    if "TA mapping" in wb.sheetnames:
        ta_ws = wb["TA mapping"]
        for r in range(3, ta_ws.max_row + 1):
            c_val = str(ta_ws.cell(r, 2).value or "").strip()
            if c_val and not detected_cohort_ta:
                detected_cohort_ta = c_val
            sb = ta_ws.cell(r, 4).value
            if sb:
                sb_str = str(sb).strip()
                ta_mapping[sb_str] = {
                    "cohort": c_val or "B50",
                    "batch": str(ta_ws.cell(r, 3).value or sb_str[0]).strip(),
                    "primary_ta": str(ta_ws.cell(r, 5).value or "").strip(),
                    "backup_ta": str(ta_ws.cell(r, 6).value or "").strip(),
                    "owner": str(ta_ws.cell(r, 7).value or "").strip(),
                    "home_lab": str(ta_ws.cell(r, 8).value or "").strip(),
                }

    # 3. Extract Proctoring List (Invigilators for exit evaluations)
    proctoring = {}
    if "Proctoring List" in wb.sheetnames:
        p_ws = wb["Proctoring List"]
        header_row = 2
        test_cols = {}
        for c in range(4, p_ws.max_column + 1):
            tname = p_ws.cell(header_row, c).value
            if tname:
                test_cols[c] = str(tname).strip()
        for r in range(header_row + 1, p_ws.max_row + 1):
            sb = p_ws.cell(r, 3).value
            if sb:
                sb_str = str(sb).strip()
                proctoring[sb_str] = {}
                for col_idx, tname in test_cols.items():
                    invig = p_ws.cell(r, col_idx).value
                    if invig:
                        proctoring[sb_str][tname] = str(invig).strip()

    # 4. Extract Stream Faculty & Stream Schedules
    stream_faculty = {}
    if "Stream Faculty" in wb.sheetnames:
        sf_ws = wb["Stream Faculty"]
        for r in range(2, sf_ws.max_row + 1):
            s_name = sf_ws.cell(r, 2).value
            if s_name:
                stream_faculty[str(s_name).strip()] = {
                    "primary": str(sf_ws.cell(r, 3).value or "").strip(),
                    "backup": str(sf_ws.cell(r, 4).value or "").strip(),
                }

    stream_schedule = {}
    if "Stream" in wb.sheetnames:
        s_ws = wb["Stream"]
        # Map Stream sheet days and timings
        s_cols = []
        for c in range(3, s_ws.max_column + 1):
            d_val = s_ws.cell(1, c).value
            t_val = s_ws.cell(2, c).value
            if t_val:
                s_cols.append((c, str(d_val or "").strip().lower(), str(t_val).strip()))
        for r in range(3, s_ws.max_row + 1):
            s_name = s_ws.cell(r, 1).value
            if s_name:
                s_name_str = str(s_name).strip()
                stream_schedule[s_name_str] = {}
                for c_idx, d_name, t_slot in s_cols:
                    day_c = WEEKDAY_MAP.get(d_name, "mon")
                    room_allocated = s_ws.cell(r, c_idx).value
                    if room_allocated:
                        stream_schedule[s_name_str].setdefault(day_c, []).append({
                            "time": t_slot,
                            "room": str(room_allocated).strip(),
                            "faculty": stream_faculty.get(s_name_str, {}).get("primary", ""),
                        })

    # 5. Extract Days and Time Slots from Schedule sheet
    col_day_slot = []
    for c in range(2, ws.max_column + 1):
        day_raw, _ = get_cell(1, c)
        slot_raw, _ = get_cell(2, c)
        if not day_raw or not slot_raw:
            continue
        day_str = str(day_raw).strip().lower()
        day_code = WEEKDAY_MAP.get(day_str)
        if not day_code:
            continue

        slot_str = str(slot_raw).strip()
        m = TIME_PATTERN.search(slot_str)
        if m:
            h = int(m.group(1))
            mins = int(m.group(2) or 0)
            mer = (m.group(3) or "").lower()
            if mer == "pm" and h < 12:
                h += 12
            elif mer == "am" and h == 12:
                h = 0
            start_t = f"{h:02d}:{mins:02d}"
            end_h = (h + 1) if (h + 1) < 24 else 0
            end_t = f"{end_h:02d}:{mins:02d}"
        else:
            start_t, end_t = "09:00", "10:00"

        col_day_slot.append({
            "col": c,
            "day": day_code,
            "slot_label": slot_str,
            "start": start_t,
            "end": end_t,
        })

    # 6. Extract Sub-batches and Slots
    sub_batch_rows = []
    r = 3
    while r <= ws.max_row:
        val, _ = ws.cell(r, 1).value, None
        if not val and (r, 1) in merged_map:
            val = merged_map[(r, 1)][0]
        if val and re.match(r"^[A-Za-z]+\d+$", str(val).strip()):
            sb_code = str(val).strip()
            # Check if row r+1 is a room row (empty or merged with same sub-batch)
            next_val = ws.cell(r + 1, 1).value if (r + 1) <= ws.max_row else None
            if not next_val and (r + 1, 1) in merged_map:
                next_val = merged_map[(r + 1, 1)][0]

            is_two_row = (r + 1 <= ws.max_row) and (not next_val or str(next_val).strip() == sb_code)
            sub_batch_rows.append((sb_code, r, is_two_row))
            r += 2 if is_two_row else 1
        else:
            r += 1

    sub_batches_data = {}
    batches_data = {}
    flat_grid = {"mon": [], "tue": [], "wed": [], "thu": [], "fri": [], "sat": []}
    all_test_slots = []
    total_slot_count = 0

    cohort_raw = str(get_cell(1, 1)[0] or detected_cohort_ta or "B50").strip()
    cohort_m = re.search(r"\b(B\d+|Cohort\s*\d+|Batch\s*\d+)\b", cohort_raw, re.IGNORECASE)
    cohort_str = cohort_m.group(1).upper() if cohort_m else cohort_raw

    for sb_code, row_idx, is_two_row in sub_batch_rows:
        batch_letter = re.match(r"^([A-Za-z]+)", sb_code).group(1)
        if batch_letter not in batches_data:
            batches_data[batch_letter] = {
                "name": batch_letter,
                "cohort": cohort_str,
                "sub_batches": [],
            }
        if sb_code not in batches_data[batch_letter]["sub_batches"]:
            batches_data[batch_letter]["sub_batches"].append(sb_code)

        home_lab = ta_mapping.get(sb_code, {}).get("home_lab") or "Home Lab"
        sub_batches_data[sb_code] = {"mon": [], "tue": [], "wed": [], "thu": [], "fri": [], "sat": []}

        for col_info in col_day_slot:
            c = col_info["col"]
            day = col_info["day"]
            subj_val, subj_fill = get_cell(row_idx, c)
            room_val, room_fill = get_cell(row_idx + 1, c) if is_two_row else (None, None)

            subject = str(subj_val or "").strip()
            room = str(room_val or "").strip()

            if not subject and not room:
                continue

            if not subject and room:
                subject = "Incubator"
            if not room:
                room = home_lab

            # Fill color detection
            fill_color = "none"
            for f in (subj_fill, room_fill):
                if f and f.start_color and f.start_color.rgb:
                    rgb_str = str(f.start_color.rgb).upper()
                    if rgb_str not in ("00000000", "FFFFFFFF"):
                        fill_color = rgb_str
                        break

            # Test detection
            subj_lower = subject.lower()
            room_lower = room.lower()
            is_test = False
            if any(k in subj_lower for k in ("exit", "test", "eval", "exam", "assessment")) or "ts" in room_lower or fill_color == "FFFFB74D":
                is_test = True

            # Session type classification
            if is_test:
                session_type = "test"
            elif subj_lower == "stream":
                session_type = "stream"
            elif fill_color in ("FF64B5F6", "64B5F6") or "tr" in room_lower:
                session_type = "faculty"
            elif fill_color in ("FF81C784", "81C784", "FF2E7D32", "2E7D32"):
                session_type = "in_place"
            else:
                session_type = "self_study"

            # Invigilator / Faculty assignment
            proctor = proctoring.get(sb_code, {}).get(subject, "")
            faculty = ""
            if session_type == "stream" and subject in stream_faculty:
                faculty = stream_faculty[subject].get("primary", "")
            elif session_type == "faculty":
                faculty = ta_mapping.get(sb_code, {}).get("primary_ta", "")

            slot_item = {
                "id": f"slot_{sb_code.lower()}_{day}_{len(sub_batches_data[sb_code][day])}",
                "sub_batch": sb_code,
                "batch": batch_letter,
                "cohort": cohort_str,
                "day": day,
                "start": col_info["start"],
                "end": col_info["end"],
                "time_label": col_info["slot_label"],
                "title": subject,
                "location": room,
                "session_type": session_type,
                "is_test": is_test,
                "color": fill_color,
                "faculty": faculty,
                "proctor": proctor,
            }

            sub_batches_data[sb_code][day].append(slot_item)
            flat_grid[day].append(slot_item)
            total_slot_count += 1

            if is_test:
                all_test_slots.append(slot_item)

    return {
        "success": total_slot_count > 0,
        "cohort": cohort_str,
        "detected_cohort": cohort_str,
        "detected_batch": list(batches_data.keys())[0] if batches_data else "",
        "slot_count": total_slot_count,
        "sub_batches": sub_batches_data,
        "batches": batches_data,
        "grid_data": flat_grid,
        "ta_mapping": ta_mapping,
        "proctoring": proctoring,
        "streams": stream_schedule,
        "stream_faculty": stream_faculty,
        "test_slots": all_test_slots,
        "errors": [],
    }


def parse_schedule_excel(excel_file) -> dict:
    """
    Parses an uploaded Excel file and returns normalized schedule JSON.
    Auto-detects:
      - TCS Ignite Campus Multi-Batch Workbook (Schedule, TA Mapping, Stream)
      - Standard Weekday Matrix Timetable
      - Row-based flat timetable list
    """
    try:
        wb = openpyxl.load_workbook(excel_file, data_only=True)
    except Exception as exc:
        return {
            "success": False,
            "grid_data": {"mon": [], "tue": [], "wed": [], "thu": [], "fri": [], "sat": []},
            "slot_count": 0,
            "errors": [f"Could not read Excel file: {exc}"],
        }

    # Strategy 0: Check if this is a TCS Ignite Campus Master Schedule workbook
    if "Schedule" in wb.sheetnames:
        return _parse_ignite_campus_workbook(wb)

    ws = wb.active
    # Also check if sheet 1 has sub-batches in column 1 (e.g. A1, A2, B1) and days in row 1
    c1_sample = [str(ws.cell(r, 1).value or "").strip() for r in range(1, min(10, ws.max_row + 1))]
    r1_sample = [str(ws.cell(1, c).value or "").strip().lower() for c in range(1, min(10, ws.max_column + 1))]
    if any(re.match(r"^[A-Za-z]+\d+$", x) for x in c1_sample) and any(d in r1_sample for d in ("monday", "tuesday")):
        return _parse_ignite_campus_workbook(wb)

    all_rows = list(ws.iter_rows(values_only=True))
    if not all_rows:
        return {
            "success": False,
            "grid_data": {"mon": [], "tue": [], "wed": [], "thu": [], "fri": [], "sat": []},
            "slot_count": 0,
            "errors": ["Worksheet is empty"],
        }

    grid_data = {
        "mon": [],
        "tue": [],
        "wed": [],
        "thu": [],
        "fri": [],
        "sat": [],
    }

    detected_batch = ""
    detected_cohort = ""
    errors = []

    # Search top 4 rows for batch or cohort labels
    for r in all_rows[:4]:
        for cell in r:
            if not cell:
                continue
            c_text = str(cell).strip()
            b_match = re.search(r"(?:batch|section)\s*[:#-]?\s*([A-Za-z0-9_-]+)", c_text, re.IGNORECASE)
            if b_match and not detected_batch:
                detected_batch = b_match.group(1)
            c_match = re.search(r"(?:cohort)\s*[:#-]?\s*([A-Za-z0-9_-]+)", c_text, re.IGNORECASE)
            if c_match and not detected_cohort:
                detected_cohort = c_match.group(1)

    # Strategy A: Check if columns represent Weekdays (Matrix layout)
    header_row_idx = -1
    day_col_indices = {}

    for row_idx, r in enumerate(all_rows[:8]):
        found_days = {}
        for col_idx, cell in enumerate(r):
            if not cell:
                continue
            cleaned = str(cell).strip().lower()
            if cleaned in WEEKDAY_MAP:
                found_days[WEEKDAY_MAP[cleaned]] = col_idx
        if len(found_days) >= 3:
            header_row_idx = row_idx
            day_col_indices = found_days
            break

    if header_row_idx != -1 and day_col_indices:
        # Matrix Layout: Rows are time slots, columns are days
        for r in all_rows[header_row_idx + 1:]:
            if not any(c is not None for c in r):
                continue
            # Look for a time string in the first 2 columns
            time_raw = ""
            for cell in r[:3]:
                if cell and ("am" in str(cell).lower() or "pm" in str(cell).lower() or ":" in str(cell) or "-" in str(cell)):
                    time_raw = str(cell).strip()
                    break

            start_t, end_t = parse_time_range(time_raw)

            for day_code, col_idx in day_col_indices.items():
                if col_idx >= len(r) or not r[col_idx]:
                    continue
                cell_val = str(r[col_idx]).strip()
                if not cell_val or cell_val.lower() in ("-", "nil", "na", "n/a", "recess", "break", "lunch"):
                    continue

                lines = [l.strip() for l in re.split(r"[\n\r/|]+", cell_val) if l.strip()]
                subject = lines[0] if lines else "Lecture"
                room = ""
                faculty = ""

                for sub_line in lines[1:]:
                    if re.search(r"lab|room|hall|lh|audi|ts|wa|tr", sub_line, re.IGNORECASE):
                        room = sub_line
                    elif re.search(r"dr\.|prof\.|mr\.|ms\.|mrs\.|trainer|faculty", sub_line, re.IGNORECASE) or not faculty:
                        faculty = sub_line

                subj_lower = subject.lower()
                is_test = any(k in subj_lower for k in ("exit", "test", "eval", "exam", "assessment")) or "ts" in (room or "").lower()

                grid_data[day_code].append({
                    "id": f"slot_{uuid.uuid4().hex[:8]}",
                    "start": start_t or "09:00",
                    "end": end_t or "10:30",
                    "title": subject,
                    "location": room or "Home Lab",
                    "faculty": faculty,
                    "is_test": is_test,
                    "session_type": "test" if is_test else "faculty" if faculty else "self_study",
                })

    else:
        # Strategy B: Row-by-Row Layout (Day, Start, End, Subject, Room, Faculty)
        header_map = {}
        for row_idx, r in enumerate(all_rows[:6]):
            for col_idx, cell in enumerate(r):
                if not cell:
                    continue
                c_clean = str(cell).strip().lower()
                if any(w in c_clean for w in ("day", "weekday")):
                    header_map["day"] = col_idx
                elif any(w in c_clean for w in ("start", "from", "start_time")):
                    header_map["start"] = col_idx
                elif any(w in c_clean for w in ("end", "to", "end_time")):
                    header_map["end"] = col_idx
                elif any(w in c_clean for w in ("time", "timing", "slot")):
                    header_map["time_range"] = col_idx
                elif any(w in c_clean for w in ("subject", "course", "module", "topic", "session", "title")):
                    header_map["subject"] = col_idx
                elif any(w in c_clean for w in ("room", "lab", "venue", "location")):
                    header_map["location"] = col_idx
                elif any(w in c_clean for w in ("faculty", "trainer", "instructor", "teacher")):
                    header_map["faculty"] = col_idx

            if "day" in header_map and ("subject" in header_map or "title" in header_map):
                header_row_idx = row_idx
                break

        if "day" in header_map:
            for r in all_rows[header_row_idx + 1:]:
                if not any(c is not None for c in r):
                    continue
                day_val = str(r[header_map["day"]]).strip().lower() if header_map.get("day") is not None and header_map["day"] < len(r) else ""
                day_code = WEEKDAY_MAP.get(day_val)
                if not day_code:
                    continue

                subject = str(r[header_map["subject"]]).strip() if header_map.get("subject") is not None and header_map["subject"] < len(r) and r[header_map["subject"]] else "Lecture"

                start_t = ""
                end_t = ""
                if header_map.get("time_range") is not None and header_map["time_range"] < len(r) and r[header_map["time_range"]]:
                    start_t, end_t = parse_time_range(r[header_map["time_range"]])
                else:
                    if header_map.get("start") is not None and header_map["start"] < len(r) and r[header_map["start"]]:
                        start_t = normalize_time(str(r[header_map["start"]]))
                    if header_map.get("end") is not None and header_map["end"] < len(r) and r[header_map["end"]]:
                        end_t = normalize_time(str(r[header_map["end"]]))

                loc = str(r[header_map["location"]]).strip() if header_map.get("location") is not None and header_map["location"] < len(r) and r[header_map["location"]] else "Home Lab"
                fac = str(r[header_map["faculty"]]).strip() if header_map.get("faculty") is not None and header_map["faculty"] < len(r) and r[header_map["faculty"]] else ""

                subj_lower = subject.lower()
                is_test = any(k in subj_lower for k in ("exit", "test", "eval", "exam", "assessment")) or "ts" in (loc or "").lower()

                grid_data[day_code].append({
                    "id": f"slot_{uuid.uuid4().hex[:8]}",
                    "start": start_t or "09:00",
                    "end": end_t or "10:30",
                    "title": subject,
                    "location": loc,
                    "faculty": fac,
                    "is_test": is_test,
                    "session_type": "test" if is_test else "faculty" if fac else "self_study",
                })

    # Sort each day's slots by start time
    total_slots = 0
    for day_code in grid_data:
        grid_data[day_code].sort(key=lambda item: item.get("start", "00:00"))
        total_slots += len(grid_data[day_code])

    return {
        "success": total_slots > 0,
        "grid_data": grid_data,
        "slot_count": total_slots,
        "detected_batch": detected_batch,
        "detected_cohort": detected_cohort,
        "errors": errors if total_slots == 0 else [],
    }
