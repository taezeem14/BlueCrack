"""Tests for TargetQueue sequential execution manager."""

from bluecrack.target_queue import TargetQueue


def test_target_queue_operations():
    """Test adding, getting, removing, and next targets."""
    tq = TargetQueue()

    # Add targets
    idx1 = tq.add_target({"target_url": "https://site1.com/login", "username": "admin", "password": "123"})
    idx2 = tq.add_target({"target_url": "https://site2.com/login", "username": "user", "password": "456"})
    assert idx1 == 0
    assert idx2 == 1

    # Verify targets list
    targets = tq.get_targets()
    assert len(targets) == 2
    assert targets[0]["index"] == 0
    assert targets[0]["status"] == "pending"

    # Next target
    next_tgt = tq.next_target()
    assert next_tgt is not None
    assert next_tgt["target_url"] == "https://site1.com/login"

    # Remove target
    assert tq.remove_target(idx2) is True
