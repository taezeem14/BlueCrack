"""Tests for ProxyManager rotation, formatting, and health verification."""

from bluecrack.proxy_manager import ProxyManager


def test_proxy_manager_empty():
    """Verify ProxyManager gracefully handles empty proxy list."""
    pm = ProxyManager([])
    assert len(pm._proxies) == 0
    assert pm.rotate() is None
    assert pm.get_best() is None
    assert pm.test_all() == {}


def test_proxy_manager_rotation():
    """Verify rotation cycles sequentially through proxies."""
    pm = ProxyManager(["http://p1:8080", "http://p2:8080"])
    first = pm.rotate()
    second = pm.rotate()
    third = pm.rotate()

    assert first != second
    assert third == first
