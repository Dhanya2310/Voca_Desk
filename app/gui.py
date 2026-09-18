"""
gui.py - Main application window for VocaDesk.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLineEdit, QPushButton, QLabel, QDialog,
    QFormLayout, QSlider, QCheckBox, QComboBox, QSpinBox,
    QDialogButtonBox, QSizePolicy, QFrame, QSystemTrayIcon, QMenu,
    QGraphicsDropShadowEffect, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import (
    QFont, QIcon, QColor, QPalette, QAction, QKeySequence, QShortcut,
)

from app.widgets import ChatBubble, MicButton, StatusBadge, PALETTE
from app.assistant import AssistantWorker, TextCommandWorker
from app.speech_to_text import SpeechToText
from app.text_to_speech import TTSEngine
from app.command_processor import CommandProcessor
from app.ai_client import AIClient
from app.settings import AppSettings
from app.reminders import ReminderChecker
from app import database as db
from app.utils import get_logger

logger = get_logger(__name__)


# ── Stylesheet ────────────────────────────────────────────────────────────────

DARK_QSS = f"""
QMainWindow, QWidget#central {{
    background: {PALETTE['bg']};
}}
QScrollArea, QScrollArea > QWidget > QWidget {{
    background: {PALETTE['bg']};
    border: none;
}}
QScrollBar:vertical {{
    background: {PALETTE['surface']};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {PALETTE['surface2']};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QLineEdit {{
    background: {PALETTE['surface2']};
    color: {PALETTE['text']};
    border: 1.5px solid {PALETTE['surface']};
    border-radius: 22px;
    padding: 10px 18px;
    font-size: 14px;
    selection-background-color: {PALETTE['accent']};
}}
QLineEdit:focus {{
    border: 1.5px solid {PALETTE['accent']};
}}
QPushButton#send_btn {{
    background: {PALETTE['accent']};
    color: white;
    border: none;
    border-radius: 20px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#send_btn:hover {{
    background: {PALETTE['accent_glow']};
}}
QPushButton#send_btn:pressed {{
    background: #4A5FEF;
}}
QPushButton#settings_btn, QPushButton#clear_btn {{
    background: {PALETTE['surface2']};
    color: {PALETTE['text_muted']};
    border: none;
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
}}
QPushButton#settings_btn:hover, QPushButton#clear_btn:hover {{
    background: {PALETTE['surface']};
    color: {PALETTE['text']};
}}
QLabel#app_name {{
    color: {PALETTE['text']};
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel#tagline {{
    color: {PALETTE['text_muted']};
    font-size: 11px;
    font-weight: 400;
}}
QFrame#divider {{
    background: {PALETTE['surface2']};
    max-height: 1px;
    min-height: 1px;
}}
/* Settings dialog */
QDialog {{
    background: {PALETTE['surface']};
}}
QLabel {{
    color: {PALETTE['text']};
}}
QSlider::groove:horizontal {{
    background: {PALETTE['surface2']};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {PALETTE['accent']};
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
}}
QSlider::sub-page:horizontal {{
    background: {PALETTE['accent']};
    border-radius: 2px;
}}
QCheckBox {{
    color: {PALETTE['text']};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {PALETTE['surface2']};
    background: {PALETTE['surface']};
}}
QCheckBox::indicator:checked {{
    background: {PALETTE['accent']};
    border-color: {PALETTE['accent']};
}}
QComboBox {{
    background: {PALETTE['surface2']};
    color: {PALETTE['text']};
    border: 1px solid {PALETTE['surface']};
    border-radius: 8px;
    padding: 6px 12px;
}}
QComboBox::drop-down {{
    border: none;
}}
QSpinBox {{
    background: {PALETTE['surface2']};
    color: {PALETTE['text']};
    border: 1px solid {PALETTE['surface']};
    border-radius: 8px;
    padding: 6px 8px;
}}
QDialogButtonBox QPushButton {{
    background: {PALETTE['accent']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
}}
QDialogButtonBox QPushButton:hover {{
    background: {PALETTE['accent_glow']};
}}
"""


# ── Settings Dialog ───────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    settings_changed = Signal()

    def __init__(self, app_settings: AppSettings, stt: SpeechToText, parent=None):
        super().__init__(parent)
        self._settings = app_settings
        self._stt = stt
        self.setWindowTitle("VocaDesk Settings")
        self.setMinimumWidth(420)
        self.setStyleSheet(DARK_QSS)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet(f"color:{PALETTE['text']}; font-size:18px; font-weight:700;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Voice enabled
        self._voice_cb = QCheckBox()
        self._voice_cb.setChecked(self._settings.voice_enabled)
        form.addRow("Enable voice output:", self._voice_cb)

        # Speech rate
        self._rate_slider = QSlider(Qt.Orientation.Horizontal)
        self._rate_slider.setRange(80, 300)
        self._rate_slider.setValue(self._settings.speech_rate)
        self._rate_lbl = QLabel(str(self._settings.speech_rate))
        self._rate_slider.valueChanged.connect(
            lambda v: self._rate_lbl.setText(str(v))
        )
        rate_row = QHBoxLayout()
        rate_row.addWidget(self._rate_slider)
        rate_row.addWidget(self._rate_lbl)
        form.addRow("Speech rate:", rate_row)

        # Volume
        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(int(self._settings.volume * 100))
        self._vol_lbl = QLabel(f"{int(self._settings.volume * 100)}%")
        self._vol_slider.valueChanged.connect(
            lambda v: self._vol_lbl.setText(f"{v}%")
        )
        vol_row = QHBoxLayout()
        vol_row.addWidget(self._vol_slider)
        vol_row.addWidget(self._vol_lbl)
        form.addRow("TTS volume:", vol_row)

        # Microphone
        self._mic_combo = QComboBox()
        self._mic_combo.addItem("System Default", -1)
        try:
            mics = self._stt.list_microphones()
            for i, name in enumerate(mics):
                self._mic_combo.addItem(name, i)
            saved_idx = self._settings.microphone_index
            for j in range(self._mic_combo.count()):
                if self._mic_combo.itemData(j) == saved_idx:
                    self._mic_combo.setCurrentIndex(j)
                    break
        except Exception:
            pass
        form.addRow("Microphone:", self._mic_combo)

        # AI mode
        self._ai_cb = QCheckBox()
        self._ai_cb.setChecked(self._settings.ai_mode_enabled)
        form.addRow("Enable AI mode:", self._ai_cb)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save_and_accept(self):
        self._settings.set("voice_enabled", self._voice_cb.isChecked())
        self._settings.set("speech_rate", self._rate_slider.value())
        self._settings.set("volume", self._vol_slider.value() / 100.0)
        self._settings.set("microphone_index", self._mic_combo.currentData())
        self._settings.set("ai_mode_enabled", self._ai_cb.isChecked())
        self.settings_changed.emit()
        self.accept()


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # Core services
        self._settings  = AppSettings()
        self._stt       = SpeechToText()
        self._tts       = TTSEngine()
        self._ai        = AIClient()
        self._processor = CommandProcessor(
            ai_client=self._ai if self._settings.ai_mode_enabled else None
        )

        # Apply settings to services
        self._apply_settings()

        # DB init
        db.init_db()

        # Window chrome
        self.setWindowTitle("VocaDesk")
        self.setMinimumSize(700, 560)
        self.resize(820, 660)
        self.setStyleSheet(DARK_QSS)

        # Build UI
        self._build_ui()
        self._setup_tray()
        self._setup_reminders()

        # Worker ref (prevent GC)
        self._worker: AssistantWorker | None = None

        # Welcome message
        QTimer.singleShot(200, self._show_welcome)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_divider())
        root.addWidget(self._build_chat_area(), stretch=1)
        root.addWidget(self._build_divider())
        root.addWidget(self._build_bottom_bar())

        # Keyboard shortcut: Enter in text box sends command
        shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        shortcut.activated.connect(self._on_send_text)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet(f"background:{PALETTE['surface']};")

        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)

        # Logo area
        logo_area = QVBoxLayout()
        logo_area.setSpacing(1)
        name_lbl = QLabel("VocaDesk")
        name_lbl.setObjectName("app_name")
        tagline = QLabel("Your intelligent desktop assistant")
        tagline.setObjectName("tagline")
        logo_area.addWidget(name_lbl)
        logo_area.addWidget(tagline)

        hl.addLayout(logo_area)
        hl.addStretch()

        # Status badge
        self._status_badge = StatusBadge()
        hl.addWidget(self._status_badge)
        hl.addSpacing(16)

        # Settings button
        settings_btn = QPushButton("⚙  Settings")
        settings_btn.setObjectName("settings_btn")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self._open_settings)
        hl.addWidget(settings_btn)

        # Clear button
        clear_btn = QPushButton("🗑  Clear")
        clear_btn.setObjectName("clear_btn")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_chat)
        hl.addWidget(clear_btn)

        return header

    def _build_divider(self) -> QFrame:
        d = QFrame()
        d.setObjectName("divider")
        return d

    def _build_chat_area(self) -> QScrollArea:
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._chat_container = QWidget()
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(0, 12, 0, 12)
        self._chat_layout.setSpacing(4)
        self._chat_layout.addStretch()

        self._scroll.setWidget(self._chat_container)
        return self._scroll

    def _build_bottom_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(88)
        bar.setStyleSheet(f"background:{PALETTE['surface']};")

        hl = QHBoxLayout(bar)
        hl.setContentsMargins(20, 12, 20, 12)
        hl.setSpacing(12)

        # Text input
        self._text_input = QLineEdit()
        self._text_input.setPlaceholderText("Type a command or question… (Enter to send)")
        self._text_input.returnPressed.connect(self._on_send_text)
        hl.addWidget(self._text_input, stretch=1)

        # Send button
        send_btn = QPushButton("Send")
        send_btn.setObjectName("send_btn")
        send_btn.setFixedSize(72, 42)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self._on_send_text)
        hl.addWidget(send_btn)

        # Mic button
        self._mic_btn = MicButton()
        self._mic_btn.clicked.connect(self._on_mic_clicked)
        hl.addWidget(self._mic_btn)

        return bar

    # ── Tray icon ─────────────────────────────────────────────────────────────

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip("VocaDesk")
        menu = QMenu()
        show_act = QAction("Show VocaDesk", self)
        show_act.triggered.connect(self.show)
        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(QApplication.instance().quit)
        menu.addAction(show_act)
        menu.addSeparator()
        menu.addAction(quit_act)
        self._tray.setContextMenu(menu)
        self._tray.show()
        self._tray.activated.connect(
            lambda r: self.show() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )

    # ── Reminders ─────────────────────────────────────────────────────────────

    def _setup_reminders(self):
        self._reminder_checker = ReminderChecker(self)
        self._reminder_checker.reminder_due.connect(self._on_reminder_due)
        self._reminder_checker.start()

    def _on_reminder_due(self, task: str):
        msg = f"Reminder: {task}"
        self._add_assistant_bubble(f"⏰ {msg}")
        self._tts.speak(msg)
        if hasattr(self, "_tray"):
            self._tray.showMessage("VocaDesk Reminder", task, QSystemTrayIcon.MessageIcon.Information, 5000)

    # ── Chat helpers ──────────────────────────────────────────────────────────

    def _add_user_bubble(self, text: str):
        bubble = ChatBubble(text, sender="user")
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _add_assistant_bubble(self, text: str):
        bubble = ChatBubble(text, sender="assistant")
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear_chat(self):
        while self._chat_layout.count() > 1:
            item = self._chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_welcome(self):
        self._add_assistant_bubble(
            "Hello! I'm VocaDesk, your desktop assistant.\n"
            "Press the 🎤 button or type a command below to get started.\n"
            "Say 'help' to see what I can do."
        )

    # ── Settings ──────────────────────────────────────────────────────────────

    def _open_settings(self):
        dlg = SettingsDialog(self._settings, self._stt, self)
        dlg.settings_changed.connect(self._apply_settings)
        dlg.exec()

    def _apply_settings(self):
        self._tts.set_rate(self._settings.speech_rate)
        self._tts.set_volume(self._settings.volume)
        self._tts.set_enabled(self._settings.voice_enabled)
        self._stt.set_microphone_index(self._settings.microphone_index)
        # Rebuild processor with updated AI setting
        if self._settings.ai_mode_enabled and self._ai.is_available:
            self._processor = CommandProcessor(ai_client=self._ai)
        else:
            self._processor = CommandProcessor(ai_client=None)

    # ── Command execution ─────────────────────────────────────────────────────

    def _on_mic_clicked(self):
        if self._worker and self._worker.isRunning():
            return  # already busy

        # Check if microphone is available
        if not self._stt.is_available:
            self._add_assistant_bubble(
                "⚠ Microphone input is unavailable.\n"
                "Please install sounddevice or PyAudio: pip install sounddevice numpy"
            )
            return

        self._set_status("Listening")
        self._mic_btn.set_state("listening")

        self._worker = AssistantWorker(self._stt, self._tts, self._processor, self)
        self._worker.status_changed.connect(self._on_status_changed)
        self._worker.user_text.connect(self._add_user_bubble)
        self._worker.assistant_text.connect(self._add_assistant_bubble)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_send_text(self):
        text = self._text_input.text().strip()
        if not text:
            return
        self._text_input.clear()

        if self._worker and self._worker.isRunning():
            return

        self._add_user_bubble(text)
        self._set_status("Processing")

        self._worker = TextCommandWorker(text, self._tts, self._processor, self)
        self._worker.status_changed.connect(self._on_status_changed)
        self._worker.assistant_text.connect(self._add_assistant_bubble)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_status_changed(self, status: str):
        self._set_status(status)
        if status == "Listening":
            self._mic_btn.set_state("listening")
        elif status == "Processing":
            self._mic_btn.set_state("processing")
        else:
            self._mic_btn.set_state("idle")

    def _on_error(self, msg: str):
        self._add_assistant_bubble(f"⚠ {msg}")
        self._set_status("Error")
        self._mic_btn.set_state("idle")

    def _set_status(self, status: str):
        self._status_badge.set_status(status)

    # ── Window events ─────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._tts.shutdown()
        self._reminder_checker.stop()
        self._reminder_checker.wait(2000)
        event.accept()