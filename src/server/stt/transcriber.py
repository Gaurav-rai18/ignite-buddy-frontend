"""
Server-side Speech-to-Text implementation based on SpeechRecognition.

Follows the reference architecture from speech.py, supporting only:
  1. 'google'          - Google Speech Recognition API (.recognize_google())
  2. 'faster_whisper'  - Faster-Whisper local model (.recognize_faster_whisper())
  3. 'vosk'            - Vosk local model (.recognize_vosk())

Operates on finished one-shot audio recordings sent from the client without streaming.
Maintains compatibility with corporate proxies and Zscaler by using standard
SpeechRecognition network invocation.
"""
from __future__ import annotations

import io
import json
import logging
import os
import wave
from typing import Any

import speech_recognition as sr

log = logging.getLogger(__name__)

# Backend mapping for the three supported engines
BACKENDS: dict[str, str] = {
    "google": "recognize_google",
    "faster_whisper": "recognize_faster_whisper",
    "vosk": "recognize_vosk",
}

ALLOWED_ENGINES = set(BACKENDS.keys())

INSTALL_HINTS = {
    "faster_whisper": "pip install faster-whisper",
    "vosk": "pip install vosk",
}


class SttError(Exception):
    """Base exception for speech recognition errors reported to the trainee."""


class SttUnavailable(SttError):
    """Raised when the speech service is unreachable due to network, proxy, or server issues."""


def _to_audio_data(audio_bytes: bytes, sample_rate: int = 16000, sample_width: int = 2) -> sr.AudioData:
    """Converts raw PCM16 or WAV bytes to sr.AudioData."""
    if not audio_bytes:
        raise ValueError("Empty audio payload")

    # If the payload is a WAV file (starts with RIFF header)
    if audio_bytes.startswith(b"RIFF") and len(audio_bytes) > 44:
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                rate = wf.getframerate()
                width = wf.getsampwidth()
                frames = wf.readframes(wf.getnframes())
                return sr.AudioData(frames, rate, width)
        except Exception as e:
            log.warning("Could not parse WAV header, treating as raw PCM: %s", e)

    return sr.AudioData(audio_bytes, sample_rate, sample_width)


def transcribe_audio(
    audio: sr.AudioData,
    backend: str = "google",
    lang: str = "en-US",
    **backend_kwargs: Any,
) -> str:
    """
    Transcribes an AudioData object using the configured SpeechRecognition backend.
    Direct implementation based on speech.py reference.
    """
    b = backend.lower()
    method_name = BACKENDS.get(b)
    if not method_name:
        raise ValueError(
            f"Unknown STT backend '{backend}'. Only 'google', 'faster_whisper', and 'vosk' "
            f"are supported via SpeechRecognition."
        )

    recognizer = sr.Recognizer()
    method = getattr(recognizer, method_name, None)
    if method is None:
        raise RuntimeError(f"speech_recognition.Recognizer has no method '{method_name}'.")

    # Build backend-specific arguments
    kwargs = dict(backend_kwargs)
    if b == "google":
        kwargs.setdefault("language", lang)
    elif b == "faster_whisper":
        whisper_model = os.getenv("ASSISTANT_WHISPER_MODEL", "base")
        kwargs.setdefault("model", whisper_model)
        short_lang = lang.split("-")[0] if "-" in lang else lang
        kwargs.setdefault("language", short_lang)
    elif b == "vosk":
        pass

    try:
        result = method(audio, **kwargs)
        if isinstance(result, tuple):
            result = result[0]
        if isinstance(result, dict):
            result = result.get("text") or (result.get("alternative") or [{}])[0].get("transcript", "")
        return str(result or "").strip()
    except sr.UnknownValueError:
        # Intelligible speech not detected (silence, cough, background noise)
        return ""
    except sr.RequestError as e:
        raise SttUnavailable(
            f"Speech service error ({b}): {e}. Check internet/proxy and corporate Zscaler connection."
        ) from e
    except ImportError as e:
        hint = INSTALL_HINTS.get(b, "pip install SpeechRecognition")
        raise SttError(f"STT engine '{b}' requires an additional package ({hint}): {e}") from e
    except Exception as e:
        raise SttError(f"STT engine '{b}' failed ({type(e).__name__}): {e}") from e


def transcribe_pcm(
    pcm_bytes: bytes,
    backend: str = "google",
    lang: str = "en-US",
    sample_rate: int = 16000,
    sample_width: int = 2,
    **backend_kwargs: Any,
) -> str:
    """Transcribes raw PCM bytes using speech_recognition."""
    if not pcm_bytes:
        return ""
    audio = _to_audio_data(pcm_bytes, sample_rate, sample_width)
    return transcribe_audio(audio, backend=backend, lang=lang, **backend_kwargs)


class Transcriber:
    """
    Central speech-to-text transcriber operating on the backend server.
    Accepts full recorded audio in one shot and transcribes it using SpeechRecognition.
    """

    def __init__(
        self,
        engine: str = "google",
        options: dict | None = None,
        lang: str = "en-US",
    ):
        engine_clean = str(engine or "google").strip().lower()
        if engine_clean not in ALLOWED_ENGINES:
            raise ValueError(
                f"Unknown STT engine '{engine}'. Only 'google', 'faster_whisper', and 'vosk' "
                f"are supported via SpeechRecognition."
            )

        self.engine = engine_clean
        self.lang = lang or "en-US"
        self.options = options or {}

    def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribes full audio recording in one shot."""
        if not audio_bytes:
            return ""
        return transcribe_pcm(
            audio_bytes,
            backend=self.engine,
            lang=self.lang,
            **self.options,
        )


def build_from_config(cfg=None) -> Transcriber:
    """Instantiates a Transcriber configured from server settings."""
    if cfg is None:
        from server import config as cfg

    try:
        raw_opts = getattr(cfg, "STT_OPTIONS", "{}")
        options = json.loads(raw_opts) if isinstance(raw_opts, str) else (raw_opts or {})
        if not isinstance(options, dict):
            raise ValueError
    except Exception:
        raise ValueError("STT_OPTIONS must be a valid JSON object string, e.g. '{\"model\": \"small.en\"}'")

    engine = getattr(cfg, "STT_ENGINE", "google")
    lang = getattr(cfg, "SPEECH_LANG", "en-US")

    return Transcriber(
        engine=engine,
        options=options,
        lang=lang,
    )
