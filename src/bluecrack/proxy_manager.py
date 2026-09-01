"""
BlueCrack Proxy Manager
========================
Smart proxy health monitoring with auto-testing, latency tracking,
round-robin rotation, and dead-proxy detection.
"""

import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)


def _normalize_proxy(proxy: str) -> str:
    """Ensure proxy has a protocol scheme prefix."""
    proxy = proxy.strip()
    if not proxy:
        return ""
    lower = proxy.lower()
    if not (lower.startswith("http://") or lower.startswith("https://") or lower.startswith("socks4://") or lower.startswith("socks5://") or lower.startswith("socks5h://")):
        return f"http://{proxy}"
    return proxy


class ProxyManager:
    """Thread-safe proxy health manager with background monitoring."""

    def __init__(
        self,
        proxies: List[str],
        test_url: str = "https://httpbin.org/ip",
    ) -> None:
        self._proxies = [_normalize_proxy(p) for p in proxies if _normalize_proxy(p)]
        self._test_url = test_url
        self._health: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._rotation_index = 0
        self._bg_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._max_failures = 3

        # Initialize health entries
        for proxy in self._proxies:
            self._health[proxy] = {
                "alive": True,
                "latency_ms": 0.0,
                "last_checked": 0.0,
                "fail_count": 0,
            }

    def test_proxy(self, proxy: str, timeout: int = 5) -> Dict[str, Any]:
        """Test a single proxy for connectivity and measure latency.

        Returns:
            Dict with keys: alive (bool), latency_ms (float).
        """
        normalized = _normalize_proxy(proxy)
        proxy_dict = {"http": normalized, "https": normalized}
        start = time.time()
        try:
            resp = requests.get(
                self._test_url,
                proxies=proxy_dict,
                timeout=timeout,
                verify=False,
            )
            latency = (time.time() - start) * 1000
            alive = resp.status_code == 200
        except Exception:
            latency = (time.time() - start) * 1000
            alive = False

        with self._lock:
            if normalized in self._health:
                self._health[normalized]["latency_ms"] = round(latency, 1)
                self._health[normalized]["last_checked"] = time.time()
                if not alive:
                    self._health[normalized]["fail_count"] += 1
                    # Only mark dead after exceeding max failures threshold
                    if self._health[normalized]["fail_count"] >= self._max_failures:
                        self._health[normalized]["alive"] = False
                else:
                    self._health[normalized]["fail_count"] = 0
                    self._health[normalized]["alive"] = True

        return {"alive": alive, "latency_ms": round(latency, 1)}

    def test_all(self) -> Dict[str, Dict[str, Any]]:
        """Test all proxies in parallel.

        Returns:
            Dict mapping proxy URL to health status.
        """
        results: Dict[str, Dict[str, Any]] = {}
        if not self._proxies:
            return results
        with ThreadPoolExecutor(max_workers=min(10, len(self._proxies))) as pool:
            futures = {
                pool.submit(self.test_proxy, proxy): proxy
                for proxy in self._proxies
            }
            for future in as_completed(futures):
                proxy = futures[future]
                try:
                    results[proxy] = future.result()
                except Exception:
                    results[proxy] = {"alive": False, "latency_ms": 0.0}
        return results

    def get_best(self) -> Optional[str]:
        """Return the lowest-latency alive proxy."""
        with self._lock:
            alive_proxies = [
                (p, h)
                for p, h in self._health.items()
                if h["alive"] and h["fail_count"] < self._max_failures
            ]
            if not alive_proxies:
                return None
            tested = [
                p for p in alive_proxies
                if p[1]["last_checked"] > 0 and p[1]["latency_ms"] > 0
            ]
            if tested:
                return min(tested, key=lambda x: x[1]["latency_ms"])[0]
            return alive_proxies[0][0]

    def rotate(self) -> Optional[str]:
        """Round-robin through alive proxies."""
        with self._lock:
            alive = [
                p
                for p, h in self._health.items()
                if h["alive"] and h["fail_count"] < self._max_failures
            ]
            if not alive:
                return None
            proxy = alive[self._rotation_index % len(alive)]
            self._rotation_index += 1
            return proxy

    def mark_dead(self, proxy: str) -> None:
        """Increment failure count for a proxy."""
        normalized = _normalize_proxy(proxy)
        with self._lock:
            if normalized in self._health:
                self._health[normalized]["fail_count"] += 1
                if self._health[normalized]["fail_count"] >= self._max_failures:
                    self._health[normalized]["alive"] = False

    def get_health_report(self) -> List[Dict[str, Any]]:
        """Return health status of all proxies for API response."""
        with self._lock:
            return [
                {
                    "proxy": p,
                    "alive": h["alive"],
                    "latency_ms": h["latency_ms"],
                    "fail_count": h["fail_count"],
                    "last_checked": h["last_checked"],
                }
                for p, h in self._health.items()
            ]

    def start_background_check(self, interval: int = 60) -> None:
        """Start a daemon thread that periodically re-tests all proxies."""
        with self._lock:
            if self._bg_thread is not None and self._bg_thread.is_alive():
                return
            self._stop_event.clear()

            def _checker() -> None:
                while not self._stop_event.is_set():
                    self.test_all()
                    self._stop_event.wait(timeout=interval)

            self._bg_thread = threading.Thread(target=_checker, daemon=True)
            self._bg_thread.start()

    def stop_background_check(self) -> None:
        """Stop the background health check thread."""
        self._stop_event.set()
        with self._lock:
            thread = self._bg_thread
            self._bg_thread = None
        if thread is not None:
            thread.join(timeout=5)

    @property
    def alive_count(self) -> int:
        """Return the number of alive proxies."""
        with self._lock:
            return sum(
                1
                for h in self._health.values()
                if h["alive"] and h["fail_count"] < self._max_failures
            )

    @property
    def total_count(self) -> int:
        """Return total number of proxies."""
        return len(self._proxies)
