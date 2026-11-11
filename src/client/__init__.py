"""Thin client that runs on each trainee PC.

Responsibilities
----------------
* Keep a WebSocket to the central server (``net``).
* Execute ``device_call`` operations safely (``device``) with local allowlists
  and UI confirmation for risky actions.
* Capture microphone audio and run STT locally (``stt``) — audio is never
  uploaded to the central server.
* Sample which apps are in use (``sensors``) and send coarse activity events.
* Host the React overlay either inside PySide6 (``desktop``) or in a normal
  browser via the local agent (``agent``).

This package must not import ``assistant_server``.
"""
