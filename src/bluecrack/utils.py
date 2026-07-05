"""
BlueCrack Utilities
====================
Helper functions for browser driver creation, reports, targeted wordlist
generation, Tor proxy control, and output formatting.
"""

import builtins
import json
import os
import random
import sys
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from selenium import webdriver

from .constants import (
    _RED,
    _RESET,
    DEFAULT_USER_AGENTS,
    HAS_STEM,
)

if HAS_STEM:
    try:
        from stem import Signal as TorSignal
        from stem.control import Controller as TorController
    except ImportError:
        pass


def configure_encoding() -> None:
    """Ensure standard output and error streams are configured to use UTF-8 on Windows."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


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
    """Build ChromeOptions from the given context dictionary with performance tuning.

    Args:
        ctx: Configuration dictionary with keys like 'headless', 'use_tor', 'proxies', etc.

    Returns:
        Configured ChromeOptions instance optimized for low-end hardware.
    """
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={random.choice(DEFAULT_USER_AGENTS)}")

    # ── Ultra Performance Tweaks for 2-Core CPUs ──
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--mute-audio")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-breakpad")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-sync")
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--num-raster-threads=1")
    options.add_argument("--disk-cache-size=1")
    options.add_argument("--media-cache-size=1")

    # Limit V8 engine memory usage to reduce CPU thrashing / RAM usage per process
    options.add_argument('--js-flags="--max-semi-space-size=2 --max-old-space-size=256"')

    # Block images to save bandwidth and dramatically speed up rendering time
    chrome_prefs = {
        "profile.default_content_settings.images": 2,
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_setting_values.notifications": 2
    }
    options.add_experimental_option("prefs", chrome_prefs)

    if ctx.get("use_tor"):
        options.add_argument("--proxy-server=socks5://127.0.0.1:9050")
    elif ctx.get("proxies"):
        options.add_argument(f"--proxy-server={random.choice(ctx['proxies'])}")

    if ctx.get("headless"):
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280x720")  # Smaller resolution = less render work
    else:
        # If running in windowed mode, make it small to minimize render overhead
        options.add_argument("--window-size=800x600")

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


def get_package_data_path(filename: str) -> str:
    """Get the absolute path to a package data file.

    Handles standard filesystem, zipped python eggs, and editable installations.
    """
    # Try importing importlib.resources (Python 3.9+)
    try:
        from importlib.resources import files
        # Resolves to a Path object under bluecrack/data/filename
        return str(files("bluecrack.data").joinpath(filename))
    except (ImportError, AttributeError, TypeError):
        # Fallback to file-based pathing relative to this module
        _pkg_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(_pkg_dir, "data", filename)
        if os.path.exists(path):
            return path
        # Fallback to root level configuration files for backward compatibility
        root_path = os.path.abspath(os.path.join(_pkg_dir, "..", "..", "..", filename))
        if os.path.exists(root_path):
            return root_path
        return filename


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
    try:
        from bluecrack.vendor import cupp as _cupp_mod
    except ImportError:
        if log_callback:
            log_callback("[-] cupp.py not found in package.")
        return ""

    try:
        cfg_path = get_package_data_path("cupp.cfg")
        _cupp_mod.read_config(cfg_path)
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
