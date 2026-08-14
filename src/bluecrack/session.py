"""
BlueCrack Session Manager
==========================
Provides crash-proof session persistence — saves attack state to disk
so attacks can be paused and resumed across restarts.
"""

import json
import os
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional, Tuple


class SessionManager:
    """Thread-safe session state manager for attack persistence."""

    def __init__(self, session_path: str = ".bluecrack_session.json") -> None:
        self._path = session_path
        self._lock = threading.Lock()
        self._save_interval = 100  # Save every N attempts

    @property
    def auto_save_interval(self) -> int:
        """Return the auto-save interval (every N attempts)."""
        return self._save_interval

    def has_session(self) -> bool:
        """Check if a saved session file exists."""
        return os.path.isfile(self._path)

    def save_state(
        self,
        ctx: Dict[str, Any],
        remaining_combos: List[Tuple[str, str]],
        metrics: Dict[str, int],
        found_creds: List[Tuple[str, str]],
    ) -> None:
        """Atomically save session state to disk.

        Writes to a temp file first, then renames to prevent corruption.
        """
        state = {
            "version": 1,
            "saved_at": time.time(),
            "saved_at_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "ctx": {
                "target_url": ctx.get("target_url", ""),
                "error_msg": ctx.get("error_msg", ""),
                "success_msg": ctx.get("success_msg", ""),
                "threads": ctx.get("threads", 1),
                "delay": ctx.get("delay", 0),
                "jitter": ctx.get("jitter", 0),
                "headless": ctx.get("headless", False),
                "limit_text": ctx.get("limit_text", ""),
                "cooldown": ctx.get("cooldown", 12),
                "use_tor": ctx.get("use_tor", False),
                "tor_port": ctx.get("tor_port", 9051),
                "tor_shift_every": ctx.get("tor_shift_every", 10),
                "max_attempts": ctx.get("max_attempts", 0),
                "continue_after_success": ctx.get("continue_after_success", False),
                "spray_mode": ctx.get("spray_mode", False),
            },
            "remaining_combos": [[u, p] for u, p in remaining_combos],
            "metrics": dict(metrics),
            "found_creds": [[u, p] for u, p in found_creds],
        }

        with self._lock:
            try:
                dir_name = os.path.dirname(self._path) or "."
                fd, tmp_path = tempfile.mkstemp(
                    dir=dir_name, suffix=".tmp", prefix=".session_"
                )
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        json.dump(state, f, indent=2)
                    # Atomic rename (works on same filesystem)
                    if os.path.exists(self._path):
                        os.replace(tmp_path, self._path)
                    else:
                        os.rename(tmp_path, self._path)
                except Exception:
                    # Clean up temp file on error
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                    raise
            except Exception:
                pass  # Silently fail to not crash the attack

    def load_state(self) -> Optional[Dict[str, Any]]:
        """Load saved session state from disk.

        Returns:
            Dict with keys: ctx, remaining_combos, metrics, found_creds, saved_at
            or None if no session exists or file is corrupted.
        """
        with self._lock:
            if not self.has_session():
                return None
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                # Convert lists back to tuples
                state["remaining_combos"] = [
                    (u, p) for u, p in state.get("remaining_combos", [])
                ]
                state["found_creds"] = [
                    (u, p) for u, p in state.get("found_creds", [])
                ]
                return state
            except (json.JSONDecodeError, KeyError, OSError):
                return None

    def clear_session(self) -> None:
        """Delete the session file."""
        with self._lock:
            try:
                if os.path.isfile(self._path):
                    os.unlink(self._path)
            except OSError:
                pass
