"""
text_to_speech.py - Thread-safe pyttsx3 TTS engine wrapper.

pyttsx3 must run in its own thread because it uses platform-native
COM objects (Windows SAPI) that conflict with Qt's event loop.
"""

import threading
import queue
from typing import Callable
from app.utils import get_logger

logger = get_logger(__name__)


class TTSEngine:
    """
    Singleton-style TTS engine that runs pyttsx3 in a dedicated
    background thread, processing requests from a queue.
    """

    def __init__(self):
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._speaking = False
        self._enabled = True
        self._rate = 175
        self._volume = 0.9
        self._thread = threading.Thread(target=self._run, daemon=True, name="TTS-Thread")
        self._thread.start()
        self._on_start_cb: Callable | None = None
        self._on_done_cb: Callable | None = None

    # ── Configuration ─────────────────────────────────────────────────────────

    def set_rate(self, rate: int):
        self._rate = rate

    def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, volume))

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

    def set_callbacks(self, on_start: Callable = None, on_done: Callable = None):
        self._on_start_cb = on_start
        self._on_done_cb = on_done

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    # ── Public interface ──────────────────────────────────────────────────────

    def speak(self, text: str):
        """Queue text to be spoken (non-blocking)."""
        if self._enabled and text.strip():
            self._queue.put(text)
            logger.debug("TTS queued: %r", text[:60])

    def stop(self):
        """Clear the queue (cannot interrupt mid-sentence easily)."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    # ── Internal ──────────────────────────────────────────────────────────────

    def _run(self):
        """Background thread: initialise pyttsx3 and process the queue."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            engine.setProperty("volume", self._volume)
        except Exception as e:
            logger.error("TTS init failed: %s", e)
            return

        while True:
            text = self._queue.get()
            if text is None:
                break  # shutdown signal

            try:
                # Update properties in case they changed
                engine.setProperty("rate", self._rate)
                engine.setProperty("volume", self._volume)

                self._speaking = True
                if self._on_start_cb:
                    self._on_start_cb()

                engine.say(text)
                engine.runAndWait()

            except Exception as e:
                logger.error("TTS speak error: %s", e)
            finally:
                self._speaking = False
                if self._on_done_cb:
                    self._on_done_cb()
                self._queue.task_done()

    def shutdown(self):
        self._queue.put(None)
