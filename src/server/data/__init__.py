"""Persistence.

central
    Cross-trainee data the Admin Panel publishes: batches, assignments,
    weekly timetable. Versioned with a monotonic ``rev`` so offline PCs
    catch up via a sync cursor.
store / db / schema / migrate
    Per-user databases (reminders, activity, chat history, …). In production
    these can live in PostgreSQL (``DATABASE_URL``); in dev they are SQLite
    files under ``ASSISTANT_DATA/users/<hash>/``.
"""
