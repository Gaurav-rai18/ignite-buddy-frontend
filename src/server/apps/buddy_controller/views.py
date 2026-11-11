from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import ExamControl, SystemSetting
from server.domain import policy
from server.channels_push import send_channel_message


def notify_policy_update():
    """Broadcasts policy change (exam mode / buddy blocked) to all active trainees."""
    send_channel_message("policy", {"type": "policy.update"})


@api_view(["POST"])
def start_exam(request):
    """Enables Exam Mode: blocks Trainee Buddy assistants during assessments."""
    ExamControl.objects.all().update(exam_mode=True)
    SystemSetting.set_bool("buddy_enabled", False, description="Exam mode active", user=request.user)
    SystemSetting.set_bool("exam_mode", True, description="Exam mode active", user=request.user)
    policy.set_blocked(True, reason="Exam in progress. The assistant is disabled.")
    notify_policy_update()

    return Response({
        "success": True,
        "exam_mode": True,
        "message": "Exam Mode Enabled"
    })


@api_view(["POST"])
def end_exam(request):
    """Disables Exam Mode: restores normal Trainee Buddy assistance."""
    ExamControl.objects.all().update(exam_mode=False)
    SystemSetting.set_bool("buddy_enabled", True, description="Buddy available", user=request.user)
    SystemSetting.set_bool("exam_mode", False, description="Exam mode disabled", user=request.user)
    policy.set_blocked(False, reason="")
    notify_policy_update()

    return Response({
        "success": True,
        "exam_mode": False,
        "message": "Exam Mode Disabled"
    })


@api_view(["GET"])
def exam_status(request):
    """Returns whether Exam Mode or an automated Test Lock is currently active."""
    exam_records = ExamControl.objects.filter(exam_mode=True)
    is_manual_exam = exam_records.exists() or SystemSetting.get_bool("exam_mode", default=False)

    from .test_lock import get_active_test_lock
    user_obj = request.user if request.user.is_authenticated else None
    test_lock = get_active_test_lock(user=user_obj)

    is_blocked = (
        policy.is_blocked(request.user.id if request.user.is_authenticated else None)
        or is_manual_exam
        or test_lock.get("is_locked", False)
    )
    return Response({
        "exam_mode": is_blocked,
        "is_manual_exam": is_manual_exam,
        "test_lock": test_lock,
    })


