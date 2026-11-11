import pytest
from server.channels_push import send_channel_message
from server.realtime import notifier


def test_broadcast_dispatch_all_trainees():
    # Verify sending to all_trainees group does not fail
    send_channel_message(notifier.ALL_GROUP, {
        "type": "trainee.notification",
        "kind": "broadcast",
        "text": "Broadcast to all",
    })


def test_broadcast_dispatch_batch():
    # Verify sending to a specific batch group
    send_channel_message(notifier.batch_group("IGN-2026-Batch 1"), {
        "type": "trainee.notification",
        "kind": "broadcast",
        "text": "Broadcast to Batch 1",
    })


def test_broadcast_dispatch_multi_batch():
    # Verify sending to multiple targeted batches
    batches = ["IGN-2026-Batch 1", "IGN-2026-Batch 2", "IGN-2026-Batch 3"]
    payload = {
        "type": "trainee.notification",
        "kind": "broadcast",
        "title": "Lab Maintenance",
        "message": "Batches 1, 2, and 3 report to Lab 2 today.",
        "text": "Lab Maintenance: Batches 1, 2, and 3 report to Lab 2 today.",
    }
    for b in batches:
        send_channel_message(notifier.batch_group(b), payload)


def test_broadcast_dispatch_multi_sub_batch():
    # Verify sending to multiple targeted sub-batches
    sub_batches = ["IGN-2026-Batch 1-A", "IGN-2026-Batch 1-B"]
    payload = {
        "type": "trainee.notification",
        "kind": "broadcast",
        "title": "Sub-batch Quiz",
        "message": "Sub-batches A & B quiz starts at 2:00 PM.",
        "text": "Sub-batch Quiz: Sub-batches A & B quiz starts at 2:00 PM.",
    }
    for sb in sub_batches:
        send_channel_message(notifier.batch_group(sb), payload)


def test_broadcast_dispatch_user():
    # Verify sending to a specific user group
    send_channel_message(notifier.user_group("test_user_1"), {
        "type": "trainee.notification",
        "kind": "broadcast",
        "text": "Broadcast to test_user_1",
    })
