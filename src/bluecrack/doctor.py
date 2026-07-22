"""
BlueCrack Doctor — Environment and Dependency Diagnostics
============================================================
Checks system dependencies, Chrome installation, and networking capabilities
to verify that BlueCrack can run successfully.
"""

import os
import shutil
import socket
import subprocess
import sys

from ._version import __version__
from .constants import (
    _BOLD,
    _CYAN,
    _GREEN,
    _RED,
    _RESET,
    _YELLOW,
    HAS_KEYBOARD,
    HAS_STEM,
)


def _check_command(cmd: str) -> bool:
    """Return True if a command is available on PATH."""
    return shutil.which(cmd) is not None


def _check_port_listening(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if a port is listening on the host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def run_doctor() -> None:
    """Perform diagnostic checkup on the system environment."""
    print(f"\n{_CYAN}==================================================")
    print(f"      BlueCrack v{__version__} Environment Doctor")
    print(f"=================================================={_RESET}\n")

    passed_checks = 0
    total_checks = 7

    # 1. Python version
    py_ver = sys.version_info
    py_ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    if py_ver >= (3, 9):
        print(f"  [+] Python version: {py_ver_str} (Supported) {_GREEN}✔{_RESET}")
        passed_checks += 1
    else:
        print(f"  [-] Python version: {py_ver_str} (Deprecated! BlueCrack requires Python >= 3.9) {_RED}✘{_RESET}")

    # 2. Chrome Installation check
    chrome_path = None
    if sys.platform == "win32":
        paths = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Google\\Chrome\\Application\\chrome.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Google\\Chrome\\Application\\chrome.exe"),
            os.path.join(os.environ.get("LocalAppData", "C:\\Users\\Default\\AppData\\Local"), "Google\\Chrome\\Application\\chrome.exe"),
        ]
        for p in paths:
            if os.path.exists(p):
                chrome_path = p
                break
    else:
        chrome_path = shutil.which("google-chrome") or shutil.which("chrome") or shutil.which("chromium")

    if chrome_path:
        # Try to get version
        try:
            if sys.platform == "win32":
                # Get version on windows via registry or powershell
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", f"(Get-Item '{chrome_path}').VersionInfo.ProductVersion"],
                    capture_output=True, text=True
                )
                ver_str = res.stdout.strip() or "Unknown"
            else:
                res = subprocess.run([chrome_path, "--version"], capture_output=True, text=True)
                ver_str = res.stdout.strip()
            print(f"  [+] Chrome browser: Installed ({ver_str}) {_GREEN}✔{_RESET}")
            passed_checks += 1
        except Exception:
            print(f"  [+] Chrome browser: Installed at {chrome_path} {_GREEN}✔{_RESET}")
            passed_checks += 1
    else:
        print(f"  [-] Chrome browser: Not detected! Selenium requires Google Chrome. {_RED}✘{_RESET}")

    # 3. Selenium & Driver check
    webdriver = None
    try:
        import selenium
        from selenium import webdriver as _wd
        webdriver = _wd
        sel_ver = getattr(selenium, '__version__', 'unknown')
        print(f"  [+] Selenium library: Installed ({sel_ver}) {_GREEN}✔{_RESET}")
        passed_checks += 1
    except ImportError:
        print(f"  [-] Selenium library: Not found! Run: pip install selenium {_RED}✘{_RESET}")

    # 4. Headless WebDriver Creation Check
    if webdriver is not None:
        print("  [*] Testing headless Chrome driver creation...")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            print(f"  [+] WebDriver test: Headless driver created successfully {_GREEN}✔{_RESET}")
            passed_checks += 1
        except Exception as e:
            print(f"  [-] WebDriver test: Failed to create driver! Details: {e} {_RED}✘{_RESET}")
            print("      Ensure Chrome is updated and no conflicting driver version exists.")
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
    else:
        print(f"  [-] WebDriver test: Skipped (Selenium not installed) {_YELLOW}⚠{_RESET}")

    # 5. Core web UI libraries (Flask / Flask-SocketIO)
    flask_ok = True
    try:
        import flask
        import flask_socketio
    except ImportError as e:
        flask_ok = False
        print(f"  [-] Web UI dependencies: Missing module: {e} {_RED}✘{_RESET}")

    if flask_ok:
        fs_ver = getattr(flask_socketio, "__version__", "installed")
        print(f"  [+] Web UI libraries: Flask ({flask.__version__}) & Flask-SocketIO ({fs_ver}) {_GREEN}✔{_RESET}")
        passed_checks += 1
    else:
        print("      Run: pip install flask flask-socketio")


    # 6. Optional modules & features (Tor, manual keyboard selector)
    optional_features = []
    if HAS_STEM:
        optional_features.append(f"Tor Control ({_GREEN}Enabled{_RESET})")
    else:
        optional_features.append(f"Tor Control ({_YELLOW}Disabled — missing stem package{_RESET})")

    if HAS_KEYBOARD:
        optional_features.append(f"Keyboard Setup ({_GREEN}Enabled{_RESET})")
    else:
        optional_features.append(f"Keyboard Setup ({_YELLOW}Disabled — missing keyboard package{_RESET})")

    print("  [+] Optional features:")
    for f in optional_features:
        print(f"      - {f}")
    passed_checks += 1  # Optional, always passes

    # 7. Network checks
    print("  [*] Checking network connectivity...")
    net_ok = False
    _orig_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(3.0)
        host = socket.gethostbyname("google.com")
        socket.create_connection((host, 80), 2.0)
        net_ok = True
    except (OSError, socket.gaierror):
        pass
    finally:
        socket.setdefaulttimeout(_orig_timeout)

    if net_ok:
        print(f"  [+] Internet connectivity: Online {_GREEN}✔{_RESET}")
        passed_checks += 1
    else:
        print(f"  [-] Internet connectivity: Offline / Blocked {_YELLOW}⚠{_RESET}")

    # Tor service check if stem is installed
    if HAS_STEM:
        tor_active = _check_port_listening(9050)
        tor_control_active = _check_port_listening(9051)
        if tor_active:
            print(f"      - Tor proxy (SOCKS5 9050): {_GREEN}Active{_RESET}")
        else:
            print(f"      - Tor proxy (SOCKS5 9050): {_YELLOW}Not responding{_RESET}")
        if tor_control_active:
            print(f"      - Tor controller (PORT 9051): {_GREEN}Active{_RESET}")
        else:
            print(f"      - Tor controller (PORT 9051): {_YELLOW}Not responding{_RESET}")

    # Summary
    print(f"\n{_CYAN}--------------------------------------------------")
    print(f"Diagnostic Summary: {passed_checks}/{total_checks} checks passed.")
    print(f"--------------------------------------------------{_RESET}")

    if passed_checks == total_checks:
        print(f"\n{_GREEN}{_BOLD}[+] CONGRATULATIONS! Your system is 100% ready to run BlueCrack.{_RESET}\n")
    elif passed_checks >= 5:
        print(f"\n{_YELLOW}{_BOLD}[!] WARNING: Most features will work, but some dependencies are missing.{_RESET}\n")
    else:
        print(f"\n{_RED}{_BOLD}[-] CRITICAL: Missing major requirements. Fix errors listed above.{_RESET}\n")
