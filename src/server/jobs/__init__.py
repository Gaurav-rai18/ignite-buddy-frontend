"""Background work on the server process.

Fires due timers/reminders, daily activity summaries, and related jobs.
Windows-native alarms are *also* registered on the client via Task Scheduler;
the server keeps the master list and stays quiet when the OS will toast.
"""
