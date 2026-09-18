"""
database.py - SQLite persistence for notes and reminders.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from app.utils import get_logger, DATA_DIR

logger = get_logger(__name__)

DB_PATH = DATA_DIR / "vocadesk.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS notes (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                content   TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                task        TEXT NOT NULL,
                remind_at   TEXT NOT NULL,
                notified    INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL
            );
        """)
    logger.debug("Database initialised at %s", DB_PATH)


# ── Notes ────────────────────────────────────────────────────────────────────

def add_note(content: str) -> int:
    """Insert a note and return its ID."""
    now = datetime.now().isoformat()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO notes (content, created_at) VALUES (?, ?)",
            (content.strip(), now),
        )
        return cur.lastrowid


def get_notes() -> list[dict]:
    """Return all notes as list of dicts."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, content, created_at FROM notes ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_note(note_id: int) -> bool:
    """Delete a note by ID. Return True if a row was deleted."""
    with _connect() as conn:
        cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        return cur.rowcount > 0


# ── Reminders ────────────────────────────────────────────────────────────────

def add_reminder(task: str, remind_at: datetime) -> int:
    """Insert a reminder and return its ID."""
    now = datetime.now().isoformat()
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO reminders (task, remind_at, created_at) VALUES (?, ?, ?)",
            (task.strip(), remind_at.isoformat(), now),
        )
        return cur.lastrowid


def get_pending_reminders() -> list[dict]:
    """Return reminders that are due and not yet notified."""
    now = datetime.now().isoformat()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM reminders WHERE notified = 0 AND remind_at <= ?",
            (now,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_reminders() -> list[dict]:
    """Return all reminders ordered by time."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM reminders ORDER BY remind_at ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def mark_reminder_notified(reminder_id: int):
    with _connect() as conn:
        conn.execute(
            "UPDATE reminders SET notified = 1 WHERE id = ?", (reminder_id,)
        )


def delete_reminder(reminder_id: int) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        return cur.rowcount > 0
