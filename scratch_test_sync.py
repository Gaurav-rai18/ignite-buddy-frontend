import sqlite3, json
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.ignite_server.settings")
sys.path.insert(0, "src")

import django
django.setup()

from server.apps.schedules.models import Schedule
from server.apps.schedules.views import _sync_grid_to_central
from server.data.central import get_central

s = Schedule.objects.get(id=1)
print("Schedule found:", s.title)
print("Calling _sync_grid_to_central...")
_sync_grid_to_central(s.grid_data, "*")

central = get_central()
slots = central.slots()
print(f"Total slots in central.db now: {len(slots)}")
c = sqlite3.connect("data/central.db")
print("Distinct batches in central.db timetable_slots:", c.execute("SELECT DISTINCT batch, COUNT(*) FROM timetable_slots GROUP BY batch").fetchall())

