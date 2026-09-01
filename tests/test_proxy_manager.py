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


def test_proxy_manager_scheme_normalization():
    """Verify schemeless proxies like ip:port get normalized with http:// prefix."""
    pm = ProxyManager(["192.168.1.10:8080", "https://10.0.0.1:3128", "socks5://localhost:9050"])
    assert pm._proxies[0] == "http://192.168.1.10:8080"
    assert pm._proxies[1] == "https://10.0.0.1:3128"
    assert pm._proxies[2] == "socks5://localhost:9050"


def test_proxy_manager_mark_dead_and_health():
    """Verify mark_dead works with unnormalized input and tracks failure thresholds."""
    pm = ProxyManager(["192.168.1.10:8080"])
    norm_key = "http://192.168.1.10:8080"
    assert pm._health[norm_key]["alive"] is True
    assert pm._health[norm_key]["fail_count"] == 0

    # Mark dead using raw unnormalized string
    pm.mark_dead("192.168.1.10:8080")
    assert pm._health[norm_key]["fail_count"] == 1
    assert pm._health[norm_key]["alive"] is True  # Not dead yet (threshold is 3)

    pm.mark_dead("192.168.1.10:8080")
    pm.mark_dead("192.168.1.10:8080")
    assert pm._health[norm_key]["fail_count"] == 3
    assert pm._health[norm_key]["alive"] is False  # Marked dead after 3 failures


