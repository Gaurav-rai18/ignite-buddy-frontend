# Broadcast Notification System (`src/server/apps/notifications`)

The Broadcast Notification System enables instructors and administrators to dispatch targeted announcements across the TCS Ignite campus hierarchy with real-time WebSocket delivery and audit logging.

---

## 1. Architecture & Targeting Modes

The system supports granular targeting across the TCS Ignite 3-tier structure:

| Target Mode (`recipient_type`) | Description | Target Field |
| :--- | :--- | :--- |
| `ALL` | Campus-wide announcement to all active users | None |
| `COHORT` | All trainees enrolled in an intake cohort (e.g., `B50` ~300+ trainees) | `target_cohort` (`Cohort` foreign key) |
| `BATCH` | Trainees in a specific technology or lecture track (e.g., `B50-A`) | `target_batch` (`Batch` foreign key) |
| `SUB_BATCH` | Trainees in a specific lab practical section (e.g., `B50-A1`) | `target_sub_batch` (`SubBatch` foreign key) |
| `ROLE` | Targeted by role (`ADMIN`, `TA`, `HR`, `MANAGER`, `TRAINEE`) | `target_role` |
| `USER` | Direct message to a single trainee or instructor | `target_username` or `target_users` list |

---

## 2. Database Models

The notification system uses a normalized relationship without string duplication:

### `Notification`
Stores the canonical announcement and dispatch criteria:
- `id`: Auto primary key
- `title`: Short headline string
- `message`: Full announcement body text
- `recipient_type`: `ALL`, `COHORT`, `BATCH`, `SUB_BATCH`, `ROLE`, or `USER`
- `target_cohort`, `target_batch`, `target_sub_batch`: Foreign keys to accounts hierarchy
- `target_role`: Role filter string
- `target_username`: Optional specific user target
- `created_by`: Foreign key to `User` (staff sender)
- `created_at`: Timestamp of creation

### `NotificationRecipient`
Normalised recipient delivery tracking (replaces redundant duplicate notification rows):
- `notification`: Foreign key to `Notification` (with `related_name="recipients"`)
- `user`: Foreign key to `User`
- `is_read`: Boolean flag (default `False`)
- `read_at`: Timestamp when the user read the notification
- **Indexes**: Compound index on `[user, is_read]` for high-performance inbox queries

---

## 3. Real-Time Delivery Flow

```
Admin submits announcement via Admin Console (or API)
                      │
                      ▼
   POST /api/notifications/broadcast/
                      │
                      ▼
   Validate target audience (Cohort / Batch / SubBatch / Role / User)
                      │
                      ▼
   Save canonical Notification record
                      │
                      ▼
   Bulk insert NotificationRecipient rows for all targeted users
                      │
                      ▼
   Broadcast live push event across Channels WebSocket group (toast alert)
                      │
                      ▼
   Connected trainee desktop assistants display live notification toast
```

---

## 4. API Endpoints

### Create Broadcast Announcement

**Bash (cURL):**
```bash
curl -X POST http://127.0.0.1:8765/api/notifications/broadcast/ \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Lab 2 Schedule Adjustment",
    "message": "Sub-batch A1 will report to Lab 3 for afternoon practicals.",
    "recipient_type": "SUB_BATCH",
    "target_sub_batch": 1
  }'
```

**Windows CMD (cURL):**
```cmd
curl -X POST http://127.0.0.1:8765/api/notifications/broadcast/ ^
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"title\":\"Lab 2 Schedule Adjustment\",\"message\":\"Sub-batch A1 will report to Lab 3 for afternoon practicals.\",\"recipient_type\":\"SUB_BATCH\",\"target_sub_batch\":1}"
```

### View Broadcast History

**Bash / CMD:**
```bash
curl -X GET http://127.0.0.1:8765/api/notifications/broadcast/history/ \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>"
```

### Fetch User Inbox Notifications

**Bash / CMD:**
```bash
curl -X GET http://127.0.0.1:8765/api/notifications/user-notifications/ \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>"
```

---

## 5. Testing

Run the notifications test suite using `pytest`:

**Bash / CMD:**
```bash
pytest tests/ -k notification
```
