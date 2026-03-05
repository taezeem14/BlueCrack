# 🚀 **BlueCrack – Browser‑Based Login Tester (Built Different)**

*A Selenium‑powered login testing tool giving Hydra vibes, but it actually respects your browser window.*

BlueCrack lets you vibe‑check login forms **inside an actual active browser** (Chrome), without inspecting elements like a boomer. 
You can literally just let it **auto-detect the inputs**, or you click the fields, lock the selectors, load up your wordlist, and let it cook. It’s that deep.

⚠️ **For educational + authorized pentesting only. Don't catch a case.**

---

## ✨ W Features

*   **Interactive Wizard mode (`-i`)** because memorizing CLI commands is kinda mid
*   **CUPP Integration (Wordlist Generator):** Direct integration with `cupp.py` (Common User Passwords Profiler) to build highly targeted, personalized dictionaries right from the wizard. 
*   **Auto-detects CSS selectors** (Auto-aim for HTML login forms)
*   **Multi-threaded AF** (Hydra-style `--threads` but spawns parallel brains)
*   **Invisible phantom mode (`--headless`)** so it doesn't nuke your screen real estate
*   **Stealth AF (duck Cloudflare / Rate Limits):**
    *   **User-Agent Spoofing:** Randomizes browsers (Chrome/Firefox/Mac/Linux) per thread to duck fingerprinting.
    *   **Anti-Bot Stripper:** Removes `navigator.webdriver` flags so WAFs don't instantly pack you up.
    *   **Proxy Rotation Engine:** Feed it a proxy list and let threads randomly hop IPs. *Yes, this straight up fixes and ducks IP blocking/bans because every request looks like a completely different user from a different location.*
    *   **Jitter Physics:** Humanized, randomized timing delays between requests so it never looks like a bot.
    *   **Smart Rate Limit Back-offs:** Automatically catches "Too Many Requests" blocks, pauses, and re-queues.

---

## 📂 The Stash (Repo Structure)

```
BlueCrack/
│
├── bluecrack.py         # Main brute testing engine (The Chef)
├── cupp.py              # Profile-based target wordlist generator
├── pass.txt             # Dummy Passlist
├── demo_server.py       # Local target practice (Dummy Flask App)
├── requirements.txt     # The drip dependencies
└── README.md            # The lore you're reading right now
```

---

## 🛠️ Getting the Drip (Install)

Install the dependencies. Smash this into your terminal:

```bash
pip install -r requirements.txt
```

*(Note: BlueCrack will automatically prompt to download `cupp.py` dynamically if it's missing during wizard generation).*
*Required: Make sure your system has Chrome + ChromeDriver setup properly or it's gonna crash and burn.*

---

## ▶️ How to Flex It

### The "I'm Lazy" Interactive Mode (Highly Recommended W)
Just run this and answer the questions. The wizard can even launch CUPP for you to build a dictionary first, auto-detect the CSS, and set everything up:
```bash
python bluecrack.py -i
```

### The "I'm a Hacker" Terminal Mode (CLI)

**Single username + passlist under the radar (headless):**
```bash
python bluecrack.py -u admin -P passlist.txt --threads 5 --url "http://target.com/login" --error "failed" --headless
```

**Matrix Combo (Userlist + Passlist):**
```bash
python bluecrack.py -U users.txt -P passlist.txt --threads 10 --url "http://target.com/login"
```

---

## 🧩 The Lore (How it Cooks)

1. The script fires up the target login page in Chrome.
2. The UI tries to **Auto-Detect** the username / password fields. 
3. If auto-detect fumbles, point and click the username field → press **S**. Then click the password field → press **T**.
4. Press **ENTER** to start the main event.
5. The threads go brrr, spinning up browsers to spam credentials.
6. If the page URL changes or the specific error message disappears, we secured the bag (Valid Login found 🔥). 

---

## 📜 The Flags (No Red Flags Here)

| Flag                  | Description                                   |
| --------------------- | --------------------------------------------- |
| `-i` / `--interactive`| Launch the ultimate hand-holding W wizard     |
| `-u` / `--user`       | Single target username                        |
| `-U` / `--userfile`   | File containing a bunch of usernames          |
| `-p` / `--passw`      | Single password check                         |
| `-P` / `--passlist`   | Wordlist of passwords to test                 |
| `--threads`           | Thread count (How fast it goes brrr)          |
| `--delay`             | Slow it down (Stealth throttle)               |
| `--jitter`            | Add random X seconds to delay (Humanize it)   |
| `--proxy`             | Single proxy string (http://IP:PORT)          |
| `--proxy-list`        | Txt file of proxies to rotate constantly      |
| `--url`               | Target login page                             |
| `--error`             | The string to check for an "L" (default: incorrect) |
| `--limit-text`        | Text that confirms Rate Limit (`Too many...`) |
| `--cooldown`          | Wait timer in secs when Rate Limit ducked   |
| `--headless`          | Runs workers invisibly in the background      |

---

## 🚀 The Anti-Rate Limit & Ghost Stash (duck Mechanics)

WAFs (Web Application Firewalls) like Cloudflare will block obvious bot spam instantly. BlueCrack uses multiple layers of Ghost-level evasion:

1. **Proxy Roulette `--proxy-list proxies.txt`**: Give it a massive list of proxies, and every single testing thread will randomly hop onto a different proxy IP address!
2. **Jitter Physics `--jitter 2.5`**: Typical bots hit a server exactly every `2.0` seconds. WAFs see that math and ban you. Using `jitter`, BlueCrack will wait a randomized time between requests (e.g., `delay + random up to 2.5s`). It looks entirely human.
3. **Ghost Driver**: BlueCrack natively hides and removes `navigator.webdriver=True` flags and spoof layers a random popular User-Agent matrix from Chrome, Firefox, Mac, and Linux for every thread. 
4. **Blank Payload Elimination**: Ghost Engine auto-strips random newline gaps and empty string payloads typically generated by OSINT profilers to prevent HTML5 `required` popups from triggering false positives.
5. **Smart Auto-Throttle Engine**: Got hit with an IP-based `429 Too Many Requests`? No panic. When the UI catches the block word (`--limit-text`), it immediately initiates a `--cooldown` freeze, kicks the failed username/password back into the active queue, waits for the block to expire entirely stealthily, and resumes without losing any credential tests!
No credentials skipped, no IP completely locked. Big W.

This tool is strictly for **educational ops**, **security research**, and **authorized penetration testing** only. 
Do **not** use it on your school's portal, systems you don't own, or ops that didn't give you written permission. You will get packed up. Deadass.
