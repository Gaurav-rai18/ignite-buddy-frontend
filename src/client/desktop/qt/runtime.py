"""Runs the local agent (the Python that executes commands on this PC and talks to the central server) on a background thread,
so the Qt event loop stays free for the window."""
import asyncio
import threading

from client import config
from client.agent.server import Agent
from client.device.executor import DeviceExecutor
from client.net import Net
from client.sensors.activity import ActivitySampler


class AgentRuntime:
    def __init__(self, port: int | None = None):
        net = Net()
        self.agent = Agent(net, DeviceExecutor(), ActivitySampler(net.send), port if port is not None else config.AGENT_PORT)
        self.agent.ui_config["shell"] = True
        self.loop = asyncio.new_event_loop()
        self.url = ""
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="agent")

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.agent.loop = self.loop

        async def boot():
            self.url = await self.agent.start_server()
            self.agent.start_background()
            self._ready.set()
        self.loop.create_task(boot())
        self.loop.run_forever()

    def start(self, timeout: float = 15) -> str:
        self._thread.start()
        if not self._ready.wait(timeout):
            raise RuntimeError("the local agent did not start")
        return self.url

    def stop(self):
        try:
            self.agent.net.stop()
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)
