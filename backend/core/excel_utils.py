import io
import re
from datetime import datetime, time
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ALLOWED_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

def format_time_str(val):
    if val is None:
        return ''
    if isinstance(val, time):
        # Format as 12-hour AM/PM
        return val.strftime('%I:%M %p').lstrip('0')
    if isinstance(val, datetime):
        return val.strftime('%I:%M %p').lstrip('0')
    s = str(val).strip()
    return s

def normalize_day(val):
    if not val:
        return None
    s = str(val).strip().capitalize()
    for day in ALLOWED_DAYS:
        if s.lower() == day.lower() or s.lower() == day[:3].lower():
            return day
    return s

def generate_schedule_template(locations=None, batches=None, timeslots=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Schedule'

    # Ensure grid lines are visible
    ws.views.sheetView[0].showGridLines = True

    # Styling
    header_fill = PatternFill(start_color='014BAA', end_color='014BAA', fill_type='solid')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    header_align = Alignment(horizontal='center', vertical='center', wrap_text=True)

    headers = [
        'Day',
        'Start Time',
        'End Time',
        'Lab / Location',
        'Topic / Subject',
        'Batch',
        'Sub-Batch',
    ]

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align
        cell.border = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1'),
        )

    # Sample rows
    sample_locations = locations or [
        'Lab 1', 'Lab 2', 'Lab 3', 'Lab 4', 'Work Area', 'TR1', 'TR2'
    ]
    sample_rows = [
        ['Monday', '9:00 AM', '11:00 AM', sample_locations[0] if len(sample_locations) > 0 else 'Lab 1', 'Digital Logic & Circuit Design', 'Batch A', 'A1, A2'],
        ['Monday', '9:00 AM', '11:00 AM', sample_locations[1] if len(sample_locations) > 1 else 'Lab 2', 'Full Stack React & Node Development', 'Batch B', 'B1, B2'],
        ['Monday', '9:00 AM', '11:00 AM', sample_locations[2] if len(sample_locations) > 2 else 'Lab 3', 'Machine Learning Models & PyTorch', 'Batch C', 'C1'],
        ['Monday', '11:30 AM', '1:30 PM', sample_locations[3] if len(sample_locations) > 3 else 'Lab 4', 'Cloud Kubernetes & DevOps CI/CD', 'Batch A', 'A3, A4'],
        ['Monday', '11:30 AM', '1:30 PM', sample_locations[4] if len(sample_locations) > 4 else 'Work Area', 'Capstone Team Project Sprint', 'Batch B', 'B3, B4'],
        ['Monday', '2:00 PM', '4:00 PM', sample_locations[5] if len(sample_locations) > 5 else 'TR1', 'Technical Interview Prep & Soft Skills', 'Batch C', 'C2, C3'],
        ['Monday', '2:00 PM', '4:00 PM', sample_locations[6] if len(sample_locations) > 6 else 'TR2', 'Competitive Coding & System Design', 'Batch C', 'C4'],
        ['Tuesday', '9:00 AM', '11:00 AM', sample_locations[0] if len(sample_locations) > 0 else 'Lab 1', 'Microcontroller Interfacing', 'Batch B', 'B1'],
        ['Tuesday', '11:30 AM', '1:30 PM', sample_locations[1] if len(sample_locations) > 1 else 'Lab 2', 'Advanced Database & SQL Optimization', 'Batch A', 'A1, A2'],
    ]

    regular_font = Font(name='Calibri', size=10)
    regular_align = Alignment(vertical='center')
    center_align = Alignment(horizontal='center', vertical='center')

    for row_idx, row_data in enumerate(sample_rows, start=2):
        for col_idx, val in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = regular_font
            cell.alignment = center_align if col_idx in [1, 2, 3, 6, 7] else regular_align
            cell.border = Border(
                left=Side(style='thin', color='E2E8F0'),
                right=Side(style='thin', color='E2E8F0'),
                top=Side(style='thin', color='E2E8F0'),
                bottom=Side(style='thin', color='E2E8F0'),
            )

    # Set row heights
    ws.row_dimensions[1].height = 28
    for r in range(2, len(sample_rows) + 2):
        ws.row_dimensions[r].height = 22

    # Column widths
    col_widths = {1: 14, 2: 15, 3: 15, 4: 20, 5: 38, 6: 14, 7: 18}
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # Optional: Instructions sheet
    ws_notes = wb.create_sheet(title='Instructions & Valid Values')
    ws_notes.views.sheetView[0].showGridLines = True
    ws_notes.column_dimensions['A'].width = 24
    ws_notes.column_dimensions['B'].width = 50

    notes_headers = ['Field', 'Allowed Values & Guidelines']
    for col_idx, h in enumerate(notes_headers, start=1):
        cell = ws_notes.cell(row=1, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align

    instructions = [
        ('Working Days', 'Monday, Tuesday, Wednesday, Thursday, Friday (Saturday & Sunday not allowed)'),
        ('Locations', ', '.join(sample_locations)),
        ('Time Format', 'e.g. 9:00 AM, 11:30 AM, 2:00 PM, 4:30 PM (or 24h: 09:00, 11:30)'),
        ('Sub-Batch Format', 'Comma-separated codes or labels, e.g. "A1, A2, A3" or "All"'),
        ('Topic / Subject', 'Enter lab or lecture title for the slot'),
    ]
    for row_idx, (field, rule) in enumerate(instructions, start=2):
        c1 = ws_notes.cell(row=row_idx, column=1, value=field)
        c2 = ws_notes.cell(row=row_idx, column=2, value=rule)
        c1.font = Font(name='Calibri', size=10, bold=True)
        c2.font = regular_font

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def parse_schedule_excel(file_bytes_or_stream, valid_locations=None, valid_batches=None):
    """
    Parses uploaded Excel timetable and returns structured timetable data or errors.
    """
    errors = []
    warnings = []

    try:
        if isinstance(file_bytes_or_stream, bytes):
            stream = io.BytesIO(file_bytes_or_stream)
        else:
            stream = file_bytes_or_stream
        wb = openpyxl.load_workbook(stream, data_only=True)
    except Exception as e:
        return {
            'valid': False,
            'errors': [f'Could not read Excel file. Please ensure it is a valid .xlsx or .xls file. Details: {str(e)}'],
            'grid_data': None,
        }

    # Find the schedule sheet
    ws = None
    for name in wb.sheetnames:
        if 'schedule' in name.lower() or 'timetable' in name.lower():
            ws = wb[name]
            break
    if ws is None:
        ws = wb.active

    if ws.max_row < 2:
        return {
            'valid': False,
            'errors': ['The uploaded Excel sheet contains no data rows.'],
            'grid_data': None,
        }

    # Find header row (usually row 1, or within first 5 rows)
    header_map = {}
    header_row_idx = None

    for r in range(1, min(6, ws.max_row + 1)):
        row_vals = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]
        row_str_map = {}
        for c_idx, val in enumerate(row_vals, start=1):
            if not val:
                continue
            cleaned = str(val).strip().lower()
            if 'day' in cleaned:
                row_str_map['day'] = c_idx
            elif 'start' in cleaned:
                row_str_map['start_time'] = c_idx
            elif 'end' in cleaned:
                row_str_map['end_time'] = c_idx
            elif 'lab' in cleaned or 'location' in cleaned or 'room' in cleaned:
                row_str_map['location'] = c_idx
            elif 'topic' in cleaned or 'subject' in cleaned or 'course' in cleaned:
                row_str_map['topic'] = c_idx
            elif 'sub-batch' in cleaned or 'sub batch' in cleaned or 'subbatch' in cleaned:
                row_str_map['subbatch'] = c_idx
            elif 'batch' in cleaned and 'sub' not in cleaned:
                row_str_map['batch'] = c_idx

        # If day and location and topic are identified, this is the header row
        if 'day' in row_str_map and 'location' in row_str_map:
            header_map = row_str_map
            header_row_idx = r
            break

    if not header_map:
        return {
            'valid': False,
            'errors': [
                'Could not locate required column headers in Excel. Expected columns: Day, Start Time, End Time, Lab / Location, Topic / Subject, Batch, Sub-Batch.'
            ],
            'grid_data': None,
        }

    # Missing critical columns
    missing_cols = []
    if 'day' not in header_map:
        missing_cols.append('Day')
    if 'location' not in header_map:
        missing_cols.append('Lab / Location')
    if 'topic' not in header_map and 'start_time' not in header_map:
        missing_cols.append('Topic or Start Time')

    if missing_cols:
        return {
            'valid': False,
            'errors': [f'Missing required column(s): {", ".join(missing_cols)}.'],
            'grid_data': None,
        }

    # Read data rows
    days_data = {}  # { 'Monday': { [time_slot]: { [location]: { topic, subbatches } } } }
    row_count = 0

    valid_loc_lookup = {}
    if valid_locations:
        for loc in valid_locations:
            valid_loc_lookup[loc.lower()] = loc

    for r in range(header_row_idx + 1, ws.max_row + 1):
        raw_day = ws.cell(row=r, column=header_map['day']).value if 'day' in header_map else None
        if not raw_day:
            continue

        raw_day_str = str(raw_day).strip()
        day = normalize_day(raw_day_str)

        # Check for Saturday / Sunday
        if raw_day_str.lower() in ['saturday', 'sat', 'sunday', 'sun']:
            errors.append(f"Row {r}: '{raw_day_str}' is not allowed. Only Monday through Friday are working schedule days.")
            continue

        if not day or day not in ALLOWED_DAYS:
            errors.append(f"Row {r}: Invalid day '{raw_day_str}'. Must be one of Monday, Tuesday, Wednesday, Thursday, Friday.")
            continue

        # Location
        raw_loc = ws.cell(row=r, column=header_map['location']).value if 'location' in header_map else ''
        loc_str = str(raw_loc).strip() if raw_loc else ''
        if not loc_str:
            continue

        # Match location to valid locations if provided
        matched_loc = loc_str
        if valid_loc_lookup:
            matched_loc = valid_loc_lookup.get(loc_str.lower(), loc_str)

        # Start and End Time
        raw_start = ws.cell(row=r, column=header_map['start_time']).value if 'start_time' in header_map else None
        raw_end = ws.cell(row=r, column=header_map['end_time']).value if 'end_time' in header_map else None

        start_str = format_time_str(raw_start)
        end_str = format_time_str(raw_end)

        time_slot = ''
        if start_str and end_str:
            time_slot = f"{start_str} – {end_str}"
        elif start_str:
            time_slot = start_str
        else:
            time_slot = '9:00 AM – 11:00 AM'

        # Topic
        raw_topic = ws.cell(row=r, column=header_map['topic']).value if 'topic' in header_map else ''
        topic = str(raw_topic).strip() if raw_topic else ''

        # Subbatches
        raw_sub = ws.cell(row=r, column=header_map['subbatch']).value if 'subbatch' in header_map else ''
        raw_batch = ws.cell(row=r, column=header_map['batch']).value if 'batch' in header_map else ''

        subbatches = []
        if raw_sub:
            parts = re.split(r'[,;/ ]+', str(raw_sub).strip())
            for p in parts:
                cleaned = p.strip().lower()
                if cleaned:
                    subbatches.append(cleaned)
        elif raw_batch:
            # e.g. Batch A -> default to a1, a2, a3, a4
            b_str = str(raw_batch).strip().upper()
            code = b_str.replace('BATCH', '').strip()
            if code in ['A', 'B', 'C', 'D', 'E']:
                subbatches.extend([f"{code.lower()}{i}" for i in range(1, 5)])

        if day not in days_data:
            days_data[day] = {}
        if time_slot not in days_data[day]:
            days_data[day][time_slot] = {}

        existing_cell = days_data[day][time_slot].get(matched_loc, {'topic': '', 'subbatches': []})
        merged_topic = topic or existing_cell['topic']
        merged_subbatches = list(dict.fromkeys(existing_cell['subbatches'] + subbatches))

        days_data[day][time_slot][matched_loc] = {
            'topic': merged_topic,
            'subbatches': merged_subbatches,
        }
        row_count += 1

    if not days_data and not errors:
        return {
            'valid': False,
            'errors': ['No timetable entries could be extracted from the file.'],
            'grid_data': None,
        }

    if errors and not days_data:
        return {
            'valid': False,
            'errors': errors,
            'grid_data': None,
        }

    # Selected primary day (first day with data or Monday)
    primary_day = 'Monday' if 'Monday' in days_data else list(days_data.keys())[0]

    return {
        'valid': True,
        'errors': errors,  # Non-fatal warnings if days_data is present
        'days_data': days_data,
        'selected_day': primary_day,
        'grid': days_data.get(primary_day, {}),
        'total_rows_parsed': row_count,
        'days_found': list(days_data.keys()),
    }
