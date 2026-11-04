from django.db import migrations

def seed_defaults(apps, schema_editor):
    ScheduleLocation = apps.get_model('core', 'ScheduleLocation')
    ScheduleBatch = apps.get_model('core', 'ScheduleBatch')
    ScheduleSubBatch = apps.get_model('core', 'ScheduleSubBatch')
    ScheduleTimeSlot = apps.get_model('core', 'ScheduleTimeSlot')
    ScheduleWeekDay = apps.get_model('core', 'ScheduleWeekDay')

    locations = [
        {'name': 'Lab 1', 'badge': 'Hardware', 'color': '#014BAA', 'order': 1},
        {'name': 'Lab 2', 'badge': 'Software', 'color': '#0284C7', 'order': 2},
        {'name': 'Lab 3', 'badge': 'Data & AI', 'color': '#7C3AED', 'order': 3},
        {'name': 'Lab 4', 'badge': 'Cloud Ops', 'color': '#059669', 'order': 4},
        {'name': 'Work Area', 'badge': 'Work Area', 'color': '#D97706', 'order': 5},
        {'name': 'TR1', 'badge': 'TR1', 'color': '#EC4899', 'order': 6},
        {'name': 'TR2', 'badge': 'TR2', 'color': '#8B5CF6', 'order': 7},
    ]
    for loc in locations:
        ScheduleLocation.objects.get_or_create(name=loc['name'], defaults=loc)

    batches = [
        {'name': 'Batch A', 'code': 'A', 'order': 1, 'subs': ['A1', 'A2', 'A3', 'A4']},
        {'name': 'Batch B', 'code': 'B', 'order': 2, 'subs': ['B1', 'B2', 'B3', 'B4']},
        {'name': 'Batch C', 'code': 'C', 'order': 3, 'subs': ['C1', 'C2', 'C3', 'C4']},
    ]
    for b_data in batches:
        subs = b_data.pop('subs')
        b, _ = ScheduleBatch.objects.get_or_create(code=b_data['code'], defaults=b_data)
        for idx, sub_name in enumerate(subs, start=1):
            sub_code = sub_name.lower()
            ScheduleSubBatch.objects.get_or_create(
                batch=b,
                code=sub_code,
                defaults={'name': sub_name, 'order': idx}
            )

    time_slots = [
        {'start_time': '9:00 AM', 'end_time': '11:00 AM', 'label': '9:00 AM – 11:00 AM', 'order': 1},
        {'start_time': '11:30 AM', 'end_time': '1:30 PM', 'label': '11:30 AM – 1:30 PM', 'order': 2},
        {'start_time': '2:00 PM', 'end_time': '4:00 PM', 'label': '2:00 PM – 4:00 PM', 'order': 3},
        {'start_time': '4:30 PM', 'end_time': '6:00 PM', 'label': '4:30 PM – 6:00 PM', 'order': 4},
    ]
    for ts in time_slots:
        ScheduleTimeSlot.objects.get_or_create(label=ts['label'], defaults=ts)

    weekdays = [
        {'name': 'Monday', 'code': 'mon', 'order': 1},
        {'name': 'Tuesday', 'code': 'tue', 'order': 2},
        {'name': 'Wednesday', 'code': 'wed', 'order': 3},
        {'name': 'Thursday', 'code': 'thu', 'order': 4},
        {'name': 'Friday', 'code': 'fri', 'order': 5},
    ]
    for wd in weekdays:
        ScheduleWeekDay.objects.get_or_create(name=wd['name'], defaults=wd)

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_schedulebatch_schedulelocation_scheduletimeslot_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_defaults, migrations.RunPython.noop),
    ]

