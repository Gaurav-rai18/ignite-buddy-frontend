"""
Speech capture and audio listener on the trainee's PC.

Captures audio directly from the system microphone using sounddevice
or speech_recognition.Microphone, calculates live RMS energy levels for the UI meter,
and applies voice activity detection (VAD).

Once recording completes, the raw PCM16 audio bytes are delivered in one shot
to the backend server for speech recognition.
"""
from __future__ import annotations

import logging
import math
import os
import threading
import time
from typing import Callable

import speech_recognition as sr

log = logging.getLogger("speech")

# Audio format defaults
SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2                # 16-bit PCM (2 bytes per sample)
CHANNELS = 1                    # mono
CHUNK_SAMPLES = 1024
ENERGY_THRESHOLD = 300.0        # initial energy threshold
PAUSE_THRESHOLD = 0.8           # seconds of silence after speech before stopping
PHRASE_TIME_LIMIT = 30.0        # max phrase duration in seconds
CALIBRATION_SECONDS = 0.3       # ambient noise learning duration
NO_SPEECH_TIMEOUT = 4.0         # abort if no speech heard within this window


class _Cancelled(Exception):
    pass


class SpeechListener:
    """
    Captures microphone audio directly from the trainee's PC.
    Delivers raw PCM16 bytes in one shot upon completion.
    """

    def __init__(self, backend: str = "google", lang: str = "en-US", **backend_kwargs):
        self.backend = (backend or "google").lower()
        self.lang = lang
        self.backend_kwargs = backend_kwargs
        self._thread: threading.Thread | None = None
        self._cancel = threading.Event()
        self._stop = threading.Event()

    @property
    def active(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(
        self,
        on_audio: Callable[[bytes], None],
        on_error: Callable[[str], None],
        on_level: Callable[[float, bool], None] | None = None,
    ):
        """Begin listening on a background daemon thread."""
        if self.active:
            return
        self._cancel.clear()
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(on_audio, on_error, on_level),
            daemon=True,
            name="speech-listener",
        )
        self._thread.start()

    def stop(self):
        """Signal that speech has ended; wrap up what was recorded."""
        self._stop.set()

    def cancel(self):
        """Abort listening immediately without sending audio."""
        self._cancel.set()
        self._stop.set()

    def _run(self, on_audio, on_error, on_level):
        try:
            pcm_bytes = self._capture_mic(on_level)
        except _Cancelled:
            on_audio(b"")
            return
        except Exception as e:
            on_error(f"Microphone error: {e}")
            return

        if not pcm_bytes or self._cancel.is_set():
            on_audio(b"")
            return

        on_audio(pcm_bytes)

    def _capture_mic(self, on_level) -> bytes:
        """Capture from microphone using sounddevice (or speech_recognition.Microphone)."""
        try:
            import sounddevice as sd
            return self._capture_sounddevice(sd, on_level)
        except ImportError:
            pass

        return self._capture_sr_microphone(on_level)

    def _capture_sounddevice(self, sd, on_level) -> bytes:
        frames: list[bytes] = []
        started = time.monotonic()
        speech_detected = False
        silent_since = started
        threshold = ENERGY_THRESHOLD
        calibration_end = started + CALIBRATION_SECONDS
        calib_energies: list[float] = []

        with sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=CHUNK_SAMPLES,
            channels=CHANNELS,
            dtype="int16",
        ) as stream:
            while not self._cancel.is_set():
                if self._stop.is_set():
                    break

                elapsed = time.monotonic() - started
                if elapsed >= PHRASE_TIME_LIMIT:
                    break
                if not speech_detected and elapsed >= NO_SPEECH_TIMEOUT:
                    break

                chunk, overflow = stream.read(CHUNK_SAMPLES)
                if not chunk:
                    continue

                b = bytes(chunk)
                energy = _rms_energy(b)

                # Ambient calibration phase
                now = time.monotonic()
                if now < calibration_end:
                    calib_energies.append(energy)
                    threshold = max(ENERGY_THRESHOLD, (sum(calib_energies) / len(calib_energies)) * 2.5)
                    continue

                frames.append(b)

                speaking = energy > threshold
                if speaking:
                    speech_detected = True
                    silent_since = now
                elif speech_detected and (now - silent_since) >= PAUSE_THRESHOLD:
                    break

                if on_level:
                    level = min(1.0, max(0.0, math.log1p(energy) / 10.0))
                    on_level(level, speaking)

        if self._cancel.is_set():
            raise _Cancelled()
        return b"".join(frames)

    def _capture_sr_microphone(self, on_level) -> bytes:
        """Fallback mic capture using speech_recognition.Microphone."""
        if self._cancel.is_set() or self._stop.is_set():
            return b""
        r = sr.Recognizer()
        r.pause_threshold = PAUSE_THRESHOLD
        r.energy_threshold = ENERGY_THRESHOLD
        r.dynamic_energy_threshold = True

        try:
            with sr.Microphone(sample_rate=SAMPLE_RATE) as source:
                r.adjust_for_ambient_noise(source, duration=CALIBRATION_SECONDS)
                if self._cancel.is_set() or self._stop.is_set():
                    raise _Cancelled()
                audio = r.listen(source, timeout=NO_SPEECH_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT)
                if self._cancel.is_set():
                    raise _Cancelled()
                return audio.get_raw_data()
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return b""


def _rms_energy(chunk: bytes) -> float:
    """Calculate RMS energy of 16-bit little-endian mono PCM chunk."""
    import struct
    n = len(chunk) // 2
    if n == 0:
        return 0.0
    samples = struct.unpack(f"<{n}h", chunk)
    return math.sqrt(sum(s * s for s in samples) / n)

