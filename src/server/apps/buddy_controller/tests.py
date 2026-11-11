from django.test import TestCase
from rest_framework.test import APIClient

from server.apps.accounts.models import Cohort
from server.apps.buddy_controller.models import (
    Batch,
    Lab,
    ExamControl
)


# ==========================
# MODEL TESTS
# ==========================

class ExamControlModelTest(TestCase):

    def setUp(self):
        self.cohort = Cohort.objects.create(name="Cohort 1")
        self.batch = Batch.objects.create(
            name="Batch A",
            cohort=self.cohort
        )

        self.lab = Lab.objects.create(
            name="Lab A"
        )

    def test_exam_mode_default_false(self):

        exam_control = ExamControl.objects.create(
            trainee_name="John",
            device_id="DEV001",
            batch=self.batch,
            lab=self.lab
        )

        self.assertFalse(
            exam_control.exam_mode
        )

    def test_enable_exam_mode(self):

        exam_control = ExamControl.objects.create(
            trainee_name="John",
            device_id="DEV002",
            batch=self.batch,
            lab=self.lab
        )

        exam_control.exam_mode = True
        exam_control.save()

        exam_control.refresh_from_db()

        self.assertTrue(
            exam_control.exam_mode
        )


# ==========================
# VIEW TESTS
# ==========================

class ExamControlViewTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.cohort = Cohort.objects.create(name="Cohort 1")
        self.batch = Batch.objects.create(
            name="Batch A",
            cohort=self.cohort
        )

        self.lab = Lab.objects.create(
            name="Lab A"
        )

        self.exam_control = ExamControl.objects.create(
            trainee_name="John",
            device_id="DEV001",
            batch=self.batch,
            lab=self.lab,
            exam_mode=False
        )

    def test_start_exam(self):

        response = self.client.post(
            "/api/buddy/start-exam/",
            {},
            format="json"
        )

        self.exam_control.refresh_from_db()

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.data["message"],
            "Exam Mode Enabled"
        )

        self.assertTrue(
            ExamControl.objects.filter(
                exam_mode=True
            ).exists()
        )

    def test_end_exam(self):

        self.exam_control.exam_mode = True
        self.exam_control.save()

        response = self.client.post(
            "/api/buddy/end-exam/",
            {},
            format="json"
        )

        self.exam_control.refresh_from_db()

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.data["message"],
            "Exam Mode Disabled"
        )

        self.assertFalse(
            self.exam_control.exam_mode
        )

    def test_exam_status_when_enabled(self):

        self.exam_control.exam_mode = True
        self.exam_control.save()

        response = self.client.get(
            "/api/buddy/status/"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTrue(
            response.data["exam_mode"]
        )

    def test_exam_status_when_disabled(self):

        response = self.client.get(
            "/api/buddy/status/"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertFalse(
            response.data["exam_mode"]
        )
