from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
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
    title = models.CharField(max_length=160)
    message = models.TextField()
    audience = models.CharField(max_length=40, default='All students')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.title

class ScheduledLink(models.Model):
    title = models.CharField(max_length=160)
    onedrive_url = models.URLField(max_length=1000, blank=True, null=True)
    content_data = models.TextField(blank=True, null=True)  # Stores JSON schedule data
    schedule_type = models.CharField(max_length=20, default='grid')  # 'grid', 'excel', 'link'
    excel_file = models.FileField(upload_to='schedules/excels/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.IntegerField(blank=True, null=True)
    publish_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['publish_at']
    def __str__(self):
        return self.title

class ScheduleLocation(models.Model):
    name = models.CharField(max_length=100, unique=True)
    badge = models.CharField(max_length=100, blank=True, default='')
    color = models.CharField(max_length=30, blank=True, default='#014BAA')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

class ScheduleBatch(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., "Batch A"
    code = models.CharField(max_length=10, unique=True)  # e.g., "A"
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

class ScheduleSubBatch(models.Model):
    batch = models.ForeignKey(ScheduleBatch, related_name='subbatches', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)  # e.g., "A1"
    code = models.CharField(max_length=20)  # e.g., "a1"
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        unique_together = ('batch', 'code')

    def __str__(self):
        return f"{self.batch.code} - {self.name}"

class ScheduleTimeSlot(models.Model):
    start_time = models.CharField(max_length=20)  # e.g. "09:00 AM"
    end_time = models.CharField(max_length=20)    # e.g. "11:00 AM"
    label = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.label or f"{self.start_time} – {self.end_time}"

class ScheduleWeekDay(models.Model):
    name = models.CharField(max_length=20, unique=True)  # e.g. "Monday"
    code = models.CharField(max_length=10, unique=True)  # e.g. "mon"
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

class SiteSetting(models.Model):
    key = models.CharField(max_length=80, unique=True)
    value = models.CharField(max_length=200, default='false')
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'{self.key}: {self.value}'
