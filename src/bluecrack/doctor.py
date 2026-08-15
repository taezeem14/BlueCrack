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
from typing import Any, Dict, List

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


def diagnose() -> Dict[str, Any]:
    """Perform a structured diagnostic check of the system environment.

    Returns:
        Dict containing structured test results, versions, and readiness status.
    """
    checks: List[Dict[str, Any]] = []

    # 1. Python Version
    py_ver = sys.version_info
    py_ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    py_ok = py_ver >= (3, 10)
    checks.append({
        "name": "Python Version",
        "status": "ok" if py_ok else "fail",
        "detail": f"{py_ver_str} ({'Supported' if py_ok else 'Deprecated, requires >=3.10'})",
        "critical": True,
    })

    # 2. Chrome Browser
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

    chrome_ver = "Unknown"
    if chrome_path:
        try:
            if sys.platform == "win32":
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", f"(Get-Item '{chrome_path}').VersionInfo.ProductVersion"],
                    capture_output=True, text=True, timeout=5
                )
                chrome_ver = res.stdout.strip() or "Installed"
            else:
                res = subprocess.run([chrome_path, "--version"], capture_output=True, text=True, timeout=5)
                chrome_ver = res.stdout.strip()
        except Exception:
            chrome_ver = f"Installed at {chrome_path}"

        checks.append({
            "name": "Google Chrome",
            "status": "ok",
            "detail": f"{chrome_ver} ({chrome_path})",
            "critical": True,
        })
    else:
        checks.append({
            "name": "Google Chrome",
            "status": "fail",
            "detail": "Not detected! Selenium browser mode requires Google Chrome.",
            "critical": True,
        })

    # 3. Selenium
    sel_ok = False
    sel_ver = "Not installed"
    try:
        import selenium
        sel_ver = getattr(selenium, "__version__", "Installed")
        sel_ok = True
    except ImportError:
        pass

    checks.append({
        "name": "Selenium Library",
        "status": "ok" if sel_ok else "fail",
        "detail": sel_ver,
        "critical": True,
    })

    # 4. Headless WebDriver Test
    driver_ok = False
    driver_detail = "Skipped"
    if sel_ok:
        try:
            from selenium import webdriver
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=options)
            driver.quit()
            driver_ok = True
            driver_detail = "Headless Chrome initialized successfully"
        except Exception as e:
            driver_detail = f"Failed to initialize: {e}"

        checks.append({
            "name": "WebDriver Initializer",
            "status": "ok" if driver_ok else "warn",
            "detail": driver_detail,
            "critical": False,
        })

    # 5. Flask Web Framework
    flask_ok = False
    try:
        import importlib.metadata
        f_ver = importlib.metadata.version("flask")
        try:
            s_ver = importlib.metadata.version("flask-socketio")
        except Exception:
            s_ver = "Installed"
        flask_ver = f"Flask {f_ver}, SocketIO {s_ver}"
        flask_ok = True
    except Exception:
        try:
            import flask
            import flask_socketio
            flask_ver = f"Flask {getattr(flask, '__version__', 'Installed')}, SocketIO {getattr(flask_socketio, '__version__', 'Installed')}"
            flask_ok = True
        except ImportError as e:
            flask_ver = f"Missing: {e}"

    checks.append({
        "name": "Web UI Libraries",
        "status": "ok" if flask_ok else "fail",
        "detail": flask_ver,
        "critical": True,
    })

    # 6. Optional modules
    checks.append({
        "name": "Tor Network Controller",
        "status": "ok" if HAS_STEM else "warn",
        "detail": "Enabled (stem installed)" if HAS_STEM else "Disabled (pip install stem)",
        "critical": False,
    })

    checks.append({
        "name": "Keyboard Shortcut Setup",
        "status": "ok" if HAS_KEYBOARD else "warn",
        "detail": "Enabled (keyboard installed)" if HAS_KEYBOARD else "Disabled (pip install keyboard)",
        "critical": False,
    })

    # 7. Internet Connectivity
    net_ok = False
    _orig_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(3.0)
        host = socket.gethostbyname("google.com")
        socket.create_connection((host, 80), 2.0)
        net_ok = True
    except Exception:
        pass
    finally:
        socket.setdefaulttimeout(_orig_timeout)

    checks.append({
        "name": "Internet Connectivity",
        "status": "ok" if net_ok else "warn",
        "detail": "Online" if net_ok else "Offline / Network Blocked",
        "critical": False,
    })

    # Summary
    passed_count = sum(1 for c in checks if c["status"] == "ok")
    total_count = len(checks)
    is_healthy = all(c["status"] == "ok" for c in checks if c["critical"])

    return {
        "version": __version__,
        "is_healthy": is_healthy,
        "passed_count": passed_count,
        "total_count": total_count,
        "checks": checks,
    }


def run_doctor() -> None:
    """Perform diagnostic checkup on the system environment and print formatted report."""
    res = diagnose()

    print(f"\n{_CYAN}==================================================")
    print(f"      BlueCrack v{res['version']} Environment Doctor")
    print(f"=================================================={_RESET}\n")

    for c in res["checks"]:
        name = c["name"]
        detail = c["detail"]
        if c["status"] == "ok":
            print(f"  [+] {name}: {detail} {_GREEN}✔{_RESET}")
        elif c["status"] == "warn":
            print(f"  [!] {name}: {detail} {_YELLOW}⚠{_RESET}")
        else:
            print(f"  [-] {name}: {detail} {_RED}✘{_RESET}")

    print(f"\n{_CYAN}--------------------------------------------------")
    print(f"Diagnostic Summary: {res['passed_count']}/{res['total_count']} checks passed.")
    print(f"--------------------------------------------------{_RESET}")

    if res["is_healthy"] and res["passed_count"] == res["total_count"]:
        print(f"\n{_GREEN}{_BOLD}[+] CONGRATULATIONS! Your system is 100% ready to run BlueCrack.{_RESET}\n")
    elif res["is_healthy"]:
        print(f"\n{_YELLOW}{_BOLD}[!] WARNING: Core features will work, but some optional dependencies are missing.{_RESET}\n")
    else:
        print(f"\n{_RED}{_BOLD}[-] CRITICAL: Missing major requirements. Fix errors listed above.{_RESET}\n")
