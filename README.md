# 🚀 BlueCrack – Advanced GUI Browser-Based Penetration Testing Framework

BlueCrack is a professional-grade Selenium and PyQt6-powered login security testing tool designed for controlled security research, educational environments, and authorized penetration testing. 
It allows researchers and students to evaluate login form behavior inside a real browser (Chrome Headless), analyze authentication responses, and study defensive mechanisms such as rate limiting and input validation dynamically across multiple parallel web contexts.

> ⚠️ This tool must only be used in controlled lab environments or on systems where explicit written authorization has been granted.

---

## 🎯 Project Purpose

BlueCrack was built as an experimentation project to explore:
* Browser automation using Selenium Webdriver
* Hardware-accelerated PyQt6 desktop interfaces
* Complex multi-threaded request coordination
* Login form state detection and CSS injection 
* Dynamic browser-context restarts bridging WebSockets and Threading
* Defensive mechanism evasion (Custom Tor Proxies, Auto-Rotations)

---

## ✨ Core Features

* **Rich Tabbed PyQt6 Interface**
  A robust and fully integrated desktop UI removing the need for clunky CLIs. Manage Targets, Engines, Networking and Generators cleanly.
* **⚡ Raw HTTP Mode (Fast & Lightweight)**
  Bypass the overhead of headless browsers with an integrated Raw Requests mode (`--raw`). Ideal for low-end machines (e.g. older processors, 4GB RAM) utilizing native network socket testing, up to 20x faster.
* **Auto-Discover Payload**
  Scrapes the target login page with BeautifulSoup, extracts form action, method, and input fields — auto-generates the raw POST payload with `^USER^` and `^PASS^` placeholders. Available in both CLI wizard and GUI.
* **Performance-Optimized Browser Engines**
  Even in browser mode, drivers are aggressively debloated—images disabled, background rendering off, UI throttled—making it lightweight for low-spec setups.
* **Auto CSS Selector Bindings**
  Includes a built-in browser-listener! Press `s` on any element to lock the Username target, and `t` to lock the Password target dynamically.
* **Multi-threaded Execution Engine**
  Spawns true parallel headless Chrome drivers simultaneously slicing through immense combos rapidly without RAM-locking. Seamlessly tears down and re-starts browser engines upon session death or successful authentication routes.
* **Intelligent Output Logs**
  Any successful session hit is aggressively parsed and cleanly appended to an integrated `credentials.txt` natively on the machine while bypassing subsequent multi-dimensional errors. Also supports explicit positive match handling (`--success`). Progress is tracked with a `[current/total]` counter so you always know where you're at.
* **Multi-User Continuation**
  Unlike tools that stop after the first hit, BlueCrack continues testing all remaining users after finding valid credentials. Every valid pair is saved to `credentials.txt` in real-time — even if you Ctrl+C mid-run.
* **Advanced Networking & Routing**
  * Auto Tor Proxy support (`socks5://127.0.0.1:9050`)
  * Dynamic IP Shifting logic (`Change IP every X attempts`) utilizing native Tor signals
  * Support for external `.txt` proxy arrays.
* **CUPP Integration & Sequence Generators**
  Built-in support for generating intelligent wordlists using `cupp.py` and a custom mathematical Sequence Generator that outputs sequential combinations natively inside the application.

---

## 🆚 BlueCrack vs. Hydra

When choosing a tool for authorized password assessment, it is important to understand the differences in architecture:

### 🐢 BlueCrack (Selenium Browser Mode)
* **The Approach**: BlueCrack completely mimics a human navigating a web browser. It renders the entire HTML/JS of a page and physically clicks the fields.
* **The Pros**: It can overcome complex modern authentication loops that rely on heavy JavaScript execution, hidden CSRF tokens, or multi-step React/Angular interactions that confuse traditional tools.
* **The Cons**: It is incredibly resource-heavy (RAM/CPU) since each thread requires its own entire customized Chrome engine to render. It is significantly slower than socket-based tools. 

### ⚡ Hydra (and BlueCrack "Raw" Mode)
* **The Approach**: Hydra doesn't care about what a website "looks" like. It ignores HTML and JavaScript completely, firing packets containing the raw username and password strings directly at the server's backend database API.
* **The Pros**: Blazing fast. Because it skips rendering the website, it requires almost zero RAM or CPU. It can execute thousands of attempts while a browser is still trying to load a single image.
* **The Cons**: If a website uses complex hashing algorithms on the frontend, hidden dynamic tokens, or encrypted handshakes before sending the payload, Hydra fails because it simply doesn't know how to run the required JavaScript to build the tokens. 

> *Note: By utilizing BlueCrack's new `--raw` mode from the CLI or GUI, it can emulate Hydra's packet-level speeds over raw network sockets without requiring an external C-library dependency.*

---

## 🛠 Installation

Install dependencies:
```bash
pip install -r requirements.txt
pip install requests PyQt6 stem selenium
```
Requirements:
* Python 3.10+
* Google Chrome
* PyQt6
* Selenium

---

## ▶ Usage

### GUI Mode
Launch the full desktop interface:
```bash
python bluecrack.py --gui
```

### Interactive Wizard (CLI)
```bash
python bluecrack.py -i
```
The wizard walks you through every option step-by-step — target, usernames, passwords, raw mode, proxy, rate-limit handling, etc.

### Direct CLI
```bash
# Raw HTTP mode (fastest) — single password against a user list
python bluecrack.py --url https://target.com/login -U users.txt -p password123 --raw --error "invalid" --threads 4

# Selenium browser mode — headless with auto-detect
python bluecrack.py --url https://target.com/login -u admin -P passwords.txt --headless --error "incorrect"

# With Tor proxy and custom payload
python bluecrack.py --url https://target.com/login -U users.txt -p pass --raw --data "email=^USER^&password=^PASS^" --proxy socks5://127.0.0.1:9050
```

### Stopping a Run
Press **Ctrl+C** at any time to gracefully stop. All credentials found so far are already saved to `credentials.txt`.

### GUI Workflow
1. **Target tab:** Enter URL, username(s), password(s)
2. **Engine tab:** Set threads, delay, error text. Enable Raw HTTP mode and use **Auto-Discover Payload** to scrape the login form automatically
3. **Network tab:** Configure Tor or proxy rotation
4. **CUPP tab:** Generate targeted wordlists or number sequences
5. Hit **START ATTACK** — progress streams to the log panel and all hits are saved to `credentials.txt`

---

## 🔐 Responsible Use Policy

BlueCrack is intended strictly for:
* Educational cybersecurity labs
* Personal research environments
* Authorized penetration testing
* Studying authentication system behavior

It must **never** be used against school portals, government systems, production websites, or any service without explicit written authorization.

---

## 📄 License

Included in the Repository.
