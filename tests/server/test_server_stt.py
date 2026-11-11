"""
Unit tests for the backend server Speech-to-Text (STT) implementation.
Verifies that:
  - Only 'google', 'faster_whisper', and 'vosk' are supported via SpeechRecognition.
  - Proxy and corporate Zscaler settings are configured.
  - One-shot audio transcription produces expected results and error mappings.
"""
import struct
import pytest
import speech_recognition as sr

from server.stt.transcriber import (
    ALLOWED_ENGINES,
    SttError,
    SttUnavailable,
    Transcriber,
    build_from_config,
    transcribe_pcm,
    transcribe_audio,
)

ONE_SECOND = struct.pack("<" + "h" * 16000, *([3000, -3000] * 8000))


def test_only_three_engines_allowed():
    assert ALLOWED_ENGINES == {"google", "faster_whisper", "vosk"}

    # Disallowed engines raise ValueError
    for bad in ["phonon", "whisper", "sphinx", "openai", "azure", "custom"]:
        with pytest.raises(ValueError, match="Only 'google', 'faster_whisper', and 'vosk'"):
            Transcriber(bad)


def test_google_engine_transcription(monkeypatch):
    seen = {}

    def fake_google(self, audio, **kw):
        seen["audio"] = audio
        seen["kw"] = kw
        return "what is the leave policy"

    monkeypatch.setattr(sr.Recognizer, "recognize_google", fake_google)
    t = Transcriber("google", lang="en-US")
    res = t.transcribe(ONE_SECOND)

    assert res == "what is the leave policy"
    assert seen["kw"] == {"language": "en-US"}
    assert seen["audio"].sample_rate == 16000
    assert seen["audio"].sample_width == 2


def test_faster_whisper_engine_transcription(monkeypatch):
    calls = []

    def fake_fw(self, audio, **kw):
        calls.append(kw)
        return "open chrome"

    monkeypatch.setattr(sr.Recognizer, "recognize_faster_whisper", fake_fw)
    cfg = type("C", (), {
        "STT_ENGINE": "faster_whisper",
        "STT_OPTIONS": '{"model": "small.en"}',
        "SPEECH_LANG": "en-US",
        "STT_PROXY": "",
        "LLM_CA_BUNDLE": "",
        "LLM_USE_SYSTEM_CERTS": True,
    })
    t = build_from_config(cfg)
    assert t.transcribe(ONE_SECOND) == "open chrome"
    assert calls[0]["language"] == "en"
    assert calls[0]["model"] == "small.en"


def test_vosk_engine_transcription(monkeypatch):
    calls = []

    def fake_vosk(self, audio, **kw):
        calls.append(kw)
        return "list files in desktop"

    monkeypatch.setattr(sr.Recognizer, "recognize_vosk", fake_vosk)
    t = Transcriber("vosk")
    assert t.transcribe(ONE_SECOND) == "list files in desktop"
    assert len(calls) == 1


def test_empty_or_unintelligible_speech(monkeypatch):
    def fail_unknown(self, audio, **kw):
        raise sr.UnknownValueError()

    monkeypatch.setattr(sr.Recognizer, "recognize_google", fail_unknown)
    t = Transcriber("google")
    assert t.transcribe(ONE_SECOND) == ""


def test_zscaler_proxy_network_error_reporting(monkeypatch):
    def fail_request(self, audio, **kw):
        raise sr.RequestError("recognition request failed: 407 Proxy Authentication Required")

    monkeypatch.setattr(sr.Recognizer, "recognize_google", fail_request)
    t = Transcriber("google")

    with pytest.raises(SttUnavailable, match="Zscaler"):
        t.transcribe(ONE_SECOND)


def test_missing_package_error_reporting(monkeypatch):
    def fail_import(self, audio, **kw):
        raise ImportError("No module named 'vosk'")

    monkeypatch.setattr(sr.Recognizer, "recognize_vosk", fail_import)
    t = Transcriber("vosk")

    with pytest.raises(SttError, match="pip install vosk"):
        t.transcribe(ONE_SECOND)


def test_transcribe_pcm_helper(monkeypatch):
    monkeypatch.setattr(sr.Recognizer, "recognize_google", lambda self, a, **kw: "test pcm transcription")
    res = transcribe_pcm(ONE_SECOND, backend="google")
    assert res == "test pcm transcription"

