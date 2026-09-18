"""
command_processor.py - The brain of VocaDesk.

All supported commands are defined here as pattern-matching rules.
To add a new command: add an entry to COMMAND_HANDLERS or the
_match() logic — the rest of the pipeline picks it up automatically.
"""

import re
from datetime import datetime, timedelta
from app.utils import get_logger, format_time, format_date
import app.system_actions as sys_act
import app.database as db

logger = get_logger(__name__)


# ── Regex patterns ─────────────────────────────────────────────────────────────

# Time / Date
_P_TIME  = re.compile(r"\b(what(?:'s|'s| is) the time|what time is it|current time|time now)\b", re.I)
_P_DATE  = re.compile(r"\b(what(?:'s|'s| is) (today'?s? date|the date)|today(?:'s)? date|current date|what day is it)\b", re.I)

# Open website: "open youtube", "open github"
_P_WEBSITE = re.compile(r"\bopen\s+(?:the\s+)?(?:website\s+)?([a-z0-9 .]+)\b", re.I)

# Search: "search for X", "search google for X", "google X"
_P_SEARCH  = re.compile(r"\bsearch(?:\s+(?:google|the web|for))?\s+(?:for\s+)?(.+)", re.I)
_P_GOOGLE  = re.compile(r"\bgoogle\s+(.+)", re.I)

# Open app: "open calculator", "launch notepad"
_P_APP = re.compile(r"\b(?:open|launch|start|run)\s+(.+)", re.I)

# System
_P_LOCK    = re.compile(r"\block\s+(?:my\s+)?(?:computer|pc|screen|workstation)\b", re.I)
_P_DESKTOP = re.compile(r"\b(?:show|go to|minimize all|minimise all)\s+(?:my\s+)?desktop\b", re.I)

# Volume
_P_VOL_UP   = re.compile(r"\b(?:increase|raise|turn up|higher|louder)\s+(?:the\s+)?volume\b", re.I)
_P_VOL_DOWN = re.compile(r"\b(?:decrease|lower|turn down|reduce|quieter)\s+(?:the\s+)?volume\b", re.I)
_P_VOL_MUTE = re.compile(r"\b(?:mute|unmute|toggle mute)\s+(?:the\s+)?(?:volume|sound|audio)?\b", re.I)

# Notes: "take a note: X", "make a note: X", "note: X", "remember X"
_P_TAKE_NOTE   = re.compile(r"\b(?:take a note|make a note|add a note|note|remember)[:\s]+(.+)", re.I)
_P_SHOW_NOTES  = re.compile(r"\b(?:show|list|read|display)\s+(?:my\s+)?notes?\b", re.I)
_P_DELETE_NOTE = re.compile(r"\b(?:delete|remove)\s+note\s+(?:#?\s*)?(\d+)\b", re.I)

# Reminders: "remind me at 7 PM to study DSA"
_P_REMIND  = re.compile(
    r"\bremind\s+me\s+(?:at\s+)?(.+?)\s+to\s+(.+)", re.I
)
_P_SHOW_REMINDERS = re.compile(
    r"\b(?:show|list|display|read)\s+(?:my\s+)?reminders?\b", re.I
)

# Greetings
_P_GREET = re.compile(r"\b(hello|hi|hey|howdy|good (?:morning|afternoon|evening|night))\b", re.I)

# Help
_P_HELP = re.compile(r"\b(help|what can you do|commands|what do you know)\b", re.I)


# ── Time parser ────────────────────────────────────────────────────────────────

def _parse_time_expression(expr: str) -> datetime | None:
    """
    Attempt to parse a natural-language time expression like:
      '7 PM', '7:30 PM', '19:00', 'in 30 minutes', 'in 2 hours'
    Returns a datetime object or None.
    """
    expr = expr.strip().lower()
    now = datetime.now()

    # Relative: "in 30 minutes", "in 2 hours"
    m = re.match(r"in\s+(\d+)\s+(minute|hour|second)s?", expr)
    if m:
        amount = int(m.group(1))
        unit   = m.group(2)
        delta  = {"minute": timedelta(minutes=amount),
                  "hour":   timedelta(hours=amount),
                  "second": timedelta(seconds=amount)}.get(unit, timedelta())
        return now + delta

    # Absolute: "7 PM", "7:30 PM", "19:00"
    for fmt in ("%I %p", "%I:%M %p", "%H:%M", "%I%p", "%I:%M%p"):
        try:
            t = datetime.strptime(expr.upper(), fmt.upper())
            result = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
            if result < now:
                result += timedelta(days=1)  # schedule for tomorrow if past
            return result
        except ValueError:
            continue

    return None


# ── Main processor ─────────────────────────────────────────────────────────────