@api_view(["GET", "PATCH", "POST", "PUT"])
def get_or_update_buddy_setting(request):
    """
    Comprehensive Buddy configuration endpoint for Admin Console (/api/settings/buddy/).
    Returns and updates:
      - enabled: Master Buddy availability
      - exam_mode: Assessment lockdown
      - exam_reason: Reason displayed during assessment lockdown
      - test_auto_lock_enabled: Auto-disable during scheduled tests
      - test_buffer_before_minutes: Buffer before test starts (default 15m)
      - test_buffer_after_minutes: Buffer after test ends (default 15m)
      - active_test_lock: Real-time active test lock status
      - voice_enabled: Microphone / speech recognition input
      - voice_tts_enabled: Spoken audio responses
      - screen_help_enabled: Screen vision & error analysis
      - ide_tracking_enabled: Active editor/IDE context tracking
      - llm_model: Active AI model
      - llm_temperature: Temperature (0.0 to 1.0)
      - llm_system_prompt: Custom campus prompt instructions
      - max_queries_per_hour: Rate limit per trainee
      - rag_ignite_enabled: Ignite Program knowledge space
      - rag_general_enabled: General Engineering knowledge space
      - rag_personal_enabled: Trainee private documents indexing
      - blocked_keywords: Comma-separated restricted keywords
    """
    if request.method == "GET":
        master_enabled = SystemSetting.get_bool("buddy_enabled", default=not policy.is_blocked())
        exam_mode = SystemSetting.get_bool("exam_mode", default=False)

        from .test_lock import get_active_test_lock
        user_obj = request.user if request.user.is_authenticated else None
        active_test_lock = get_active_test_lock(user=user_obj)

        return Response({
            "enabled": master_enabled,
            "exam_mode": exam_mode,
            "exam_reason": SystemSetting.get_str("exam_reason", default="Assessment in progress. Buddy assistant is temporarily paused."),
            "test_auto_lock_enabled": SystemSetting.get_bool("test_auto_lock_enabled", default=True),
            "test_buffer_before_minutes": SystemSetting.get_int("test_buffer_before_minutes", default=15),
            "test_buffer_after_minutes": SystemSetting.get_int("test_buffer_after_minutes", default=15),
            "active_test_lock": active_test_lock,
            "voice_enabled": SystemSetting.get_bool("voice_enabled", default=True),
            "voice_tts_enabled": SystemSetting.get_bool("voice_tts_enabled", default=True),
            "screen_help_enabled": SystemSetting.get_bool("screen_help_enabled", default=True),
            "ide_tracking_enabled": SystemSetting.get_bool("ide_tracking_enabled", default=True),
            "llm_model": SystemSetting.get_str("llm_model", default="llama3.2:3b"),
            "llm_temperature": SystemSetting.get_float("llm_temperature", default=0.3),
            "llm_system_prompt": SystemSetting.get_str("llm_system_prompt", default="Encourage trainees to think logically. Guide with hints and explanations before solutions."),
            "max_queries_per_hour": SystemSetting.get_int("max_queries_per_hour", default=30),
            "rag_ignite_enabled": SystemSetting.get_bool("rag_ignite_enabled", default=True),
            "rag_general_enabled": SystemSetting.get_bool("rag_general_enabled", default=True),
            "rag_personal_enabled": SystemSetting.get_bool("rag_personal_enabled", default=True),
            "blocked_keywords": SystemSetting.get_str("blocked_keywords", default="exam leak, test solutions, cheat, bypass policy"),
        })

    data = request.data
    user = request.user

    # Master Buddy toggle
    if "enabled" in data:
        enabled_val = bool(data["enabled"])
        SystemSetting.set_bool("buddy_enabled", enabled_val, user=user)
        policy.set_blocked(not enabled_val, reason="The assistant has been disabled by the administrator." if not enabled_val else "")
        ExamControl.objects.all().update(exam_mode=not enabled_val)

    # Exam Mode toggle & reason
    if "exam_mode" in data:
        exam_mode_val = bool(data["exam_mode"])
        SystemSetting.set_bool("exam_mode", exam_mode_val, user=user)
        if exam_mode_val:
            reason = data.get("exam_reason", "Assessment in progress. Buddy assistant is temporarily paused.")
            policy.set_blocked(True, reason=reason)
            ExamControl.objects.all().update(exam_mode=True)
        else:
            is_enabled = SystemSetting.get_bool("buddy_enabled", default=True)
            policy.set_blocked(not is_enabled, reason="")
            ExamControl.objects.all().update(exam_mode=False)

    if "exam_reason" in data:
        SystemSetting.set_str("exam_reason", str(data["exam_reason"]).strip(), user=user)

    # Automated Test Lockdown Settings
    if "test_auto_lock_enabled" in data:
        SystemSetting.set_bool("test_auto_lock_enabled", bool(data["test_auto_lock_enabled"]), user=user)
    if "test_buffer_before_minutes" in data:
        try:
            SystemSetting.set_int("test_buffer_before_minutes", int(data["test_buffer_before_minutes"]), user=user)
        except (ValueError, TypeError):
            pass
    if "test_buffer_after_minutes" in data:
        try:
            SystemSetting.set_int("test_buffer_after_minutes", int(data["test_buffer_after_minutes"]), user=user)
        except (ValueError, TypeError):
            pass

    # Feature switches
    if "voice_enabled" in data:
        SystemSetting.set_bool("voice_enabled", bool(data["voice_enabled"]), user=user)
    if "voice_tts_enabled" in data:
        SystemSetting.set_bool("voice_tts_enabled", bool(data["voice_tts_enabled"]), user=user)
    if "screen_help_enabled" in data:
        SystemSetting.set_bool("screen_help_enabled", bool(data["screen_help_enabled"]), user=user)
    if "ide_tracking_enabled" in data:
        SystemSetting.set_bool("ide_tracking_enabled", bool(data["ide_tracking_enabled"]), user=user)

    # AI / LLM configuration
    if "llm_model" in data:
        SystemSetting.set_str("llm_model", str(data["llm_model"]).strip(), user=user)
    if "llm_temperature" in data:
        try:
            SystemSetting.set_float("llm_temperature", float(data["llm_temperature"]), user=user)
        except (ValueError, TypeError):
            pass
    if "llm_system_prompt" in data:
        SystemSetting.set_str("llm_system_prompt", str(data["llm_system_prompt"]).strip(), user=user)

    # Safety & RAG
    if "max_queries_per_hour" in data:
        try:
            SystemSetting.set_int("max_queries_per_hour", int(data["max_queries_per_hour"]), user=user)
        except (ValueError, TypeError):
            pass
    if "rag_ignite_enabled" in data:
        val = bool(data["rag_ignite_enabled"])
        SystemSetting.set_bool("rag_ignite_enabled", val, user=user)
        policy.set_capability("kb.ignite", val)
    if "rag_general_enabled" in data:
        val = bool(data["rag_general_enabled"])
        SystemSetting.set_bool("rag_general_enabled", val, user=user)
        policy.set_capability("kb.general", val)
    if "rag_personal_enabled" in data:
        SystemSetting.set_bool("rag_personal_enabled", bool(data["rag_personal_enabled"]), user=user)
    if "blocked_keywords" in data:
        SystemSetting.set_str("blocked_keywords", str(data["blocked_keywords"]).strip(), user=user)

    notify_policy_update()

    master_enabled = SystemSetting.get_bool("buddy_enabled", default=not policy.is_blocked())
    exam_mode = SystemSetting.get_bool("exam_mode", default=False)
    return Response({
        "success": True,
        "enabled": master_enabled,
        "exam_mode": exam_mode,
        "exam_reason": SystemSetting.get_str("exam_reason", default="Assessment in progress. Buddy assistant is temporarily paused."),
        "voice_enabled": SystemSetting.get_bool("voice_enabled", default=True),
        "voice_tts_enabled": SystemSetting.get_bool("voice_tts_enabled", default=True),
        "screen_help_enabled": SystemSetting.get_bool("screen_help_enabled", default=True),
        "ide_tracking_enabled": SystemSetting.get_bool("ide_tracking_enabled", default=True),
        "llm_model": SystemSetting.get_str("llm_model", default="llama3.2:3b"),
        "llm_temperature": SystemSetting.get_float("llm_temperature", default=0.3),
        "llm_system_prompt": SystemSetting.get_str("llm_system_prompt", default="Encourage trainees to think logically. Guide with hints and explanations before solutions."),
        "max_queries_per_hour": SystemSetting.get_int("max_queries_per_hour", default=30),
        "rag_ignite_enabled": SystemSetting.get_bool("rag_ignite_enabled", default=True),
        "rag_general_enabled": SystemSetting.get_bool("rag_general_enabled", default=True),
        "rag_personal_enabled": SystemSetting.get_bool("rag_personal_enabled", default=True),
        "blocked_keywords": SystemSetting.get_str("blocked_keywords", default="exam leak, test solutions, cheat, bypass policy"),
        "message": "Buddy settings updated successfully",
    })
