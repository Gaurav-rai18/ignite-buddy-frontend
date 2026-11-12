import asyncio
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status

from server.apps.accounts.models import User, Cohort, Batch, SubBatch
from server.apps.assignments.models import Assignment, AssignmentRecipient
from server.apps.assignments.notifications import (
    send_deadline_reminders,
    format_due,
)
from server.apps.notifications.models import Notification, NotificationRecipient


def _make_users():
    admin = User.objects.create_user(
        username="admin_user",
        email="admin@ignite.tcs.com",
        password="StrongPassword123!",
        role="ADMIN",
        is_staff=True,
        is_superuser=True,
    )
    ta = User.objects.create_user(
        username="ta_user",
        email="ta@ignite.tcs.com",
        password="StrongPassword123!",
        role="TA",
    )
    trainee = User.objects.create_user(
        username="trainee_user",
        email="trainee@ignite.tcs.com",
        password="StrongPassword123!",
        role="TRAINEE",
    )
    return admin, ta, trainee


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


class AssignmentNotificationTests(TestCase):
    """New-assignment, submission and evaluation notifications."""

    def setUp(self):
        self.client = APIClient()
        self.admin, self.ta, self.trainee = _make_users()
        self.cohort = Cohort.objects.create(name="Cohort 2026", code="C2026")
        self.batch = Batch.objects.create(name="Batch A", cohort=self.cohort)
        self.sub_batch = SubBatch.objects.create(name="Lab A1", batch=self.batch)
        self.trainee.cohort = self.cohort
        self.trainee.batch = self.batch
        self.trainee.sub_batch = self.sub_batch
        self.trainee.first_name = "Asha"
        self.trainee.save()

    def _create_assignment(self, **overrides):
        deadline = timezone.now().date() + timedelta(days=5)
        defaults = dict(
            topic="BST Implementation",
            subject="Data Structures",
            start_date=timezone.now().date(),
            deadline=deadline,
            message="Implement a balanced BST.",
            created_by=self.admin,
            recipient_type="ALL",
        )
        defaults.update(overrides)
        return Assignment.objects.create(**defaults)

    def test_publishing_notifies_all_eligible_trainees(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "topic": "Graph Traversal",
            "subject": "Algorithms",
            "start_date": timezone.now().date().isoformat(),
            "deadline": (timezone.now().date() + timedelta(days=5)).isoformat(),
            "deadline_at": (timezone.now() + timedelta(days=5)).isoformat(),
            "message": "Implement BFS and DFS.",
            "recipient_type": "ALL",
        }
        resp = self.client.post("/api/assignments/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        notif = Notification.objects.filter(
            dedupe_key=f"assignment:{resp.data['id']}:new:{self.trainee.id}"
        ).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.title, "New Assignment Posted")
        self.assertIn("Graph Traversal", notif.message)
        self.assertIn("Hi Asha!", notif.message)
        self.assertEqual(notif.priority, "high")
        self.assertEqual(notif.category, "assignment")
        self.assertTrue(notif.action_url.endswith(f"/assignments/{resp.data['id']}"))
        # Inbox row created for the trainee
        self.assertTrue(
            NotificationRecipient.objects.filter(notification=notif, user=self.trainee).exists()
        )

    def test_invalid_deadline_at_is_rejected_before_assignment_creation(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "topic": "Invalid date-time",
            "subject": "Algorithms",
            "start_date": timezone.now().date().isoformat(),
            "deadline": (timezone.now().date() + timedelta(days=5)).isoformat(),
            "deadline_at": "not-a-date-time",
            "message": "This should not be published.",
            "recipient_type": "ALL",
        }

        response = self.client.post("/api/assignments/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Assignment.objects.filter(topic="Invalid date-time").exists())

    def test_editing_published_assignment_retries_a_missing_notification(self):
        assignment = self._create_assignment()
        AssignmentRecipient.objects.create(assignment=assignment, user=self.trainee)
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            f"/api/assignments/{assignment.id}/",
            {"message": "Updated instructions."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        key = f"assignment:{assignment.id}:new:{self.trainee.id}"
        self.assertTrue(Notification.objects.filter(dedupe_key=key).exists())

        retry = self.client.patch(
            f"/api/assignments/{assignment.id}/",
            {"message": "Updated instructions again."},
            format="json",
        )
        self.assertEqual(retry.status_code, status.HTTP_200_OK)
        self.assertEqual(Notification.objects.filter(dedupe_key=key).count(), 1)

    def test_new_assignment_notification_is_not_duplicated(self):
        assignment = self._create_assignment()
        AssignmentRecipient.objects.create(assignment=assignment, user=self.trainee)
        from server.apps.assignments.notifications import notify_new_assignment

        first = notify_new_assignment(assignment)
        second = notify_new_assignment(assignment)
        self.assertEqual(first, 1)
        self.assertEqual(second, 0)
        self.assertEqual(
            Notification.objects.filter(title="New Assignment Posted").count(), 1
        )

    def test_draft_is_hidden_from_trainee_until_published(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "topic": "Draft Only",
            "subject": "Algorithms",
            "start_date": timezone.now().date().isoformat(),
            "deadline": (timezone.now().date() + timedelta(days=3)).isoformat(),
            "message": "Not yet published.",
            "recipient_type": "ALL",
            "is_published": False,
        }
        resp = self.client.post("/api/assignments/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        assignment_id = resp.data["id"]
        self.assertFalse(Assignment.objects.get(pk=assignment_id).is_published)
        self.assertFalse(Notification.objects.filter(title="New Assignment Posted").exists())

        # Trainee does not see the draft
        self.client.force_authenticate(user=self.trainee)
        list_resp = self.client.get("/api/assignments/")
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual([a for a in list_resp.data if a["id"] == assignment_id], [])

        # Publish it -> trainee sees it and gets the notification
        self.client.force_authenticate(user=self.admin)
        pub = self.client.patch(
            f"/api/assignments/{assignment_id}/", {"is_published": True}, format="json"
        )
        self.assertEqual(pub.status_code, status.HTTP_200_OK)
        self.assertTrue(Assignment.objects.get(pk=assignment_id).is_published)
        self.assertEqual(Notification.objects.filter(title="New Assignment Posted").count(), 1)

    def test_submission_notifies_trainee_and_faculty(self):
        assignment = self._create_assignment()
        AssignmentRecipient.objects.create(assignment=assignment, user=self.trainee)

        self.client.force_authenticate(user=self.trainee)
        resp = self.client.post(
            f"/api/assignments/{assignment.id}/submissions/",
            {"submission_text": "Done."},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertTrue(
            Notification.objects.filter(title="Submission Received", dedupe_key__contains=str(self.trainee.id)).exists()
        )
        faculty_notif = Notification.objects.filter(title="New Submission Received").first()
        self.assertIsNotNone(faculty_notif)
        self.assertTrue(
            NotificationRecipient.objects.filter(notification=faculty_notif, user=self.admin).exists()
        )

    def test_evaluation_notifies_trainee_with_feedback(self):
        assignment = self._create_assignment()
        recipient = AssignmentRecipient.objects.create(
            assignment=assignment, user=self.trainee, status="SUBMITTED",
            submitted_at=timezone.now(),
        )
        self.client.force_authenticate(user=self.ta)
        resp = self.client.post(
            f"/api/assignments/{assignment.id}/evaluate/{recipient.id}/",
            {"grade": "A", "feedback": "Great work."},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        notif = Notification.objects.filter(title="Feedback Available").first()
        self.assertIsNotNone(notif)
        self.assertIn("Great work.", notif.message)
        self.assertIn("A", notif.message)

    def test_evaluation_without_feedback_uses_evaluated_title(self):
        assignment = self._create_assignment()
        recipient = AssignmentRecipient.objects.create(
            assignment=assignment, user=self.trainee, status="SUBMITTED",
            submitted_at=timezone.now(),
        )
        self.client.force_authenticate(user=self.ta)
        resp = self.client.post(
            f"/api/assignments/{assignment.id}/evaluate/{recipient.id}/",
            {"grade": "B"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(Notification.objects.filter(title="Assignment Evaluated").exists())
        self.assertFalse(Notification.objects.filter(title="Feedback Available").exists())


class AssignmentReminderTests(TestCase):
    """24h / 1h deadline reminders, dedupe, submitted-skip and timezone handling."""

    def setUp(self):
        self.admin, self.ta, self.trainee = _make_users()
        self.cohort = Cohort.objects.create(name="Cohort 2026", code="C2026")
        self.batch = Batch.objects.create(name="Batch A", cohort=self.cohort)
        self.sub_batch = SubBatch.objects.create(name="Lab A1", batch=self.batch)
        self.trainee.cohort = self.cohort
        self.trainee.batch = self.batch
        self.trainee.sub_batch = self.sub_batch
        self.trainee.save()

    def _assignment_due_in(self, hours=0, minutes=0):
        now = timezone.now()
        due = now + timedelta(hours=hours, minutes=minutes)
        return Assignment.objects.create(
            topic="Reminder Test",
            subject="Algorithms",
            start_date=now.date(),
            deadline=due.date(),
            deadline_at=due,
            message="Reminder test assignment.",
            created_by=self.admin,
            recipient_type="ALL",
            is_published=True,
        )

    def test_24h_reminder_fires_once(self):
        assignment = self._assignment_due_in(hours=23)
        AssignmentRecipient.objects.create(assignment=assignment, user=self.trainee)

        self.assertEqual(send_deadline_reminders(), 1)
        notif = Notification.objects.get(title="Assignment Due Tomorrow")
        self.assertIn("is due tomorrow", notif.message)
        # Second scan is a no-op (duplicate prevention)
        self.assertEqual(send_deadline_reminders(), 0)
        self.assertEqual(Notification.objects.filter(title="Assignment Due Tomorrow").count(), 1)

    def test_24h_reminder_waits_until_the_window_opens(self):
        assignment = self._assignment_due_in(hours=25)
        AssignmentRecipient.objects.create(assignment=assignment, user=self.trainee)

        self.assertEqual(send_deadline_reminders(), 0)
        self.assertFalse(Notification.objects.filter(title="Assignment Due Tomorrow").exists())

        due = timezone.now() + timedelta(hours=23)
        Assignment.objects.filter(pk=assignment.pk).update(
            deadline=due.date(),
            deadline_at=due,
        )
        self.assertEqual(send_deadline_reminders(), 1)
        self.assertTrue(Notification.objects.filter(title="Assignment Due Tomorrow").exists())

    def test_1h_reminder_fires_once(self):
        assignment = self._assignment_due_in(minutes=30)
        AssignmentRecipient.objects.create(assignment=assignment, user=self.trainee)

        self.assertEqual(send_deadline_reminders(), 1)
        notif = Notification.objects.get(title="Deadline Approaching")
        self.assertIn("due in 1 hour", notif.message)
        self.assertEqual(notif.priority, "urgent")
        self.assertEqual(send_deadline_reminders(), 0)

    def test_submitted_trainee_is_skipped(self):
        assignment = self._assignment_due_in(hours=23)
        AssignmentRecipient.objects.create(
            assignment=assignment, user=self.trainee,
            status="SUBMITTED", submitted_at=timezone.now(),
        )
        self.assertEqual(send_deadline_reminders(), 0)
        self.assertFalse(Notification.objects.filter(title="Assignment Due Tomorrow").exists())

    def test_resubmission_rearms_reminders(self):
        assignment = self._assignment_due_in(hours=23)
        recipient = AssignmentRecipient.objects.create(
            assignment=assignment, user=self.trainee,
            status="SUBMITTED", submitted_at=timezone.now(),
        )
        self.assertEqual(send_deadline_reminders(), 0)

        # Faculty sends the submission back for resubmission
        self.client = APIClient()
        self.client.force_authenticate(user=self.ta)
        resp = self.client.post(
            f"/api/assignments/{assignment.id}/evaluate/{recipient.id}/",
            {"grade": "C", "feedback": "Please redo.", "resubmission_required": True},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        recipient.refresh_from_db()
        self.assertTrue(recipient.resubmission_required)
        self.assertIsNone(recipient.notified_24h_at)

        # Reminder now fires because the submission needs a resubmission
        self.assertEqual(send_deadline_reminders(), 1)
        self.assertEqual(Notification.objects.filter(title="Assignment Due Tomorrow").count(), 1)

    def test_past_due_assignment_sends_no_reminder(self):
        now = timezone.now()
        assignment = Assignment.objects.create(
            topic="Expired",
            subject="Algorithms",
            start_date=(now - timedelta(days=3)).date(),
            deadline=(now - timedelta(days=1)).date(),
            deadline_at=now - timedelta(hours=2),
            message="Too late.",
            created_by=self.admin,
            recipient_type="ALL",
            is_published=True,
        )
        AssignmentRecipient.objects.create(assignment=assignment, user=self.trainee)
        self.assertEqual(send_deadline_reminders(), 0)

    def test_unpublished_assignment_sends_no_reminder(self):
        assignment = self._assignment_due_in(hours=23)
        Assignment.objects.filter(pk=assignment.pk).update(is_published=False)
        AssignmentRecipient.objects.create(assignment=assignment, user=self.trainee)
        self.assertEqual(send_deadline_reminders(), 0)

    def test_deadline_timezone_is_respected(self):
        due = timezone.now() + timedelta(hours=23)
        assignment = Assignment.objects.create(
            topic="TZ",
            subject="Algorithms",
            start_date=due.date(),
            deadline=due.date(),
            deadline_at=due,
            message="TZ test",
            created_by=self.admin,
            recipient_type="ALL",
        )
        self.assertTrue(timezone.is_aware(assignment.due_at))
        self.assertEqual(assignment.due_at, due)
        # format_due renders in the active (server) timezone as local time
        self.assertEqual(
            format_due(assignment.due_at),
            timezone.localtime(due).strftime("%d %b %Y, %I:%M %p"),
        )

    def test_deadline_without_time_falls_back_to_end_of_day(self):
        day = timezone.now().date() + timedelta(days=2)
        assignment = Assignment.objects.create(
            topic="Date only",
            subject="Algorithms",
            start_date=timezone.now().date(),
            deadline=day,
            message="End of day fallback",
            created_by=self.admin,
            recipient_type="ALL",
        )
        self.assertEqual(assignment.due_at.date(), day)
        self.assertEqual(timezone.localtime(assignment.due_at).hour, 23)


class AssignmentTargetingAndPermissionTests(TestCase):
    """Batch/cohort targeting, trainee visibility and permission enforcement."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin_user", email="admin@ignite.tcs.com",
            password="StrongPassword123!", role="ADMIN", is_staff=True, is_superuser=True,
        )
        self.cohort = Cohort.objects.create(name="Cohort 2026", code="C2026")
        self.batch_a = Batch.objects.create(name="Batch A", cohort=self.cohort)
        self.batch_b = Batch.objects.create(name="Batch B", cohort=self.cohort)
        self.sub_batch_a1 = SubBatch.objects.create(name="Lab A1", batch=self.batch_a)
        self.sub_batch_b1 = SubBatch.objects.create(name="Lab B1", batch=self.batch_b)

        self.trainee_a = User.objects.create_user(
            username="trainee_a", email="a@ignite.tcs.com", password="P@ssw0rd!1",
            role="TRAINEE", sub_batch=self.sub_batch_a1,
        )
        self.trainee_b = User.objects.create_user(
            username="trainee_b", email="b@ignite.tcs.com", password="P@ssw0rd!1",
            role="TRAINEE", sub_batch=self.sub_batch_b1,
        )

    def test_batch_targeting_only_assigns_selected_batch(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "topic": "Batch A only",
            "subject": "Algorithms",
            "start_date": timezone.now().date().isoformat(),
            "deadline": (timezone.now().date() + timedelta(days=5)).isoformat(),
            "message": "Only batch A.",
            "recipient_type": "BATCH",
            "batch_ids": [self.batch_a.id],
        }
        resp = self.client.post("/api/assignments/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        assignment = Assignment.objects.get(pk=resp.data["id"])
        assigned_users = set(assignment.recipients.values_list("user__username", flat=True))
        self.assertIn("trainee_a", assigned_users)
        self.assertNotIn("trainee_b", assigned_users)

    def test_trainee_only_sees_own_assignments(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "topic": "Batch B only",
            "subject": "Algorithms",
            "start_date": timezone.now().date().isoformat(),
            "deadline": (timezone.now().date() + timedelta(days=5)).isoformat(),
            "message": "Only batch B.",
            "recipient_type": "BATCH",
            "batch_ids": [self.batch_b.id],
        }
        self.client.post("/api/assignments/", payload, format="json")

        self.client.force_authenticate(user=self.trainee_a)
        resp = self.client.get("/api/assignments/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

        self.client.force_authenticate(user=self.trainee_b)
        resp_b = self.client.get("/api/assignments/")
        self.assertEqual(len(resp_b.data), 1)
        self.assertEqual(resp_b.data[0]["topic"], "Batch B only")

    def test_trainee_cannot_evaluate_submission(self):
        assignment = Assignment.objects.create(
            topic="Perm", subject="Algorithms",
            start_date=timezone.now().date(),
            deadline=timezone.now().date() + timedelta(days=3),
            message="Perm test", created_by=self.admin, recipient_type="ALL",
        )
        recipient = AssignmentRecipient.objects.create(
            assignment=assignment, user=self.trainee_a,
            status="SUBMITTED", submitted_at=timezone.now(),
        )
        self.client.force_authenticate(user=self.trainee_a)
        resp = self.client.post(
            f"/api/assignments/{assignment.id}/evaluate/{recipient.id}/",
            {"grade": "A"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_trainee_cannot_delete_assignment(self):
        assignment = Assignment.objects.create(
            topic="Perm2", subject="Algorithms",
            start_date=timezone.now().date(),
            deadline=timezone.now().date() + timedelta(days=3),
            message="Perm test", created_by=self.admin, recipient_type="ALL",
        )
        self.client.force_authenticate(user=self.trainee_a)
        resp = self.client.delete(f"/api/assignments/{assignment.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class AssignmentSchedulerTickTests(TestCase):
    """The scheduler hook must dispatch reminders and never raise."""

    def test_tick_assignments_calls_reminder_scan(self):
        from server.jobs.runner import tick_assignments

        admin, _, trainee = _make_users()
        due = timezone.now() + timedelta(hours=23)
        assignment = Assignment.objects.create(
            topic="Scheduler", subject="Algorithms",
            start_date=due.date(), deadline=due.date(), deadline_at=due,
            message="sched", created_by=admin, recipient_type="ALL", is_published=True,
        )
        AssignmentRecipient.objects.create(assignment=assignment, user=trainee)

        self.assertEqual(tick_assignments(), 1)
        self.assertEqual(tick_assignments(), 0)


class TraineeAssignmentWebSocketTests(TransactionTestCase):
    """The trainee desktop reads and submits assignments over the assistant WebSocket.

    The consumer handlers are exercised directly (authentication, framing and the
    channel layer are covered by the transport integration tests).
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username="faculty_user", email="faculty@ignite.tcs.com",
            password="StrongPassword123!", role="ADMIN",
        )
        self.trainee = User.objects.create_user(
            username="alice", email="alice@ignite.tcs.com",
            password="StrongPassword123!", role="TRAINEE", first_name="Alice",
        )
        self.cohort = Cohort.objects.create(name="Cohort 2026", code="C2026")
        self.batch = Batch.objects.create(name="Batch A", cohort=self.cohort)
        self.other_batch = Batch.objects.create(name="Batch B", cohort=self.cohort)
        self.sub_batch = SubBatch.objects.create(name="Lab A1", batch=self.batch)
        self.trainee.cohort = self.cohort
        self.trainee.batch = self.batch
        self.trainee.sub_batch = self.sub_batch
        self.trainee.save()

    # ---- helpers ----
    def _assignment(self, topic="WS Assignment", published=True, batch=None, **overrides):
        due = timezone.now() + timedelta(days=2)
        defaults = dict(
            topic=topic,
            subject="Algorithms",
            platform_link="https://example.com/brief.pdf",
            start_date=timezone.now().date(),
            deadline=due.date(),
            deadline_at=due,
            message="Read the brief and submit your repository link.",
            created_by=self.admin,
            recipient_type="BATCH" if batch else "ALL",
            target_batch=batch,
            is_published=published,
        )
        defaults.update(overrides)
        return Assignment.objects.create(**defaults)

    def _consumer(self, user=None):
        """A consumer that behaves like an authenticated trainee desktop session."""
        from server.realtime.consumer import AssistantConsumer
        from server.domain.session import User as SessionUser

        consumer = AssistantConsumer()
        consumer.scope = {"type": "websocket"}
        consumer.user = user if user is not None else SessionUser(id="alice", name="Alice")
        consumer.account_user_id = self.trainee.id if user is None else None
        sent = []

        async def send_json(msg):
            sent.append(msg)

        consumer.send_json = send_json
        return consumer, sent

    # ---- tests ----
    def test_assignments_get_returns_only_published_targeted_work(self):
        # Recipients are who the admin targeting actually assigned the work to.
        mine = self._assignment(topic="Visible to Alice", batch=self.batch)
        AssignmentRecipient.objects.create(assignment=mine, user=self.trainee)
        other_batch = self._assignment(topic="Other batch", batch=self.other_batch)   # not assigned to Alice
        self.assertFalse(AssignmentRecipient.objects.filter(assignment=other_batch, user=self.trainee).exists())
        draft = self._assignment(topic="Draft", published=False)
        AssignmentRecipient.objects.create(assignment=draft, user=self.trainee)

        consumer, sent = self._consumer()
        asyncio.run(consumer.on_assignments_get({}))

        self.assertEqual(sent[0]["type"], "assignments_data")
        payload = sent[0]["assignments"]
        self.assertEqual([a["title"] for a in payload], ["Visible to Alice"])
        self.assertEqual(payload[0]["status"], "PENDING")
        self.assertEqual(payload[0]["recipient_id"], AssignmentRecipient.objects.get(assignment=mine).id)
        self.assertTrue(payload[0]["instructions"])
        self.assertTrue(payload[0]["due_at"])

    def test_assignment_submit_records_submission_and_refreshes_list(self):
        assignment = self._assignment()
        recipient = AssignmentRecipient.objects.create(assignment=assignment, user=self.trainee)

        consumer, sent = self._consumer()
        asyncio.run(
            consumer.on_assignment_submit(
                {"assignment_id": assignment.id, "submission_text": "Done", "submission_link": "https://github.com/a/b"}
            )
        )

        self.assertTrue(sent[0]["ok"])
        self.assertEqual(sent[0]["status"], "SUBMITTED")
        self.assertEqual(sent[1]["type"], "assignments_data")
        self.assertEqual(sent[1]["assignments"][0]["status"], "SUBMITTED")

        recipient.refresh_from_db()
        self.assertEqual(recipient.status, "SUBMITTED")
        self.assertEqual(recipient.submission_text, "Done")
        self.assertEqual(recipient.submission_link, "https://github.com/a/b")
        self.assertIsNotNone(recipient.submitted_at)
        # The trainee and the faculty both get told about the submission.
        self.assertTrue(Notification.objects.filter(title="Submission Received").exists())
        self.assertTrue(Notification.objects.filter(title="New Submission Received").exists())

    def test_assignment_submit_rejects_empty_and_unpublished(self):
        draft = self._assignment(topic="Draft", published=False)

        consumer, sent = self._consumer()
        asyncio.run(consumer.on_assignment_submit({"assignment_id": draft.id, "submission_text": "  "}))
        self.assertFalse(sent[0]["ok"])
        self.assertIn("submission link", sent[0]["error"])

        asyncio.run(consumer.on_assignment_submit({"assignment_id": draft.id, "submission_text": "late"}))
        self.assertFalse(sent[1]["ok"])
        self.assertEqual(sent[1]["error"], "Assignment not found.")
        self.assertEqual(AssignmentRecipient.objects.count(), 0)

    def test_account_lookup_falls_back_to_the_socket_identity(self):
        # Older JWTs use usernames as their subject. This one also belongs to an
        # admin, so lookup must choose the trainee account rather than .first().
        User.objects.create_user(
            username="alice",
            email="staff-alice@ignite.tcs.com",
            password="StrongPassword123!",
            role="ADMIN",
        )
        assignment = self._assignment()
        AssignmentRecipient.objects.create(assignment=assignment, user=self.trainee)

        consumer, sent = self._consumer()          # account_user_id deliberately not preset
        asyncio.run(consumer.on_assignments_get({}))
        self.assertEqual([a["title"] for a in sent[0]["assignments"]], [assignment.topic])

    def test_account_id_disambiguates_duplicate_trainee_usernames(self):
        from server.domain.session import User as SessionUser

        User.objects.create_user(
            username="alice",
            email="alice2@ignite.tcs.com",
            password="StrongPassword123!",
            role="TRAINEE",
        )
        assignment = self._assignment()
        AssignmentRecipient.objects.create(assignment=assignment, user=self.trainee)

        consumer, sent = self._consumer(
            user=SessionUser(id="alice", name="Alice", account_user_id=self.trainee.id)
        )
        asyncio.run(consumer.on_assignments_get({}))

        self.assertEqual([a["title"] for a in sent[0]["assignments"]], [assignment.topic])
        self.assertEqual(consumer._account_user().id, self.trainee.id)

    def test_unauthenticated_consumer_sends_nothing(self):
        consumer, sent = self._consumer(user=False)   # user=False -> self.user is falsy
        asyncio.run(consumer.on_assignments_get({}))
        asyncio.run(consumer.on_assignment_submit({"assignment_id": 1, "submission_text": "hi"}))
        self.assertEqual(sent, [])
        self.assertEqual(AssignmentRecipient.objects.count(), 0)
