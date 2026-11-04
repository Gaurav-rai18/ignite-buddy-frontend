"""
Models for the Ignite Buddy campus administration system.

This module defines the database schema for:
- User management (custom User extending Django's AbstractUser)
- Broadcast messaging to students
- Schedule publishing (links, Excel files, grid-based timetables)
- Dynamic schedule configuration (locations, batches, sub-batches, time slots, weekdays)
- Global site settings (feature flags like buddy_enabled)

The schedule configuration models (ScheduleLocation, ScheduleBatch, ScheduleSubBatch,
ScheduleTimeSlot, ScheduleWeekDay) work together to define the structure of a timetable
grid. Admins can dynamically add/remove these entities, and the frontend schedule builder
reads them via the /api/schedule-config/ endpoint.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Adds campus-specific fields: batch (cohort number like '50', '51')
    and subbatch (lab group like 'a1', 'b3'). These are used for
    targeting broadcasts and assigning students to schedule slots.

    Fields:
        batch:    The student's cohort/intake number (e.g., '51').
        subbatch: The student's lab sub-group (e.g., 'a1', 'b2').
        status:   'Active' or 'Inactive' — controls account visibility.
    """
    BATCH_CHOICES = [
        ('51', 'Batch 51'),
        ('50', 'Batch 50'),
        ('49', 'Batch 49'),
        ('46', 'Batch 46'),
        ('47', 'Batch 47'),
    ]
    SUBBATCH_CHOICES = [
        ('a1', 'A1'), ('a2', 'A2'), ('a3', 'A3'), ('a4', 'A4'),
        ('b1', 'B1'), ('b2', 'B2'), ('b3', 'B3'), ('b4', 'B4'),
        ('c1', 'C1'), ('c2', 'C2'), ('c3', 'C3'), ('c4', 'C4'),
    ]
    
    batch = models.CharField(max_length=2, choices=BATCH_CHOICES, blank=True, null=True)
    subbatch = models.CharField(max_length=2, choices=SUBBATCH_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=10, default='Active')

    def __str__(self):
        return self.username


class Broadcast(models.Model):
    """
    A campus-wide announcement message.

    Created by admins and targeted to a specific audience group.
    Ordered by newest first (created_at descending).

    Fields:
        title:      Short headline (max 160 chars, enforced by frontend too).
        message:    Full announcement body text.
        audience:   Target group (e.g., 'All students', 'All faculty').
        created_at: Auto-set on creation, used for ordering.
    """
    title = models.CharField(max_length=160)
    message = models.TextField()
    audience = models.CharField(max_length=40, default='All students')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.title


