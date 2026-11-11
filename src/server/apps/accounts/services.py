"""
Accounts Service Layer
Business logic for User creation, password management, and bulk Excel import with TCS Ignite hierarchy.
"""
import re
import openpyxl
from django.contrib.auth.hashers import make_password
from .models import User, Cohort, Batch, SubBatch


def create_user(validated_data):
    """Creates a user account and hashes the password."""
    password = validated_data.pop("password")
    if validated_data.get("employee_id") is None:
        validated_data["employee_id"] = ""
    if validated_data.get("accops_id") is None:
        validated_data["accops_id"] = ""
    user = User(**validated_data)
    user.set_password(password)
    # Admin-created trainees must change password upon first login
    if user.role == "TRAINEE" or not user.is_staff:
        user.must_change_password = True
    else:
        user.must_change_password = False
    user.save()
    return user


def change_password(user, new_password):
    """Updates an authenticated user's password."""
    user.set_password(new_password)
    user.must_change_password = False
    user.save()
    return user


def reset_password(user, new_password):
    """Resets another user's password."""
    user.set_password(new_password)
    user.must_change_password = True
    user.save()
    return user


def activate_user(user):
    user.is_active = True
    user.save()
    return user


def deactivate_user(user):
    user.is_active = False
    user.save()
    return user


_sub_batch_cache = {}


def resolve_or_create_sub_batch(raw_batch_str: str, cohort_hint: str = "", batch_hint: str = ""):
    """
    Resolves or creates a SubBatch from inputs such as:
      - raw_batch_str="B50-A1" -> Cohort=B50, Batch=A, SubBatch=A1
      - raw_batch_str="A1", cohort_hint="B50", batch_hint="A"
    """
    if not raw_batch_str and not sub_batch_name_clean(raw_batch_str):
        return None

    raw_str = str(raw_batch_str).strip().upper()
    cache_key = f"{raw_str}:{cohort_hint}:{batch_hint}".upper()
    if cache_key in _sub_batch_cache:
        return _sub_batch_cache[cache_key]

    cohort_code = str(cohort_hint).strip().upper() if cohort_hint else "B50"
    batch_name = str(batch_hint).strip().upper() if batch_hint else "A"
    sub_batch_name = raw_str

    # Parse compound formats like "B50-A1", "B50-A-1", "B50-A-A1"
    match = re.match(r"^(B\d+)[-_/ ]?([A-Z])[-_/ ]?([A-Z0-9]+)$", raw_str)
    if match:
        cohort_code, batch_name, sub_batch_name = match.groups()
    else:
        # Check if format is "B50-A1" where sub-batch is A1 and batch is A
        match2 = re.match(r"^(B\d+)[-_/ ]?(([A-Z])\d+)$", raw_str)
        if match2:
            cohort_code, sub_batch_name, batch_name = match2.group(1), match2.group(2), match2.group(3)
        else:
            # Check format like "A1"
            match3 = re.match(r"^([A-Z])(\d+)$", raw_str)
            if match3:
                batch_name = match3.group(1)
                sub_batch_name = raw_str

    try:
        cohort_obj, _ = Cohort.objects.get_or_create(code=cohort_code, defaults={"name": f"Ignite Cohort {cohort_code}"})
        batch_obj, _ = Batch.objects.get_or_create(cohort=cohort_obj, name=batch_name)
        sub_batch_obj, _ = SubBatch.objects.get_or_create(batch=batch_obj, name=sub_batch_name)
        _sub_batch_cache[cache_key] = sub_batch_obj
        return sub_batch_obj
    except Exception:
        return None


def sub_batch_name_clean(val):
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in ("nan", "none", "null", "") else s