class CommandProcessor:
    """
    Processes a text command and returns a response string.

    To add a new command:
      1. Add a regex pattern at the top of this file.
      2. Add an elif branch inside process() that matches it.
    """

    def __init__(self, ai_client=None):
        self._ai = ai_client

    def process(self, text: str) -> str:
        """Match `text` against known patterns and return a response string."""
        if not text or not text.strip():
            return "I didn't catch anything. Please try again."

        t = text.strip()
        logger.debug("Processing command: %r", t)

        # ── Time / Date ───────────────────────────────────────────────────────
        if _P_TIME.search(t):
            return f"It is {format_time()}."

        if _P_DATE.search(t):
            return f"Today is {format_date()}."

        # ── Greetings ─────────────────────────────────────────────────────────
        m = _P_GREET.match(t.strip())
        if m:
            hour = datetime.now().hour
            if hour < 12:
                period = "Good morning"
            elif hour < 17:
                period = "Good afternoon"
            else:
                period = "Good evening"
            return f"{period}! I'm VocaDesk. How can I help you?"

        # ── Help ──────────────────────────────────────────────────────────────
        if _P_HELP.search(t):
            return self._help_text()

        # ── Volume ────────────────────────────────────────────────────────────
        if _P_VOL_UP.search(t):
            return sys_act.increase_volume()
        if _P_VOL_DOWN.search(t):
            return sys_act.decrease_volume()
        if _P_VOL_MUTE.search(t):
            return sys_act.mute_volume()

        # ── System ────────────────────────────────────────────────────────────
        if _P_LOCK.search(t):
            return sys_act.lock_computer()
        if _P_DESKTOP.search(t):
            return sys_act.show_desktop()

        # ── Notes ─────────────────────────────────────────────────────────────
        m = _P_TAKE_NOTE.match(t)
        if m:
            note_text = m.group(1).strip()
            note_id = db.add_note(note_text)
            return f"Note saved. (ID: {note_id})"

        if _P_SHOW_NOTES.search(t):
            return self._format_notes()

        m = _P_DELETE_NOTE.search(t)
        if m:
            nid = int(m.group(1))
            success = db.delete_note(nid)
            return f"Note {nid} deleted." if success else f"Note {nid} not found."

        # ── Reminders ─────────────────────────────────────────────────────────
        m = _P_REMIND.match(t)
        if m:
            time_expr = m.group(1).strip()
            task      = m.group(2).strip()
            remind_at = _parse_time_expression(time_expr)
            if remind_at:
                rid = db.add_reminder(task, remind_at)
                time_str = remind_at.strftime("%I:%M %p").lstrip("0")
                return f"Reminder set for {time_str}: '{task}'. (ID: {rid})"
            else:
                return (
                    f"I couldn't understand '{time_expr}' as a time. "
                    "Try formats like '7 PM', '7:30 PM', or 'in 30 minutes'."
                )

        if _P_SHOW_REMINDERS.search(t):
            return self._format_reminders()

        # ── Search ────────────────────────────────────────────────────────────
        m = _P_SEARCH.match(t) or _P_GOOGLE.match(t)
        if m:
            query = m.group(1).strip()
            if query:
                return sys_act.search_web(query)

        # ── Open website vs Open app ──────────────────────────────────────────
        # We distinguish by checking the known-websites list first.
        m = _P_WEBSITE.match(t)
        if m:
            target = m.group(1).strip().lower()
            # Check websites
            for key in sys_act.WEBSITES:
                if target == key or target in key or key in target:
                    return sys_act.open_website(target)
            # Fall through to app check
            result = sys_act.open_application(target)
            if "don't know" not in result and "couldn't find" not in result:
                return result
            # Last resort: try as website anyway
            return sys_act.open_website(target)

        # ── AI fallback ───────────────────────────────────────────────────────
        if self._ai and self._ai.is_available:
            logger.debug("Delegating to AI: %r", t)
            return self._ai.ask(t)

        # ── Unknown ───────────────────────────────────────────────────────────
        return (
            "I'm not sure how to help with that. "
            "Say 'help' to see what I can do, or type your question."
        )

    # ── Formatters ────────────────────────────────────────────────────────────

    def _format_notes(self) -> str:
        notes = db.get_notes()
        if not notes:
            return "You don't have any saved notes yet."
        lines = [f"You have {len(notes)} note(s):"]
        for n in notes:
            lines.append(f"  [{n['id']}] {n['content']}")
        return "\n".join(lines)

    def _format_reminders(self) -> str:
        reminders = db.get_all_reminders()
        if not reminders:
            return "You don't have any reminders."
        lines = [f"You have {len(reminders)} reminder(s):"]
        for r in reminders:
            try:
                dt = datetime.fromisoformat(r["remind_at"])
                time_str = dt.strftime("%b %d at %I:%M %p").lstrip("0")
            except Exception:
                time_str = r["remind_at"]
            status = "✓ done" if r["notified"] else "pending"
            lines.append(f"  [{r['id']}] {time_str} — {r['task']} ({status})")
        return "\n".join(lines)

    def _help_text(self) -> str:
        return (
            "Here's what I can do:\n"
            "  • What time is it? / What's the date?\n"
            "  • Open YouTube / Google / GitHub / Gmail / LinkedIn …\n"
            "  • Search for Python decorators\n"
            "  • Open Calculator / Notepad / VS Code / File Explorer …\n"
            "  • Lock my computer / Show my desktop\n"
            "  • Increase / Decrease / Mute volume\n"
            "  • Take a note: your note text\n"
            "  • Show my notes / Delete note 3\n"
            "  • Remind me at 7 PM to study DSA\n"
            "  • Show my reminders\n"
            "  • (AI mode) Ask me anything if an API key is configured"
        )
