"""
settings.py - Application settings backed by QSettings (INI file).
"""

from PySide6.QtCore import QSettings
from app.utils import get_logger, PROJECT_ROOT

logger = get_logger(__name__)

SETTINGS_FILE = str(PROJECT_ROOT / "data" / "vocadesk_settings.ini")


class AppSettings:
    """Thin wrapper around QSettings for type-safe access."""

    _defaults = {
        "assistant_name": "VocaDesk",
        "voice_enabled": True,
        "speech_rate": 175,
        "volume": 0.9,
        "theme": "dark",
        "microphone_index": -1,   # -1 = system default
        "ai_mode_enabled": False,
    }

    def __init__(self):
        self._qs = QSettings(SETTINGS_FILE, QSettings.Format.IniFormat)
        logger.debug("Settings loaded from %s", SETTINGS_FILE)

    # ── Generic access ────────────────────────────────────────────────────────

    def get(self, key: str):
        default = self._defaults.get(key)
        value = self._qs.value(key, default)
        # QSettings stores everything as strings on Windows
        if isinstance(default, bool):
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        if isinstance(default, int):
            return int(value)
        if isinstance(default, float):
            return float(value)
        return value

    def set(self, key: str, value):
        self._qs.setValue(key, value)
        self._qs.sync()
        logger.debug("Setting saved: %s = %r", key, value)

    # ── Convenience properties ────────────────────────────────────────────────

    @property
    def assistant_name(self) -> str:
        return self.get("assistant_name")

    @property
    def voice_enabled(self) -> bool:
        return self.get("voice_enabled")

    @voice_enabled.setter
    def voice_enabled(self, v: bool):
        self.set("voice_enabled", v)

    @property
    def speech_rate(self) -> int:
        return self.get("speech_rate")

    @speech_rate.setter
    def speech_rate(self, v: int):
        self.set("speech_rate", v)

    @property
    def volume(self) -> float:
        return self.get("volume")

    @volume.setter
    def volume(self, v: float):
        self.set("volume", v)

    @property
    def microphone_index(self) -> int:
        return self.get("microphone_index")

    @microphone_index.setter
    def microphone_index(self, v: int):
        self.set("microphone_index", v)

    @property
    def ai_mode_enabled(self) -> bool:
        return self.get("ai_mode_enabled")

    @ai_mode_enabled.setter
    def ai_mode_enabled(self, v: bool):
        self.set("ai_mode_enabled", v)

    def all_settings(self) -> dict:
        result = {}
        for key, default in self._defaults.items():
            result[key] = self.get(key)
        return result
