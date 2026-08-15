"""Tests for SessionManager state persistence and recovery."""

import os
import tempfile

from bluecrack.session import SessionManager


def test_session_lifecycle():
    """Test saving, checking, loading, and clearing sessions."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        session_file = os.path.join(tmp_dir, "test_session.json")
        sm = SessionManager(session_path=session_file)

        assert not sm.has_session()

        # Save session
        ctx = {"target_url": "https://example.com/login", "threads": 4}
        remaining = [("admin", "pass1"), ("admin", "pass2")]
        metrics = {"attempted": 10, "successes": 1}
        found_creds = [("root", "toor")]

        sm.save_state(ctx, remaining, metrics, found_creds)
        assert sm.has_session()

        # Load session
        loaded = sm.load_state()
        assert loaded is not None
        assert loaded["ctx"]["target_url"] == "https://example.com/login"
        assert len(loaded["remaining_combos"]) == 2
        assert loaded["metrics"]["attempted"] == 10
        assert loaded["found_creds"] == [("root", "toor")]

        # Clear session
        sm.clear_session()
        assert not sm.has_session()
        assert sm.load_state() is None


def test_session_corrupted_file_recovery():
    """Test safe handling when session file contains invalid JSON."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        session_file = os.path.join(tmp_dir, "corrupted_session.json")
        with open(session_file, "w", encoding="utf-8") as f:
            f.write("INVALID_JSON_CORRUPTED_DATA{{{")

        sm = SessionManager(session_path=session_file)
        assert sm.has_session()
        # Should gracefully return None and not crash
        assert sm.load_state() is None
