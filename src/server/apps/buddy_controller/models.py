"""
Buddy Controller & Exam Mode Models
Integrates with TCS Ignite Cohort/Batch hierarchy and manages exam mode locks.
"""
from django.db import models
from server.apps.accounts.models import User, Cohort, Batch, Lab, SubBatch

# Re-export for backward compatibility
__all__ = ["Cohort", "Batch", "Lab", "SubBatch", "SystemSetting", "ExamControl"]


class SystemSetting(models.Model):
    """
    Persistent key-value configuration storage.
    Used for global settings like 'buddy_enabled', 'exam_mode_reason', etc.
    """
    key = models.CharField(max_length=100, primary_key=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.key}={self.value}"

    @classmethod
    def get_bool(cls, key: str, default: bool = True) -> bool:
        try:
            row = cls.objects.filter(key=key).first()
            if not row:
                return default
            return row.value.strip().lower() in ("true", "1", "yes", "on")
        except Exception:
            return default

    @classmethod
    def set_bool(cls, key: str, val: bool, description: str = "", user=None):
        try:
            cls.objects.update_or_create(
                key=key,
                defaults={
                    "value": "true" if val else "false",
                    "description": description or f"System setting {key}",
                    "updated_by": user if user and user.is_authenticated else None,
                },
            )
        except Exception:
            pass

    @classmethod
    def get_str(cls, key: str, default: str = "") -> str:
        try:
            row = cls.objects.filter(key=key).first()
            return row.value if row else default
        except Exception:
            return default

    @classmethod
    def set_str(cls, key: str, val: str, description: str = "", user=None):
        try:
            cls.objects.update_or_create(
                key=key,
                defaults={
                    "value": str(val),
                    "description": description or f"System setting {key}",
                    "updated_by": user if user and user.is_authenticated else None,
                },
            )
        except Exception:
            pass

    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        try:
            row = cls.objects.filter(key=key).first()
            return int(row.value) if row else default
        except Exception:
            return default

    @classmethod
    def set_int(cls, key: str, val: int, description: str = "", user=None):
        cls.set_str(key, str(val), description=description, user=user)

    @classmethod
    def get_float(cls, key: str, default: float = 0.0) -> float:
        try:
            row = cls.objects.filter(key=key).first()
            return float(row.value) if row else default
        except Exception:
            return default

    @classmethod
    def set_float(cls, key: str, val: float, description: str = "", user=None):
        cls.set_str(key, str(val), description=description, user=user)


class ExamControl(models.Model):
    """
    Controls Trainee Buddy assistant availability during examinations (PRA / lab evaluations).
    Can lock down by individual user/device, by Lab, or by Sub-Batch.
    """
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE, related_name="exam_controls"
    )
    trainee_name = models.CharField(max_length=100, blank=True)
    device_id = models.CharField(max_length=100, unique=True)
    sub_batch = models.ForeignKey(SubBatch, null=True, blank=True, on_delete=models.SET_NULL)
    batch = models.ForeignKey(Batch, null=True, blank=True, on_delete=models.SET_NULL)
    lab = models.ForeignKey(Lab, null=True, blank=True, on_delete=models.SET_NULL)
    exam_mode = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.user and not self.trainee_name:
            self.trainee_name = self.user.username
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.trainee_name or self.device_id} (Exam: {self.exam_mode})"
