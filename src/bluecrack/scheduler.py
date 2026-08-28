"""
BlueCrack Attack Scheduler
============================
Schedule attacks to run at specific times with background timer management.
"""

import threading
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


class AttackScheduler:
    """Manages scheduled attacks with background timer execution."""

    def __init__(self) -> None:
        self._scheduled: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._on_fire: Optional[Callable[[Dict[str, Any]], None]] = None

    def set_fire_callback(
        self, cb: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Set callback to invoke when a scheduled attack fires.

        Args:
            cb: Callable that receives the attack config dict.
        """
        self._on_fire = cb

    def schedule(self, config: Dict[str, Any], run_at_iso: str) -> str:
        """Schedule an attack for future execution.

        Args:
            config: Attack configuration dict.
            run_at_iso: ISO 8601 datetime string for when to run.

        Returns:
            Unique schedule ID (UUID).
        """
        schedule_id = str(uuid.uuid4())[:8]
        try:
            run_at = datetime.fromisoformat(run_at_iso)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid datetime format: {run_at_iso}")

        entry = {
            "id": schedule_id,
            "config": dict(config),
            "run_at": run_at_iso,
            "run_at_ts": run_at.timestamp(),
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }

        with self._lock:
            self._scheduled.append(entry)

        # Ensure timer is running
        self.start()
        return schedule_id

    def cancel(self, schedule_id: str) -> bool:
        """Cancel a scheduled attack by ID.

        Returns:
            True if found and cancelled, False otherwise.
        """
        with self._lock:
            for entry in self._scheduled:
                if entry["id"] == schedule_id and entry["status"] == "pending":
                    entry["status"] = "cancelled"
                    return True
        return False

    def list_scheduled(self) -> List[Dict[str, Any]]:
        """Return all scheduled attacks with their status."""
        with self._lock:
            return [
                {
                    "id": e["id"],
                    "run_at": e["run_at"],
                    "status": e["status"],
                    "created_at": e["created_at"],
                    "target_url": e["config"].get("target_url", ""),
                }
                for e in self._scheduled
            ]

    def clear_history(self) -> int:
        """Remove fired, cancelled, or error tasks from history.

        Returns:
            Count of cleared tasks.
        """
        with self._lock:
            initial = len(self._scheduled)
            self._scheduled = [e for e in self._scheduled if e.get("status") == "pending"]
            return initial - len(self._scheduled)

    def start(self) -> None:
        """Start the background timer thread."""
        with self._lock:
            if self._timer_thread is not None and self._timer_thread.is_alive():
                return
            self._stop_event.clear()

            def _timer_loop() -> None:
                while not self._stop_event.is_set():
                    now = time.time()
                    to_fire = []
                    with self._lock:
                        for e in self._scheduled:
                            if e["status"] == "pending" and e["run_at_ts"] <= now:
                                e["status"] = "fired"
                                to_fire.append(e)

                    for entry in to_fire:
                        if self._on_fire:
                            def _fire_worker(item=entry) -> None:
                                try:
                                    self._on_fire(item["config"])
                                except Exception:
                                    with self._lock:
                                        item["status"] = "error"

                            try:
                                threading.Thread(
                                    target=_fire_worker,
                                    daemon=True,
                                ).start()
                            except Exception:
                                with self._lock:
                                    entry["status"] = "error"

                    self._stop_event.wait(timeout=1)

            self._timer_thread = threading.Thread(
                target=_timer_loop, daemon=True
            )
            self._timer_thread.start()

    def stop(self) -> None:
        """Stop the background timer thread."""
        self._stop_event.set()
        with self._lock:
            if self._timer_thread is not None:
                self._timer_thread.join(timeout=5)
                self._timer_thread = None

    @property
    def pending_count(self) -> int:
        """Return the number of pending scheduled attacks."""
        with self._lock:
            return sum(
                1 for e in self._scheduled if e["status"] == "pending"
            )
