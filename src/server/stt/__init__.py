"""
Server-side Speech-to-Text module.

Provides audio transcription on the central assistant server for client devices,
supporting only 'google', 'faster_whisper', and 'vosk' via Python's SpeechRecognition.
"""
from .transcriber import Transcriber, SttError, SttUnavailable, build_from_config

__all__ = ["Transcriber", "SttError", "SttUnavailable", "build_from_config"]

