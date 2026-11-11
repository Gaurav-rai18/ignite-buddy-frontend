"""Backward-compatible shim.

The Admin API is now implemented as DRF ViewSets in server.api.views.
This module remains only so any residual imports keep working and to document
the migration. Prefer importing from server.api.
"""
from server.api.views import (  # noqa: F401
    AssignmentViewSet,
    TimetableViewSet,
    TraineeViewSet,
)

# Legacy function names (no longer used by urls.py)
assignments = None
timetable = None
trainees = None
panel = None
