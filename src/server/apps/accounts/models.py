"""
Accounts & TCS Ignite Hierarchy Models

Hierarchy:
    Cohort (e.g. B49, B50)
      └── Batch (e.g. A, B, C)
            └── SubBatch (e.g. A1, A2, B1, B2)
                  └── User (Trainee)
                  └── Lab (Physical Training Lab)
"""
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import RegexValidator
from django.db import models


class CustomUserManager(UserManager):
    """
    Manager that ensures superusers and staff are automatically assigned
    the ADMIN role instead of defaulting to TRAINEE.
    """
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", "ADMIN")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("must_change_password", False)
        return super().create_superuser(username, email, password, **extra_fields)

    def create_user(self, username, email=None, password=None, **extra_fields):
        if extra_fields.get("is_superuser") or extra_fields.get("is_staff"):
            extra_fields.setdefault("role", "ADMIN")
        return super().create_user(username, email, password, **extra_fields)


class Cohort(models.Model):
    """
    TCS Ignite Program Cohort (e.g. B49, B50, B51).
    Top-level intake grouping representing 300-500 trainees.
    """
    code = models.CharField(max_length=20, unique=True)  # e.g. "B50"
    name = models.CharField(max_length=100, blank=True)  # e.g. "Ignite Batch 50"
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-code"]

    def __str__(self):
        return self.code


class Batch(models.Model):
    """
    Major Track / Section within a Cohort (e.g. A, B, C).
    """
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="batches")
    name = models.CharField(max_length=20)  # e.g. "A", "B", "C"
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("cohort", "name")
        ordering = ["cohort__code", "name"]
        verbose_name_plural = "Batches"

    @property
    def full_code(self):
        return f"{self.cohort.code}-{self.name}"

    def __str__(self):
        return self.full_code


class Lab(models.Model):
    """
    Physical Computer Lab / Assessment Room in the Ignite facility.
    """
    name = models.CharField(max_length=100, unique=True)  # e.g. "Lab 1", "Lab 2"
    capacity = models.IntegerField(default=35)
    location = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SubBatch(models.Model):
    """
    Hands-on Practical / Lab Group of 20-30 trainees (e.g. A1, A2, B1, B2).
    """
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="sub_batches")
    name = models.CharField(max_length=20)  # e.g. "A1", "A2", "B1"
    lab = models.ForeignKey(Lab, null=True, blank=True, on_delete=models.SET_NULL, related_name="sub_batches")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("batch", "name")
        ordering = ["batch__cohort__code", "name"]
        verbose_name_plural = "Sub Batches"

    @property
    def full_code(self):
        return f"{self.batch.cohort.code}-{self.name}"

    def __str__(self):
        return self.full_code


class User(AbstractUser):
    """
    Custom User Model for Ignite Buddy.
    Supports Role-Based Access Control and TCS Ignite Cohort/Batch hierarchy.
    """
    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("TRAINEE", "Trainee"),
        ("TA", "TA"),
        ("HR", "HR"),
        ("MANAGER", "Manager"),
    )

    username = models.CharField(
        max_length=150,
        unique=False,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[\w\s.@+-]+$",
                message="Enter a valid username. Letters, digits, spaces, and @/./+/-/_ characters are allowed.",
            )
        ],
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="TRAINEE")

    # Trainees belong directly to a Sub-Batch (e.g. B50-A1)
    sub_batch = models.ForeignKey(
        SubBatch, null=True, blank=True, on_delete=models.SET_NULL, related_name="trainees"
    )

    # Instructors / TAs / HR can oversee an entire Cohort or Batch
    assigned_cohort = models.ForeignKey(
        Cohort, null=True, blank=True, on_delete=models.SET_NULL, related_name="staff"
    )
    assigned_batch = models.ForeignKey(
        Batch, null=True, blank=True, on_delete=models.SET_NULL, related_name="staff"
    )

    employee_id = models.CharField(
        max_length=7,
        unique=True,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\d{7}$",
                message="Employee ID must be a 7-digit integer.",
            )
        ],
    )
    accops_id = models.CharField(max_length=128, blank=True)  # Accops VDI identifier
    department = models.CharField(max_length=100, blank=True, default="TCS Ignite Training")
    designation = models.CharField(max_length=100, blank=True, default="Administrator")
    profile_picture = models.TextField(blank=True, default="")
    last_active_at = models.DateTimeField(null=True, blank=True)
    must_change_password = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = CustomUserManager()

    def clean(self):
        super().clean()
        if not self.employee_id:
            self.employee_id = None
        elif isinstance(self.employee_id, str):
            self.employee_id = self.employee_id.strip()

    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = None
        elif isinstance(self.employee_id, str):
            self.employee_id = self.employee_id.strip()
        if (self.is_superuser or self.is_staff) and self.role == "TRAINEE":
            self.role = "ADMIN"
        if self.is_superuser:
            self.must_change_password = False
        super().save(*args, **kwargs)

    @property
    def cohort_code(self):
        if self.sub_batch:
            return self.sub_batch.batch.cohort.code
        if self.assigned_cohort:
            return self.assigned_cohort.code
        return ""

    @property
    def batch_code(self):
        if self.sub_batch:
            return self.sub_batch.batch.name
        if self.assigned_batch:
            return self.assigned_batch.name
        return ""

    @property
    def sub_batch_code(self):
        return self.sub_batch.name if self.sub_batch else ""

    @property
    def full_batch_name(self):
        if self.sub_batch:
            return self.sub_batch.full_code
        if self.assigned_batch:
            return self.assigned_batch.full_code
        if self.assigned_cohort:
            return self.assigned_cohort.code
        return "Unassigned"

    def __str__(self):
        return f"{self.email} ({self.role})"
