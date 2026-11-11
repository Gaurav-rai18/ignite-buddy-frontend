"""Local agent process that sits between the UI and the central server.

Serves the built React app from ``agent/static/`` on 127.0.0.1 only, owns the
WebSocket to the server, runs STT, and dispatches device operations through
``DeviceExecutor``. Used by both ``trainee-desktop`` (PySide6) and
``trainee-agent`` (open in a normal browser for development).

Security notes (see module docstring in ``server.py``): Host header checks,
Origin checks, per-run token embedded in the page, strict message allowlist.
"""
