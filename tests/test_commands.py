"""
tests/test_commands.py - Unit tests for command processing logic.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def processor():
    """Return a CommandProcessor with no AI client."""
    from app.command_processor import CommandProcessor
    return CommandProcessor(ai_client=None)


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    """Redirect the database to a temporary path for test isolation."""
    import app.database as db_module
    import app.utils as utils_module
    monkeypatch.setattr(utils_module, "DATA_DIR", tmp_path)
    import app.database
    monkeypatch.setattr(app.database, "DB_PATH", tmp_path / "test.db")
    app.database.init_db()
    yield


# ── Time command ──────────────────────────────────────────────────────────────

class TestTimeCommand:
    def test_what_time_is_it(self, processor):
        result = processor.process("What time is it?")
        assert "It is" in result
        assert "M" in result  # AM or PM

    def test_current_time(self, processor):
        result = processor.process("current time")
        assert "It is" in result

    def test_whats_the_time(self, processor):
        result = processor.process("what's the time")
        assert "It is" in result


# ── Date command ──────────────────────────────────────────────────────────────

class TestDateCommand:
    def test_what_is_todays_date(self, processor):
        result = processor.process("What is today's date?")
        assert "Today is" in result

    def test_what_day_is_it(self, processor):
        result = processor.process("what day is it")
        assert "Today is" in result

    def test_current_date(self, processor):
        result = processor.process("current date")
        assert "Today is" in result


# ── Website command ───────────────────────────────────────────────────────────

class TestWebsiteCommand:
    def test_open_youtube(self, processor):
        with patch("webbrowser.open") as mock_open:
            result = processor.process("open YouTube")
            mock_open.assert_called_once()
            assert "YouTube" in result or "youtube" in result.lower()

    def test_open_google(self, processor):
        with patch("webbrowser.open") as mock_open:
            result = processor.process("open Google")
            mock_open.assert_called_once()

    def test_open_github(self, processor):
        with patch("webbrowser.open") as mock_open:
            result = processor.process("open GitHub")
            mock_open.assert_called_once()


# ── Search command ────────────────────────────────────────────────────────────

class TestSearchCommand:
    def test_search_for_query(self, processor):
        with patch("webbrowser.open") as mock_open:
            result = processor.process("search for Python decorators")
            mock_open.assert_called_once()
            called_url = mock_open.call_args[0][0]
            assert "google" in called_url
            assert "Python" in called_url or "python" in called_url.lower()

    def test_search_google_for(self, processor):
        with patch("webbrowser.open") as mock_open:
            result = processor.process("search Google for machine learning")
            mock_open.assert_called_once()

    def test_google_query(self, processor):
        with patch("webbrowser.open") as mock_open:
            result = processor.process("google what is recursion")
            mock_open.assert_called_once()


# ── Unknown command ───────────────────────────────────────────────────────────

class TestUnknownCommand:
    def test_unknown_returns_helpful_message(self, processor):
        result = processor.process("xyzzy frobulate zorblax")
        assert len(result) > 0
        # Should not crash and should return a user-friendly message
        assert "not sure" in result.lower() or "help" in result.lower()

    def test_empty_input(self, processor):
        result = processor.process("")
        assert "try again" in result.lower() or len(result) > 0


# ── Notes ─────────────────────────────────────────────────────────────────────

class TestNotes:
    def test_take_a_note(self, processor):
        result = processor.process("take a note: buy groceries tomorrow")
        assert "saved" in result.lower() or "note" in result.lower()

    def test_note_colon(self, processor):
        result = processor.process("note: finish the DSA assignment")
        assert "saved" in result.lower()

    def test_show_notes_empty(self, processor):
        result = processor.process("show my notes")
        assert "note" in result.lower()

    def test_show_notes_after_adding(self, processor):
        processor.process("take a note: test note content")
        result = processor.process("show my notes")
        assert "test note content" in result

    def test_delete_note(self, processor):
        processor.process("take a note: note to be deleted")
        # The note ID should be 1 (first note in fresh DB)
        result = processor.process("delete note 1")
        assert "deleted" in result.lower() or "not found" in result.lower()


# ── Reminders ─────────────────────────────────────────────────────────────────

class TestReminders:
    def test_remind_me_in_minutes(self, processor):
        result = processor.process("remind me in 30 minutes to drink water")
        assert "reminder" in result.lower() or "set" in result.lower()

    def test_remind_me_at_time(self, processor):
        result = processor.process("remind me at 11 PM to sleep")
        assert "reminder" in result.lower() or "11" in result

    def test_show_reminders_empty(self, processor):
        result = processor.process("show my reminders")
        assert "reminder" in result.lower()

    def test_show_reminders_after_adding(self, processor):
        processor.process("remind me in 60 minutes to check email")
        result = processor.process("show my reminders")
        assert "check email" in result.lower()


# ── Greeting ──────────────────────────────────────────────────────────────────

class TestGreeting:
    def test_hello(self, processor):
        result = processor.process("hello")
        assert "vocadesk" in result.lower() or "morning" in result.lower() \
               or "afternoon" in result.lower() or "evening" in result.lower()

    def test_hi(self, processor):
        result = processor.process("hi")
        assert len(result) > 0


# ── Help ──────────────────────────────────────────────────────────────────────

class TestHelp:
    def test_help(self, processor):
        result = processor.process("help")
        assert "time" in result.lower() or "open" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
