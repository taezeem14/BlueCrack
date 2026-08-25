"""
BlueCrack Target Queue
=======================
Multi-target sequential attack queue — attack multiple URLs
in sequence, each with its own configuration.
"""

import threading
from typing import Any, Dict, List, Optional


class TargetQueue:
    """Manages a queue of attack targets for sequential execution."""

    def __init__(self) -> None:
        self._targets: List[Dict[str, Any]] = []
        self._current_index: int = 0
        self._results: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def add_target(self, config: Dict[str, Any]) -> int:
        """Add a target configuration to the queue.

        Returns:
            The index of the added target.
        """
        with self._lock:
            index = len(self._targets)
            self._targets.append({
                "index": index,
                "config": config,
                "status": "pending",
            })
            return index

    def remove_target(self, index: int) -> bool:
        """Remove a target by index.

        Returns:
            True if removed, False if index invalid or already running.
        """
        with self._lock:
            if 0 <= index < len(self._targets):
                if self._targets[index]["status"] == "pending":
                    self._targets.pop(index)
                    # Re-index remaining targets
                    for i, t in enumerate(self._targets):
                        t["index"] = i
                    if self._current_index > index:
                        self._current_index = max(0, self._current_index - 1)
                    return True
            return False

    def get_targets(self) -> List[Dict[str, Any]]:
        """Return a copy of all targets."""
        with self._lock:
            return [dict(t) for t in self._targets]

    def next_target(self) -> Optional[Dict[str, Any]]:
        """Get the next pending target configuration.

        Returns:
            The config dict for the next target (including its index), or None if all done.
        """
        with self._lock:
            while self._current_index < len(self._targets):
                target = self._targets[self._current_index]
                if target["status"] == "pending":
                    target["status"] = "running"
                    self._current_index += 1
                    cfg = dict(target["config"])
                    cfg["index"] = target["index"]
                    return cfg
                self._current_index += 1
            return None

    def set_result(
        self,
        index: int,
        metrics: Dict[str, Any],
        found_creds: List,
    ) -> None:
        """Store the result for a completed target."""
        with self._lock:
            if 0 <= index < len(self._targets):
                self._targets[index]["status"] = "completed"
                self._results[index] = {
                    "metrics": dict(metrics),
                    "found_creds": list(found_creds),
                }

    def get_progress(self) -> Dict[str, Any]:
        """Get overall multi-target progress."""
        with self._lock:
            total = len(self._targets)
            completed = sum(
                1 for t in self._targets if t["status"] == "completed"
            )
            running = sum(
                1 for t in self._targets if t["status"] == "running"
            )
            return {
                "total": total,
                "completed": completed,
                "running": running,
                "pending": total - completed - running,
                "current_index": self._current_index,
                "results": dict(self._results),
            }

    def reset(self) -> None:
        """Reset the queue for reuse."""
        with self._lock:
            self._current_index = 0
            self._results.clear()
            for t in self._targets:
                t["status"] = "pending"
