"""Tests for AttackScheduler delayed queue management."""

import time

from bluecrack.scheduler import AttackScheduler


def test_scheduler_lifecycle():
    """Test scheduling, listing, and cancelling attacks."""
    sched = AttackScheduler()
    # Schedule an attack in the future
    future_time = time.time() + 1000
    run_at_str = time.strftime("%Y-%m-%dT%H:%M", time.localtime(future_time))

    entry_id = sched.schedule(
        {"target_url": "https://example.com/login", "username": "admin", "password": "123"},
        run_at_str,
    )
    assert entry_id is not None

    # List scheduled
    scheduled = sched.list_scheduled()
    assert len(scheduled) >= 1
    found = [s for s in scheduled if s["id"] == entry_id]
    assert len(found) == 1
    assert found[0]["status"] == "pending"

    # Cancel
    assert sched.cancel(entry_id) is True
    scheduled_after = sched.list_scheduled()
    found_after = [s for s in scheduled_after if s["id"] == entry_id]
    assert len(found_after) == 1
    assert found_after[0]["status"] == "cancelled"

    # Clear history
    cleared = sched.clear_history()
    assert cleared == 1
    assert len(sched.list_scheduled()) == 0

    # Test scheduling with None config
    entry_id_none = sched.schedule(None, run_at_str)
    assert entry_id_none is not None
    found_none = [s for s in sched.list_scheduled() if s["id"] == entry_id_none]
    assert len(found_none) == 1
    assert found_none[0]["target_url"] == ""

    # Test stop() thread cleanup
    sched.stop()
    assert sched._timer_thread is None

