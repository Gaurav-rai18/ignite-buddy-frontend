import io
from django.test import TestCase, Client
from .models import ScheduleLocation, ScheduleBatch, ScheduleSubBatch, ScheduleTimeSlot, ScheduleWeekDay, ScheduledLink
from .excel_utils import generate_schedule_template, parse_schedule_excel

class ScheduleEnhancementsBackendTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_schedule_config_endpoint(self):
        response = self.client.get('/api/schedule-config/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify 7 locations
        loc_names = [l['name'] for l in data['locations']]
        self.assertIn('Lab 1', loc_names)
        self.assertIn('Work Area', loc_names)
        self.assertIn('TR1', loc_names)
        self.assertIn('TR2', loc_names)
        self.assertNotIn('Incubator', loc_names)

        # Verify weekdays (only Mon-Fri)
        days = [w['name'] for w in data['weekdays']]
        self.assertIn('Monday', days)
        self.assertIn('Friday', days)
        self.assertNotIn('Saturday', days)
        self.assertNotIn('Sunday', days)

    def test_dynamic_batch_and_subbatch_creation(self):
        # Create Batch D
        res = self.client.post('/api/schedule-batches/', {'code': 'D', 'name': 'Batch D', 'subbatches_count': 3})
        self.assertEqual(res.status_code, 201)
        batch_id = res.json()['id']

        # Add Sub-batch D4
        sub_res = self.client.post('/api/schedule-subbatches/', {'batch': batch_id, 'name': 'D4', 'code': 'd4'})
        self.assertEqual(sub_res.status_code, 201)
        self.assertEqual(sub_res.json()['name'], 'D4')

        # Prevent duplicate code in same batch
        dup_res = self.client.post('/api/schedule-subbatches/', {'batch': batch_id, 'name': 'D4', 'code': 'd4'})
        self.assertEqual(dup_res.status_code, 400)

    def test_dynamic_timeslot_creation(self):
        res = self.client.post('/api/schedule-timeslots/', {
            'start_time': '6:30 PM',
            'end_time': '8:00 PM',
            'label': '6:30 PM – 8:00 PM',
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['label'], '6:30 PM – 8:00 PM')

    def test_reject_saturday_weekday(self):
        res = self.client.post('/api/schedule-weekdays/', {'name': 'Saturday', 'code': 'sat'})
        self.assertEqual(res.status_code, 400)

    def test_excel_template_download_and_parsing(self):
        # Download template
        dl_res = self.client.get('/api/schedule-template/')
        self.assertEqual(dl_res.status_code, 200)
        self.assertTrue(len(dl_res.content) > 1000)

        # Parse downloaded template
        file_obj = io.BytesIO(dl_res.content)
        file_obj.name = 'template.xlsx'
        parse_res = self.client.post('/api/schedules/parse-excel/', {'file': file_obj})
        self.assertEqual(parse_res.status_code, 200)
        parsed = parse_res.json()
        self.assertTrue(parsed['success'])
        self.assertTrue(parsed['total_rows_parsed'] > 0)
        self.assertIn('Monday', parsed['days_found'])
