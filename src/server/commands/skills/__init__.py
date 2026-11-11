"""Importing this package registers every skill (tools + grammar rules). IMPORT ORDER = RULE PRIORITY:
the first rule that matches a clause wins, so specific skills come before generic ones (system.open_target last).

When adding a command: create or extend a skill module, register the
tool and parse rule, and add coverage under ``tests/server/``.
"""
from . import blocked, timers, reminders, trainee, notes, tasks, activity, privacy, utility, files, system, web, help  # noqa: F401
