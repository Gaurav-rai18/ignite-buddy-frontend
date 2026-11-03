# Schedule Feature Documentation

## Overview
The **Schedule** feature in the Campus Admin Panel provides administrators with a full‑featured UI to create, preview, and delete schedules. It supports two schedule types:
1. **Native Timetable Grid** – a custom grid built with day pills, batch selectors (A/B/C), sub‑batch chips and slot counters.
2. **OneDrive Sharing Link** – a simple external link to a shared OneDrive document.

The implementation touches both the **frontend (React/Vite)** and the **backend (Django REST Framework)**.

---

## Table of Contents
1. [Frontend Files](#frontend-files)
2. [Backend Files](#backend-files)
3. [Data Flow & Sequence](#data-flow--sequence)
4. [Database Schema](#database-schema)
5. [How to Use the Feature](#how-to-use-the-feature)
6. [Testing](#testing)
7. [Future Enhancements](#future-enhancements)

---

## Frontend Files
| Path | Purpose |
|------|---------|
| `src/pages/Schedule/Schedule.jsx` | Main page – header stats, tab toggle, renders form, list, and modals. |
| `src/components/schedule/ScheduleForm.jsx` | Form for creating a schedule. Handles type toggle, date shortcuts, validation, and submission. |
| `src/components/schedule/ScheduleGridBuilder.jsx` | Native grid builder UI – day pills, batch selector, sub‑batch chips, slot counter, clear‑day action, scroll handling. |
| `src/components/schedule/SchedulePreviewModal.jsx` | Modal that previews the current grid or the OneDrive link before publishing. |
| `src/components/schedule/DeleteScheduleDialog.jsx` | Confirmation dialog shown when a user clicks the delete (trash) icon. |
| `src/components/schedule/ScheduleList.jsx` | Lists existing schedules with preview & delete actions. |
| `src/services/scheduleService.js` | API wrapper – `createSchedule`, `fetchSchedules`, `deleteSchedule`. |
| `src/hooks/useSchedules.js` | Custom hook that fetches schedules and provides `create`, `delete`, and `refresh` callbacks to components. |
| `src/utils/validation.js` | Added whitelist validation for the `audience` field (`VALID_AUDIENCES`). |
| `src/constants/index.js` | Exported `VALID_AUDIENCES` constant used by validation and UI. |
| `src/styles.css` | Schedule‑specific CSS (header stats, tab toggle, grid builder layout, responsive breakpoints, overflow handling). |
| `src/test/components.test.jsx` | Updated component tests to cover the new UI (preview modal, delete dialog). |
| `src/test/validation.test.js` | Tests for the audience whitelist validation. |
| `src/test/authAndError.test.js` | Tests for `authService` login fallback (unchanged but still passes). |

---

## Backend Files (Django)
| Path | Purpose |
|------|---------|
| `backend/schedule/models.py` | `Schedule` model – fields: `title`, `message`, `audience`, `type` (`grid`/`link`), `grid_data` (JSON), `link_url`, `start_date`, `end_date`, `created_at`, `updated_at`. |
| `backend/schedule/serializers.py` | `ScheduleSerializer` – validates required fields, enforces audience whitelist (`VALID_AUDIENCES`). |
| `backend/schedule/views.py` | `ScheduleViewSet` – provides `list`, `create`, `retrieve`, `update`, `destroy` endpoints. |
| `backend/schedule/urls.py` | Router registration (`/api/schedules/`). |
| `backend/settings.py` (part) | Added `VALID_AUDIENCES` to settings for shared validation. |

The backend already exposed a `DELETE /api/schedules/<id>/` endpoint, which the new frontend wrapper consumes.

---

## Data Flow & Sequence
```mermaid
graph TD
    A[User clicks "Create Schedule"] --> B[ScheduleForm UI]
    B --> C{Schedule Type?}
    C -->|Grid| D[ScheduleGridBuilder]
    C -->|Link| E[Enter OneDrive URL]
    D --> F[User fills grid]
    E --> F[User enters link]
    F --> G[Click "Preview"]
    G --> H[SchedulePreviewModal shows data]
    H --> I[User confirms]
    I --> J[scheduleService.createSchedule]
    J --> K[POST /api/schedules/]
    K --> L[Backend creates Schedule record]
    L --> M[Response with new schedule ID]
    M --> N[useSchedules.refresh -> fetch list]
    N --> O[ScheduleList re‑renders]
    O --> P[User clicks trash icon]
    P --> Q[DeleteScheduleDialog opens]
    Q --> R[User confirms delete]
    R --> S[scheduleService.deleteSchedule]
    S --> T[DELETE /api/schedules/<id>/]
    T --> U[Backend deletes record]
    U --> V[useSchedules.refresh -> fetch list]
    V --> W[ScheduleList updates]
```

### Step‑by‑Step Description
1. **Form Interaction** – `ScheduleForm` renders the type toggle and date shortcuts. Selecting *Native Timetable Grid* displays `ScheduleGridBuilder`; selecting *OneDrive Link* shows a simple text field.
2. **Building the Grid** – Users add days, select batch presets (A/B/C) and optionally choose sub‑batch chips. The component keeps a local `gridData` state.
3. **Preview** – Clicking *Preview* opens `SchedulePreviewModal`. It renders a read‑only copy of the grid (or the link) so the user can verify before publishing.
4. **Create** – On confirmation, `scheduleService.createSchedule` sends a `POST` request with the payload. The backend validates the audience against `VALID_AUDIENCES` and stores the JSON grid (or link).
5. **List & Delete** – `useSchedules` fetches all schedules and supplies a `deleteSchedule` callback. The list shows a *preview* icon and a *trash* icon. Deleting triggers `DeleteScheduleDialog`; on confirm the service calls the backend `DELETE` endpoint and refreshes the list.

---

## Database Schema
```sql
CREATE TABLE schedule_schedule (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    audience VARCHAR(50) NOT NULL,                -- must be in VALID_AUDIENCES
    type VARCHAR(10) NOT NULL CHECK (type IN ('grid','link')),
    grid_data JSONB,                               -- null if type='link'
    link_url VARCHAR(500),                         -- null if type='grid'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```
*The Django model mirrors the table above. The `grid_data` JSON stores an array of day objects, each containing batch‑A/B/C arrays of sub‑batch IDs and slot counts.*

---

## How to Use the Feature
1. Navigate to **/schedule** in the admin UI.
2. Toggle between **Native Timetable Grid** and **OneDrive Sharing Link**.
3. For the grid:
   - Click a day pill to edit that day.
   - Choose a batch preset (A/B/C) or toggle sub‑batch chips.
   - The slot counter updates automatically.
   - Use the **Clear Day** button to reset a day.
4. Click **Preview** to open the modal and verify the layout.
5. Press **Publish** to save the schedule.
6. Existing schedules appear in the list; use the eye icon to preview again or the trash icon to delete.

---

## Testing
- **Unit tests** (`npm test`) cover:
  - Validation whitelist (`validation.test.js`).
  - Auth service login fallback.
  - Component rendering and interaction (`components.test.jsx`).
- All **34 tests pass**.
- UI can be manually tested by running `npm run dev` and interacting at `http://localhost:5173/schedule`.

---

## Future Enhancements
- Add optimistic UI updates for create/delete actions.
- Persist the active tab in the URL query string.
- Write dedicated Vitest tests for `ScheduleGridBuilder` interactions (drag‑drop, sub‑batch selection).
- Introduce pagination / infinite scroll for large schedule lists.
- Export / import schedule JSON for backup.

---

*Documentation generated by Antigravity on 2026‑11‑04.*
