"""Shared types and helpers used by *both* the central server and every client.

This package must stay free of Django, PySide6, and other heavy dependencies so
it can be imported on trainee PCs and on the server alike.

Modules
-------
protocol
    Message type constants, device-op names, DeviceResult, and the JSON shapes
    that travel over the WebSocket.
redaction
    Strip secrets / PII from logs and audit trails.
codectx
    Small helpers for encoding context passed between layers.
"""
