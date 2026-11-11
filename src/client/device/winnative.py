"""
Native Windows reminders/timers/alarms.

Windows' Clock app has NO public API for creating alarms or timers (only `ms-clock:` to open it). The closest native
mechanism that works even when this assistant is closed is Task Scheduler + a Windows toast notification that uses the
system *alarm* sound and Dismiss/Snooze buttons. This module only BUILDS the PowerShell; DeviceExecutor runs it through
the launcher. Inputs are validated/escaped here because they originate from user text.
"""
import base64
import re
from xml.sax.saxutils import escape

REF_OK = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
TASK_PATH = "\\TraineeAssistant\\"


def _ps_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def encode_ps(script: str) -> str:
    """PowerShell -EncodedCommand wants base64 of UTF-16LE: no quoting problems, no injection through text."""
    return base64.b64encode(script.encode("utf-16-le")).decode()


def toast_script(title: str, text: str) -> str:
    xml = ('<toast scenario="alarm"><visual><binding template="ToastGeneric"><text>' + escape(title) + "</text><text>"
           + escape(text) + '</text></binding></visual><actions><action content="Snooze" arguments="snooze" '
           'activationType="system"/><action content="Dismiss" arguments="dismiss" activationType="system"/></actions>'
           '<audio src="ms-winsoundevent:Notification.Looping.Alarm2" loop="false"/></toast>')
    return ("[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null\n"
            "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null\n"
            "$x = New-Object Windows.Data.Xml.Dom.XmlDocument\n"
            f"$x.LoadXml({_ps_quote(xml)})\n"
            "$t = [Windows.UI.Notifications.ToastNotification]::new($x)\n"
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
            "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe').Show($t)\n")


def schedule_script(ref: str, kind: str, epoch: int, text: str, repeat: str = "") -> str:
    if not REF_OK.match(ref):
        raise ValueError("bad reference")
    if kind not in ("reminder", "timer") or repeat not in ("", "daily", "weekly"):
        raise ValueError("bad kind/repeat")
    title = "Timer finished" if kind == "timer" else "Reminder"
    action_arg = "-NoProfile -WindowStyle Hidden -EncodedCommand " + encode_ps(toast_script(title, (text or title)[:200]))
    trigger = {"": "New-ScheduledTaskTrigger -Once -At $when",
               "daily": "New-ScheduledTaskTrigger -Daily -At $when",
               "weekly": "New-ScheduledTaskTrigger -Weekly -DaysOfWeek $when.DayOfWeek -At $when"}[repeat]
    once = "" if repeat else "$tr.EndBoundary = $when.AddDays(7).ToString('s')\n"
    expire = "" if repeat else " -DeleteExpiredTaskAfter (New-TimeSpan -Days 1)"
    return ("$ErrorActionPreference = 'Stop'\n"
            f"$when = [DateTimeOffset]::FromUnixTimeSeconds({int(epoch)}).LocalDateTime\n"
            f"$act = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument {_ps_quote(action_arg)}\n"
            f"$tr = {trigger}\n{once}"
            "$set = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries "
            f"-DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5){expire}\n"
            f"Register-ScheduledTask -TaskName {_ps_quote(ref)} -TaskPath {_ps_quote(TASK_PATH)} "
            "-Action $act -Trigger $tr -Settings $set -Force | Out-Null\n")


def cancel_script(ref: str) -> str:
    if not REF_OK.match(ref):
        raise ValueError("bad reference")
    return (f"Unregister-ScheduledTask -TaskName {_ps_quote(ref)} -TaskPath {_ps_quote(TASK_PATH)} "
            "-Confirm:$false -ErrorAction SilentlyContinue\n")