class ScheduledLink(models.Model):
    """
    A published schedule item — the core record for all schedule types.

    Supports three schedule_type values:
        'grid'  — Native timetable built in the interactive grid UI.
        'excel' — Timetable uploaded as an Excel spreadsheet.
        'link'  — Legacy OneDrive sharing link.

    IMPORTANT: The actual timetable data (which topics/batches go in which
    time slots at which locations) is stored as a JSON *string* in the
    content_data TextField — NOT as separate relational rows. The JSON
    structure is: { day: "Monday", grid: { [timeSlot]: { [location]: { topic, subbatches[] } } } }

    For Excel uploads, content_data also includes a 'days_data' key with
    data for multiple days, and the original file is saved to excel_file.

    Fields:
        title:         Admin-supplied name for this schedule.
        onedrive_url:  Legacy URL field (blank for grid/excel types).
        content_data:  JSON string of the timetable grid data.
        schedule_type: Discriminator: 'grid', 'excel', or 'link'.
        excel_file:    The uploaded .xlsx/.xls file (null for grid/link).
        file_name:     Original filename of the uploaded Excel.
        file_size:     File size in bytes.
        publish_at:    When this schedule should become visible to students.
        created_at:    Auto-set record creation timestamp.
    """
    title = models.CharField(max_length=160)
    onedrive_url = models.URLField(max_length=1000, blank=True, null=True)
    content_data = models.TextField(blank=True, null=True)  # JSON string of timetable data
    schedule_type = models.CharField(max_length=20, default='grid')  # 'grid' | 'excel' | 'link'
    excel_file = models.FileField(upload_to='schedules/excels/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.IntegerField(blank=True, null=True)
    publish_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['publish_at']  # Soonest-to-publish first
    def __str__(self):
        return self.title


class ScheduleLocation(models.Model):
    """
    A physical lab or room that appears as a column in the timetable grid.

    Seeded by migration 0004 with 7 default locations:
    Lab 1 (Hardware), Lab 2 (Software), Lab 3 (Data & AI), Lab 4 (Cloud Ops),
    Work Area, TR1, TR2. The legacy 'Incubator' column has been removed.

    Fields:
        name:  Unique location name displayed in grid column headers.
        badge: Short descriptor shown under the name (e.g., 'Hardware').
        color: Hex color code for UI theming of this column.
        order: Sort order for column arrangement (1-based).
    """
    name = models.CharField(max_length=100, unique=True)
    badge = models.CharField(max_length=100, blank=True, default='')
    color = models.CharField(max_length=30, blank=True, default='#014BAA')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class ScheduleBatch(models.Model):
    """
    A batch group (e.g., Batch A, Batch B) that contains multiple sub-batches.

    Admins can dynamically create new batches at runtime. When a batch is
    created via the API, 4 sub-batches are auto-generated by default.
    Deleting a batch CASCADE-deletes all its sub-batches.

    Fields:
        name:  Display name (e.g., 'Batch A'). Must be unique.
        code:  Short identifier (e.g., 'A'). Used to generate sub-batch codes.
        order: Sort order for display in the UI.
    """
    name = models.CharField(max_length=50, unique=True)  # e.g., "Batch A"
    code = models.CharField(max_length=10, unique=True)  # e.g., "A"
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class ScheduleSubBatch(models.Model):
    """
    An individual sub-batch within a batch group (e.g., A1, A2, B3).

    Sub-batches are the smallest assignable unit in the timetable grid.
    Each grid cell can have multiple sub-batches toggled on. Sub-batch
    codes are stored lowercase in the grid JSON (e.g., 'a1', 'b3').

    The (batch, code) pair is unique — prevents duplicate sub-batches
    within the same parent batch.

    Fields:
        batch: FK to parent ScheduleBatch (CASCADE on delete).
        name:  Display label (e.g., 'A1'). Shown on chip buttons.
        code:  Lowercase identifier (e.g., 'a1'). Stored in grid JSON.
        order: Sort order within the parent batch.
    """
    batch = models.ForeignKey(ScheduleBatch, related_name='subbatches', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)  # e.g., "A1"
    code = models.CharField(max_length=20)  # e.g., "a1"
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        unique_together = ('batch', 'code')  # No duplicate codes per batch

    def __str__(self):
        return f"{self.batch.code} - {self.name}"


class ScheduleTimeSlot(models.Model):
    """
    A time period row in the timetable grid (e.g., 9:00 AM – 11:00 AM).

    Times are stored as display strings (not Django TimeField) because the
    frontend renders them directly. The 'label' field is the key used in
    the grid JSON structure (e.g., content_data.grid["9:00 AM – 11:00 AM"]).

    Admins can dynamically add/edit/delete time slots. The frontend validates
    against overlapping time ranges before submitting.

    Fields:
        start_time: Display string (e.g., '9:00 AM').
        end_time:   Display string (e.g., '11:00 AM').
        label:      Combined label used as the grid row key. Auto-generated
                    as '{start_time} – {end_time}' if not provided.
        order:      Sort order (chronological arrangement).
    """
    start_time = models.CharField(max_length=20)  # e.g. "09:00 AM"
    end_time = models.CharField(max_length=20)    # e.g. "11:00 AM"
    label = models.CharField(max_length=50, blank=True)  # Grid row key
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.label or f"{self.start_time} – {self.end_time}"


class ScheduleWeekDay(models.Model):
    """
    A working day in the timetable (Monday through Friday only).

    Saturday and Sunday are explicitly rejected by the API (ScheduleWeekDayViewSet).
    Seeded by migration 0004 with Mon-Fri.

    Fields:
        name:  Full day name (e.g., 'Monday'). Used as display and grid key.
        code:  Abbreviated code (e.g., 'mon'). Used for compact references.
        order: Sort order (1=Monday through 5=Friday).
    """
    name = models.CharField(max_length=20, unique=True)  # e.g. "Monday"
    code = models.CharField(max_length=10, unique=True)  # e.g. "mon"
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name


class SiteSetting(models.Model):
    """
    Key-value store for global site settings (e.g., feature flags).

    Currently used for:
        'buddy_enabled' — Controls whether the Buddy AI assistant is
        available to students. Toggled via the /api/settings/buddy/ endpoint.

    Fields:
        key:        Setting identifier (e.g., 'buddy_enabled').
        value:      String value ('true' or 'false' for booleans).
        updated_at: Auto-updated timestamp on every save.
    """
    key = models.CharField(max_length=80, unique=True)
    value = models.CharField(max_length=200, default='false')
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'{self.key}: {self.value}'