def bulk_create_users(excel_file):
    """
    Bulk User Creation Service with TCS Ignite Cohort/Batch hierarchy resolution.
    Accepts .xlsx files up to 600 users per upload.
    Validates that:
      - Employee ID is an integer of exactly 7 digits (e.g. 1234567) and unique.
      - Email is unique.
      - Username allows spaces and duplicate values.
    """
    MAX_BULK_LIMIT = 600

    try:
        wb = openpyxl.load_workbook(excel_file, data_only=True)
        ws = wb.active
        all_rows = list(ws.iter_rows(values_only=True))
    except Exception as exc:
        return {"created_count": 0, "failed_count": 0, "errors": [f"Failed to read Excel workbook: {exc}"]}

    if not all_rows:
        return {"created_count": 0, "failed_count": 0, "errors": ["Excel workbook contains no data rows."]}

    # Filter non-empty data rows
    data_rows = [
        (idx, r) for idx, r in enumerate(all_rows[1:], start=2)
        if any(v is not None and str(v).strip() != "" for v in r)
    ]

    if not data_rows:
        return {"created_count": 0, "failed_count": 0, "errors": ["Excel workbook contains no user rows."]}

    if len(data_rows) > MAX_BULK_LIMIT:
        return {
            "created_count": 0,
            "failed_count": 0,
            "errors": [f"File contains {len(data_rows)} rows. The maximum bulk upload limit is {MAX_BULK_LIMIT} users per file."],
        }

    headers = [str(cell).strip().lower() if cell is not None else f"col_{idx}" for idx, cell in enumerate(all_rows[0])]
    valid_roles = {"TRAINEE", "TA", "HR", "MANAGER", "ADMIN"}

    existing_emails = set(User.objects.values_list("email", flat=True))
    existing_employee_ids = set(User.objects.exclude(employee_id__isnull=True).exclude(employee_id="").values_list("employee_id", flat=True))

    seen_emails = set()
    seen_employee_ids = set()

    users_to_create = []
    errors = []
    created_count = 0
    failed_count = 0

    DEFAULT_PASSWORD_HASH = make_password("Temp@123")

    for row_num, row_vals in data_rows:
        try:
            row_dict = {
                headers[i]: row_vals[i]
                for i in range(min(len(headers), len(row_vals)))
            }

            raw_username = row_dict.get("username") or row_dict.get("name") or row_dict.get("full_name") or row_dict.get("employee_id")
            if raw_username is None or str(raw_username).strip() == "":
                failed_count += 1
                errors.append(f"Row {row_num}: Missing username")
                continue

            # Username allows spaces and is not required to be unique
            username = str(raw_username).strip()
            if isinstance(raw_username, float) and raw_username.is_integer():
                username = str(int(raw_username))

            raw_email = row_dict.get("email")
            email = str(raw_email).strip().lower() if raw_email else ""
            role = str(row_dict.get("role", "TRAINEE")).strip().upper()

            if not email or "@" not in email:
                failed_count += 1
                errors.append(f"Row {row_num}: Invalid or missing email")
                continue

            if role not in valid_roles:
                failed_count += 1
                errors.append(f"Row {row_num}: Invalid role '{role}'")
                continue

            if email in existing_emails or email in seen_emails:
                failed_count += 1
                errors.append(f"Row {row_num}: Email '{email}' already exists")
                continue

            # Validate Employee ID: integer, exactly 7 digits (e.g. 2109845)
            raw_emp = row_dict.get("employee_id") or (row_dict.get("username") if str(row_dict.get("username", "")).isdigit() else None)
            employee_id = None
            if raw_emp is not None and str(raw_emp).strip() != "" and str(raw_emp).lower() not in ("nan", "none", "null"):
                if isinstance(raw_emp, (int, float)):
                    emp_str = str(int(raw_emp))
                else:
                    emp_str = str(raw_emp).strip()

                if not re.match(r"^\d{7}$", emp_str):
                    failed_count += 1
                    errors.append(f"Row {row_num}: Employee ID '{emp_str}' must be a 7-digit integer (e.g. 1234567)")
                    continue

                if emp_str in existing_employee_ids or emp_str in seen_employee_ids:
                    failed_count += 1
                    errors.append(f"Row {row_num}: Employee ID '{emp_str}' already exists")
                    continue

                employee_id = emp_str

            if role == "TRAINEE" and not employee_id:
                failed_count += 1
                errors.append(f"Row {row_num}: 7-digit Employee ID is required for trainees")
                continue

            # Resolve SubBatch hierarchy if present
            raw_batch = sub_batch_name_clean(row_dict.get("sub_batch") or row_dict.get("batch") or row_dict.get("section"))
            cohort_hint = sub_batch_name_clean(row_dict.get("cohort"))
            batch_hint = sub_batch_name_clean(row_dict.get("batch_name"))

            sub_batch_obj = resolve_or_create_sub_batch(raw_batch, cohort_hint, batch_hint) if raw_batch else None
            accops_id = str(row_dict.get("accops_id", "")).strip()

            users_to_create.append(
                User(
                    username=username,
                    email=email,
                    role=role,
                    password=DEFAULT_PASSWORD_HASH,
                    sub_batch=sub_batch_obj,
                    employee_id=employee_id,
                    accops_id=accops_id,
                    must_change_password=True,
                )
            )

            seen_emails.add(email)
            if employee_id:
                seen_employee_ids.add(employee_id)
            created_count += 1

        except Exception as e:
            failed_count += 1
            errors.append(f"Row {row_num}: {str(e)}")

    if users_to_create:
        User.objects.bulk_create(users_to_create)

    return {
        "created_count": created_count,
        "failed_count": failed_count,
        "errors": errors[:30],
    }
