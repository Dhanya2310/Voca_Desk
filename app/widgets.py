"""
widgets.py - Custom PySide6 widgets: ChatBubble, MicButton, StatusBadge.
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy,
    QPushButton, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, Property, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QRadialGradient

# ── Colour palette ─────────────────────────────────────────────────────────────

PALETTE = {
    "bg":          "#0F1117",
    "surface":     "#1A1D27",
    "surface2":    "#252836",
    "user_bubble": "#2E3A6E",
    "bot_bubble":  "#1E2535",
    "accent":      "#5C6FFF",
    "accent_glow": "#7B8FFF",
    "text":        "#E8EAF0",
    "text_muted":  "#8B90A7",
    "success":     "#4CAF82",
    "warning":     "#F59E0B",
    "error":       "#EF4444",
    "listening":   "#EF4444",
    "processing":  "#F59E0B",
    "speaking":    "#4CAF82",
    "ready":       "#5C6FFF",
}


# ── Status badge ──────────────────────────────────────────────────────────────

class StatusBadge(QWidget):
    """A small coloured dot + label showing the current assistant status."""

    STATUS_COLORS = {
        "Ready":      PALETTE["ready"],
        "Listening":  PALETTE["listening"],
        "Processing": PALETTE["processing"],
        "Speaking":   PALETTE["speaking"],
        "Error":      PALETTE["error"],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._dot = QLabel()
        self._dot.setFixedSize(10, 10)
        self._dot.setStyleSheet(
            f"background:{PALETTE['ready']}; border-radius:5px;"
        )
        layout.addWidget(self._dot)

        self._label = QLabel("Ready")
        self._label.setStyleSheet(
            f"color:{PALETTE['text_muted']}; font-size:12px; font-weight:500;"
        )
        layout.addWidget(self._label)

    def set_status(self, status: str):
        color = self.STATUS_COLORS.get(status, PALETTE["text_muted"])
        self._dot.setStyleSheet(
            f"background:{color}; border-radius:5px;"
        )
        self._label.setText(status)
        self._label.setStyleSheet(
            f"color:{color}; font-size:12px; font-weight:600;"
        )


# ── Chat bubble ───────────────────────────────────────────────────────────────

class ChatBubble(QWidget):
    """A single message bubble in the conversation view."""

    def __init__(self, text: str, sender: str = "assistant", parent=None):
        """
        sender: 'user' or 'assistant'
        """
        super().__init__(parent)
        self._sender = sender
        self._build(text)

    def _build(self, text: str):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 4, 12, 4)

        bubble = QWidget()
        bubble.setObjectName("bubble")

        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(14, 10, 14, 10)
        inner.setSpacing(4)

        # Sender label
        sender_lbl = QLabel("You" if self._sender == "user" else "VocaDesk")
        sender_lbl.setStyleSheet(
            f"color:{PALETTE['accent_glow'] if self._sender == 'user' else PALETTE['text_muted']};"
            "font-size:11px; font-weight:700; letter-spacing:0.5px;"
        )
        inner.addWidget(sender_lbl)

        # Message text
        msg_lbl = QLabel(text)
        msg_lbl.setWordWrap(True)
        msg_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg_lbl.setStyleSheet(
            f"color:{PALETTE['text']}; font-size:14px; line-height:1.5;"
        )
        inner.addWidget(msg_lbl)

        if self._sender == "user":
            bg = PALETTE["user_bubble"]
            outer.addStretch()
            outer.addWidget(bubble)
            radius = "18px 18px 4px 18px"
        else:
            bg = PALETTE["bot_bubble"]
            outer.addWidget(bubble)
            outer.addStretch()
            radius = "18px 18px 18px 4px"

        bubble.setStyleSheet(
            f"QWidget#bubble {{ background:{bg}; border-radius:{radius}; }}"
        )

        # Max width
        bubble.setMaximumWidth(560)
        bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 80))
        bubble.setGraphicsEffect(shadow)


# ── Mic Button ────────────────────────────────────────────────────────────────

class MicButton(QPushButton):
    """
    Large circular microphone button with animated ring.
    States: idle, listening, processing
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = "idle"
        self._ring_opacity = 0.0

        self.setFixedSize(80, 80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to start listening  (Enter)")
        self._update_style()

        # Pulsing animation
        self._anim = QPropertyAnimation(self, b"ring_opacity")
        self._anim.setDuration(900)
        self._anim.setStartValue(0.2)
        self._anim.setEndValue(0.8)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setLoopCount(-1)  # infinite

    # ── Qt Property for animation ────────────────────────────────────────────

    def _get_ring_opacity(self) -> float:
        return self._ring_opacity

    def _set_ring_opacity(self, v: float):
        self._ring_opacity = v
        self.update()

    ring_opacity = Property(float, _get_ring_opacity, _set_ring_opacity)

    # ── Public ────────────────────────────────────────────────────────────────

    def set_state(self, state: str):
        """state: 'idle' | 'listening' | 'processing'"""
        self._state = state
        if state == "listening":
            self._anim.start()
        else:
            self._anim.stop()
            self._ring_opacity = 0.0
        self._update_style()
        self.update()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 4

        # Animated ring (listening only)
        if self._ring_opacity > 0:
            ring_r = r + 10
            pen = QPen(QColor(239, 68, 68, int(self._ring_opacity * 200)))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2))

        # Main circle
        if self._state == "idle":
            grad = QRadialGradient(cx, cy - r * 0.2, r)
            grad.setColorAt(0, QColor("#6B7FFF"))
            grad.setColorAt(1, QColor("#3A4FDD"))
        elif self._state == "listening":
            grad = QRadialGradient(cx, cy - r * 0.2, r)
            grad.setColorAt(0, QColor("#FF6B6B"))
            grad.setColorAt(1, QColor("#DD3A3A"))
        else:  # processing
            grad = QRadialGradient(cx, cy - r * 0.2, r)
            grad.setColorAt(0, QColor("#FFB347"))
            grad.setColorAt(1, QColor("#DD8C1A"))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Microphone icon (Unicode character rendered as text)
        icon = "🎤" if self._state == "idle" else ("🔴" if self._state == "listening" else "⏳")
        painter.setPen(QColor("white"))
        font = QFont()
        font.setPointSize(22)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, icon)

    def _update_style(self):
        self.setStyleSheet(
            "QPushButton { background: transparent; border: none; }"
        )
