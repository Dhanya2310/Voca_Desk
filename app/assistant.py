"""
assistant.py - Orchestrator QThread.

Ties together: STT → CommandProcessor → TTS.
Emits Qt signals so the GUI stays responsive.
"""

from PySide6.QtCore import QThread, Signal
from app.speech_to_text import SpeechToText
from app.text_to_speech import TTSEngine
from app.command_processor import CommandProcessor
from app.ai_client import AIClient
from app.settings import AppSettings
from app.utils import get_logger

logger = get_logger(__name__)


class AssistantWorker(QThread):
    """
    Background worker for a single listen → process → speak cycle.

    Signals:
      status_changed(str)  – 'Listening', 'Processing', 'Speaking', 'Ready', 'Error'
      user_text(str)       – the recognised speech
      assistant_text(str)  – the response text
      error(str)           – friendly error message
    """

    status_changed   = Signal(str)
    user_text        = Signal(str)
    assistant_text   = Signal(str)
    error            = Signal(str)

    def __init__(self, stt: SpeechToText, tts: TTSEngine,
                 processor: CommandProcessor, parent=None):
        super().__init__(parent)
        self._stt = stt
        self._tts = tts
        self._processor = processor

    def run(self):
        # 1. Listen
        self.status_changed.emit("Listening")
        try:
            text = self._stt.listen()
        except RuntimeError as e:
            self.status_changed.emit("Error")
            self.error.emit(str(e))
            return
        except ValueError as e:
            self.status_changed.emit("Error")
            self.error.emit(str(e))
            return
        except Exception as e:
            logger.exception("Unexpected STT error")
            self.status_changed.emit("Error")
            self.error.emit("An unexpected error occurred while listening.")
            return

        self.user_text.emit(text)

        # 2. Process
        self.status_changed.emit("Processing")
        try:
            response = self._processor.process(text)
        except Exception as e:
            logger.exception("Command processing error")
            response = "Something went wrong processing your request."

        self.assistant_text.emit(response)

        # 3. Speak
        self.status_changed.emit("Speaking")
        self._tts.speak(response)

        # Wait briefly so status shows "Speaking" while TTS runs
        import time
        while self._tts.is_speaking:
            time.sleep(0.2)

        self.status_changed.emit("Ready")


class TextCommandWorker(QThread):
    """
    Like AssistantWorker but skips STT — processes a pre-supplied text command.
    """

    status_changed = Signal(str)
    assistant_text = Signal(str)
    error          = Signal(str)

    def __init__(self, text: str, tts: TTSEngine,
                 processor: CommandProcessor, parent=None):
        super().__init__(parent)
        self._text = text
        self._tts = tts
        self._processor = processor

    def run(self):
        self.status_changed.emit("Processing")
        try:
            response = self._processor.process(self._text)
        except Exception as e:
            logger.exception("Text command processing error")
            response = "Something went wrong processing your request."

        self.assistant_text.emit(response)

        self.status_changed.emit("Speaking")
        self._tts.speak(response)

        import time
        while self._tts.is_speaking:
            time.sleep(0.2)

        self.status_changed.emit("Ready")
