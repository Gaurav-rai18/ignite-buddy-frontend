"""
Helper for Channels group broadcasts from Django views.
"""
import asyncio
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer, InMemoryChannelLayer

logger = logging.getLogger(__name__)


# Patch InMemoryChannelLayer.group_send for Python 3.12+ / 3.14 compatibility:
# Channels' default InMemoryChannelLayer uses `asyncio.as_completed(ops)` which deadlocks
# or raises on empty groups in modern Python async runtimes.
async def _safe_in_memory_group_send(self, group, message):
    assert isinstance(message, dict), "Message is not a dict"
    self.require_valid_group_name(group)
    self._clean_expired()
    if group not in self.groups or not self.groups[group]:
        return
    ops = [self.send(channel, message) for channel in list(self.groups[group].keys())]
    if ops:
        await asyncio.gather(*ops, return_exceptions=True)

InMemoryChannelLayer.group_send = _safe_in_memory_group_send


def send_channel_message(group: str, message: dict):
    """
    Dispatches a message to a Channels group using asgiref.sync.async_to_sync,
    ensuring messages are broadcast reliably from synchronous Django views,
    worker threads, and ASGI servers.
    """
    try:
        layer = get_channel_layer()
        if not layer:
            return
        if hasattr(layer, "groups") and not layer.groups.get(group):
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            loop.create_task(layer.group_send(group, message))
        else:
            async_to_sync(layer.group_send)(group, message)
    except Exception as exc:
        logger.warning("send_channel_message error for group '%s': %s", group, exc)
