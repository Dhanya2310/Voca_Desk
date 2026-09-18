"""
reminders.py - Background thread that checks for due reminders
               and emits a Qt signal when one fires.
"""

import time
from PySide6.QtCore import QThread, Signal
from app import database as db
from app.utils import get_logger

logger = get_logger(__name__)


class ReminderChecker(QThread):
    """
    Runs in a background thread, checking every 30 seconds for
    reminders that are due. Emits reminder_due(task_text) when found.
    """

    reminder_due = Signal(str)   # emits the reminder task text

    POLL_INTERVAL = 30  # seconds

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False

    def run(self):
        self._running = True
        logger.debug("ReminderChecker started.")
        while self._running:
            try:
                pending = db.get_pending_reminders()
                for r in pending:
                    logger.info("Reminder fired: %s", r["task"])
                    db.mark_reminder_notified(r["id"])
                    self.reminder_due.emit(r["task"])
            except Exception as e:
                logger.error("ReminderChecker error: %s", e)
            # Sleep in small intervals so we can exit quickly
            for _ in range(self.POLL_INTERVAL * 2):
                if not self._running:
                    break
                time.sleep(0.5)

    def stop(self):
        self._running = False
