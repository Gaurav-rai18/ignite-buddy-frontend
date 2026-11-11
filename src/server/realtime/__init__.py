"""Network edge of the server: WebSockets, presence, admin static page.

Modules
-------
consumer
    Channels consumer: auth frame, rate limits, dispatch to orchestrator.
notifier / presence
    Live sync and online set.
admin_ui.html
    Classic Admin Panel at ``/admin/``.
session_ui / routing
    Channels routing and UI adapter.
"""
