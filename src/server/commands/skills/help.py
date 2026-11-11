"""'help' lists the capabilities and query types the assistant understands."""
from server.domain import policy
from ..model import SAFE
from ..parser import RULES, rule
from ..registry import tool


@tool("show_help", SAFE, "List what the assistant can do.", {})
def show_help(s):
    off = [c for c, on in policy.capabilities(s.user.id).items() if not on]
    off_text = f"\n\n> Note: Disabled by your administrator: {', '.join(off)}" if off else ""

    return {
        "msg": f"""# Assistant Capabilities & Query Guide

### Company Policies & Space Information
Query internal company policies, code of conduct, leave and attendance guidelines, Accops VDI procedures, IT asset security, lab rules, workstation etiquette, and general Ignite space facilities. The system maintains multi-turn conversation memory and references internal policy documents.

### Task Management
Maintain your personal to-do checklist. Add tasks, mark items complete, view your pending list, or remove finished tasks.

### Notes & Scratchpad
Record notes, search across stored notes, update existing entries, and manage personal documentation saved locally on your workstation.

### Countdown Timers
Configure countdown timers and focus blocks (such as Pomodoro intervals or breaks) with desktop notifications and alerts.

### Scheduled Reminders
Schedule calendar and time-based alerts for meetings, reviews, submission deadlines, and routine reminders.

### Workstation Controls
Launch installed applications, open project folders in File Explorer, and control audio volume.

### Workspace Activity
Generate daily activity summaries and review productive time tracking.{off_text}
"""
    }


@rule(r"help|what can you do|show (?:me )?(?:the )?commands|list (?:the )?commands|commands", examples=("help",))
def help_rule(m, b):
    b.add("show_help")
