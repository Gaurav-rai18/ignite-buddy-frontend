from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from server.apps.accounts.models import User, Cohort, Batch, SubBatch
from server.apps.assignments.models import Assignment, AssignmentRecipient


class AssignmentFeatureTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Users
        self.admin = User.objects.create_user(
            username="admin_user",
            email="admin@ignite.tcs.com",
            password="StrongPassword123!",
            role="ADMIN",
            is_staff=True,
            is_superuser=True,
        )
        self.ta = User.objects.create_user(
            username="ta_user",
            email="ta@ignite.tcs.com",
            password="StrongPassword123!",
            role="TA",
        )
        self.trainee = User.objects.create_user(
            username="trainee_user",
            email="trainee@ignite.tcs.com",
            password="StrongPassword123!",
            role="TRAINEE",
        )

        # Cohort, Batch, SubBatch
        self.cohort = Cohort.objects.create(name="Ignite Cohort 2026", code="C2026")
        self.batch = Batch.objects.create(name="Batch A", cohort=self.cohort)
        self.sub_batch = SubBatch.objects.create(name="Lab A1", batch=self.batch)

        self.trainee.cohort = self.cohort
        self.trainee.batch = self.batch
        self.trainee.sub_batch = self.sub_batch
        self.trainee.save()

    def test_admin_create_assignment_all_students(self):
        self.client.force_authenticate(user=self.admin)
        start = timezone.now().date().isoformat()
        deadline = (timezone.now() + timedelta(days=7)).date().isoformat()

        payload = {
            "topic": "Binary Search Trees Implementation",
            "subject": "Advanced Data Structures",
            "platform_link": "https://hackerearth.com/practice/bst",
            "start_date": start,
            "deadline": deadline,
            "message": "Complete all 5 test cases and submit your github repo.",
            "recipient_type": "ALL",
        }

        response = self.client.post("/api/assignments/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["topic"], payload["topic"])

        # Trainee should have received AssignmentRecipient
        assignment_id = response.data["id"]
        recipient = AssignmentRecipient.objects.filter(assignment_id=assignment_id, user=self.trainee).first()
        self.assertIsNotNone(recipient)
        self.assertEqual(recipient.status, "PENDING")

    def test_trainee_cannot_create_assignment(self):
        self.client.force_authenticate(user=self.trainee)
        payload = {
            "topic": "Unauthorized Attempt",
            "subject": "Hacking",
            "start_date": timezone.now().date().isoformat(),
            "deadline": (timezone.now() + timedelta(days=1)).date().isoformat(),
            "message": "Should fail",
            "recipient_type": "ALL",
        }
        response = self.client.post("/api/assignments/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_deadline_patch(self):
        self.client.force_authenticate(user=self.ta)
        start = timezone.now().date()
        deadline = start + timedelta(days=3)

        assignment = Assignment.objects.create(
            topic="Dynamic Programming",
            subject="Algorithms",
            start_date=start,
            deadline=deadline,
            message="Solve the knapsack problem.",
            created_by=self.ta,
            recipient_type="ALL",
        )

        new_deadline = (start + timedelta(days=10)).isoformat()
        response = self.client.patch(
            f"/api/assignments/{assignment.id}/",
            {"deadline": new_deadline},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assignment.refresh_from_db()
        self.assertEqual(str(assignment.deadline), new_deadline)

    def test_trainee_submission_and_evaluation(self):
        # 1. Admin creates assignment
        assignment = Assignment.objects.create(
            topic="REST API Integration",
            subject="Cloud Systems",
            start_date=timezone.now().date(),
            deadline=timezone.now().date() + timedelta(days=5),
            message="Build a DRF endpoint.",
            created_by=self.admin,
            recipient_type="ALL",
        )
        recipient = AssignmentRecipient.objects.create(
            assignment=assignment,
            user=self.trainee,
            status="PENDING",
        )

        # 2. Trainee submits work
        self.client.force_authenticate(user=self.trainee)
        sub_payload = {
            "submission_link": "https://github.com/ignite-trainee/drf-solution",
            "submission_text": "Completed all unit tests and docker configuration.",
        }
        sub_resp = self.client.post(
            f"/api/assignments/{assignment.id}/submissions/",
            sub_payload,
            format="json",
        )
        self.assertEqual(sub_resp.status_code, status.HTTP_200_OK)
        recipient.refresh_from_db()
        self.assertEqual(recipient.status, "SUBMITTED")
        self.assertEqual(recipient.submission_link, sub_payload["submission_link"])

        # 3. TA grades work
        self.client.force_authenticate(user=self.ta)
        eval_payload = {
            "grade": "A+",
            "feedback": "Outstanding implementation with comprehensive test coverage.",
        }
        eval_resp = self.client.post(
            f"/api/assignments/{assignment.id}/evaluate/{recipient.id}/",
            eval_payload,
            format="json",
        )
        self.assertEqual(eval_resp.status_code, status.HTTP_200_OK)
        recipient.refresh_from_db()
        self.assertEqual(recipient.status, "EVALUATED")
        self.assertEqual(recipient.grade, "A+")
        self.assertEqual(recipient.evaluated_by, self.ta)

    def test_delete_assignment(self):
        self.client.force_authenticate(user=self.admin)
        assignment = Assignment.objects.create(
            topic="Temporary Homework",
            subject="Scratch",
            start_date=timezone.now().date(),
            deadline=timezone.now().date() + timedelta(days=1),
            message="Delete me",
            created_by=self.admin,
            recipient_type="ALL",
        )
        resp = self.client.delete(f"/api/assignments/{assignment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Assignment.objects.filter(id=assignment.id).exists())
