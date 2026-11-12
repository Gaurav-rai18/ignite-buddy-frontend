"""Tests for the shared notification service and the trainee inbox API."""
import asyncio

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from server.apps.accounts.models import User
from server.apps.notifications.models import Notification, NotificationRecipient
from server.apps.notifications.services import create_notification
from server.realtime.notifier import user_group


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.trainee = User.objects.create_user(
            username="trainee_user",
            email="trainee@ignite.tcs.com",
            password="StrongPassword123!",
            role="TRAINEE",
        )

    def test_create_notification_persists_and_delivers(self):
        notif, created = create_notification(
            title="New Assignment Posted",
            message="Hi Trainee! A new assignment has been posted.",
            users=[self.trainee],
            category="assignment",
            priority="high",
            action_url="/assignments/1",
            action_label="Open assignment",
        )
        self.assertTrue(created)
        self.assertEqual(notif.title, "New Assignment Posted")
        self.assertTrue(
            NotificationRecipient.objects.filter(notification=notif, user=self.trainee).exists()
        )

    def test_assignment_notification_reaches_connected_buddy_immediately(self):
        layer = get_channel_layer()
        group = user_group(self.trainee.username)
        channel = async_to_sync(layer.new_channel)()
        async_to_sync(layer.group_add)(group, channel)
        try:
            notif, created = create_notification(
                title="New Assignment Posted",
                message="Your assignment is ready.",
                users=[self.trainee],
                category="assignment",
                priority="high",
                action_url="/assignments/42",
                action_label="Open assignment",
                dedupe_key=f"assignment:42:new:{self.trainee.id}",
                ws_kind="assignment",
            )

            async def receive_event():
                return await asyncio.wait_for(layer.receive(channel), timeout=1)

            event = async_to_sync(receive_event)()
        finally:
            async_to_sync(layer.group_discard)(group, channel)

        self.assertTrue(created)
        self.assertEqual(notif.title, "New Assignment Posted")
        self.assertEqual(event["type"], "trainee.notification")
        self.assertEqual(event["kind"], "assignment")
        self.assertEqual(event["category"], "assignment")
        self.assertEqual(event["action_url"], "/assignments/42")

    def test_dedupe_key_prevents_duplicates(self):
        _, first = create_notification(
            title="Deadline Approaching",
            message="Due in 1 hour.",
            users=[self.trainee],
            dedupe_key="assignment:1:1h:1",
        )
        existing, second = create_notification(
            title="Deadline Approaching",
            message="Due in 1 hour.",
            users=[self.trainee],
            dedupe_key="assignment:1:1h:1",
        )
        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(existing.dedupe_key, "assignment:1:1h:1")

    def test_no_users_still_records_master_notification(self):
        notif, created = create_notification(
            title="Broadcast",
            message="Hello all",
            users=[],
            broadcast_group="all_trainees",
        )
        self.assertTrue(created)
        self.assertEqual(notif.recipients.count(), 0)


class TraineeInboxApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.trainee = User.objects.create_user(
            username="trainee_user",
            email="trainee@ignite.tcs.com",
            password="StrongPassword123!",
            role="TRAINEE",
        )

    def test_user_notifications_include_action_metadata(self):
        create_notification(
            title="Feedback Available",
            message="Your submission was evaluated.",
            users=[self.trainee],
            category="assignment",
            priority="high",
            action_url="/assignments/7",
            action_label="View feedback",
        )
        self.client.force_authenticate(user=self.trainee)
        resp = self.client.get("/api/notifications/user-notifications/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        row = resp.data[0]
        self.assertEqual(row["title"], "Feedback Available")
        self.assertEqual(row["priority"], "high")
        self.assertEqual(row["category"], "assignment")
        self.assertEqual(row["action_url"], "/assignments/7")
        self.assertEqual(row["action_label"], "View feedback")
        self.assertFalse(row["is_read"])

    def test_mark_notification_read(self):
        _, _ = create_notification(
            title="Submission Received",
            message="Received.",
            users=[self.trainee],
        )
        recipient = NotificationRecipient.objects.get(user=self.trainee)
        self.client.force_authenticate(user=self.trainee)
        resp = self.client.patch(f"/api/notifications/read/{recipient.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        recipient.refresh_from_db()
        self.assertTrue(recipient.is_read)
        self.assertIsNotNone(recipient.read_at)
