# BlueCrack

```
██████╗ ██╗     ██╗   ██╗███████╗  ██████╗██████╗  █████╗  ██████╗██╗  ██╗
██╔══██╗██║     ██║   ██║██╔════╝ ██╔════╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝
██████╔╝██║     ██║   ██║█████╗   ██║     ██████╔╝███████║██║     █████╔╝
██╔══██╗██║     ██║   ██║██╔══╝   ██║     ██╔══██╗██╔══██║██║     ██╔═██╗
██████╔╝███████╗╚██████╔╝███████╗ ╚██████╗██║  ██║██║  ██║╚██████╗██║  ██╗
╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
```

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**BlueCrack** is a Hydra-style browser-based login tester built with Selenium and PyQt6. It automates credential testing against web login forms using real browser sessions, supporting multi-threaded execution, Tor proxy integration, and intelligent rate-limit evasion — all wrapped in a modern glassmorphism dark-themed GUI.

---

> ## ⚠️ Responsible Use Warning
>
> **BlueCrack is designed strictly for authorized security testing, educational research, and penetration testing with explicit permission.** Unauthorized access to computer systems is illegal under laws including the CFAA (US), Computer Misuse Act (UK), and equivalent legislation worldwide. The authors assume **no liability** for misuse. Always obtain written authorization before testing any system you do not own.

---

## 🎯 Project Purpose

BlueCrack was created to provide security researchers and penetration testers with a browser-based credential testing tool that operates through real browser sessions rather than raw HTTP requests. This approach allows it to:

- **Handle JavaScript-heavy login pages** that traditional tools like Hydra cannot interact with
- **Bypass client-side protections** such as dynamic CSRF tokens, JavaScript form validation, and CAPTCHAs (with manual intervention)
- **Simulate realistic user behavior** with configurable delays, jitter, and user-agent rotation
- **Detect and adapt to rate limiting** by automatically cooling down or rotating Tor circuits

Unlike protocol-level brute forcers, BlueCrack drives actual Chrome browser instances, making it effective against modern web applications with complex authentication flows.

---

## ✨ Core Features

| Feature | Description |
|---|---|
| 🎨 **Glassmorphism Dark GUI** | Rich PyQt6 interface with frosted-glass panels, gradient accents, and a polished dark theme |
| 📊 **Live Stats Dashboard** | Real-time metrics — elapsed time, attempts/sec, ETA, hit counter, and progress bar |
| 🔍 **Auto CSS Selector Detection** | Automatically identifies username/password fields and submit buttons on any login page |
| ⚡ **Multi-Threaded Execution** | Parallel browser workers with configurable thread count (1–50) |
| 🔄 **Retry Budgets** | Per-credential retry limits (max 3) to prevent infinite loops on transient failures |
| ✅ **Success/Error Validation** | Detect login outcomes via configurable success strings, error messages, or URL redirects |
| 📋 **JSON Session Reports** | Auto-generated JSON reports with full session metadata, results, and timing data |
| 📝 **Export Logs** | One-click log export from the GUI for post-analysis |
| 🔑 **CUPP Wordlist Generator** | Built-in Common User Passwords Profiler for targeted wordlist generation |
| 🔢 **Sequence Generator** | Generate numeric/pattern-based wordlists with configurable ranges |
| 🧅 **Tor Proxy + Auto IP Rotation** | Route traffic through Tor with automatic circuit renewal every N attempts |
| 🛡️ **Rate-Limit Evasion** | Configurable cooldown timers, jitter, and proxy rotation on rate-limit detection |
| 🖥️ **Triple Mode Operation** | Full CLI with all flags, interactive wizard for guided setup, and GUI for visual control |
| 🚀 **Continue After Success** | Multi-user mode: keep testing remaining users after finding valid credentials |

---

## 🛠 Installation

### Prerequisites

- **Python 3.10+**
- **Google Chrome** (latest stable)
- **ChromeDriver** (matching your Chrome version — auto-managed by Selenium 4.15+)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install selenium>=4.15 stem>=1.8 keyboard>=0.13 flask>=3.0 PyQt6>=6.5 requests>=2.31
```

### Optional: Tor Setup

For Tor proxy support, install and configure Tor with a control port:

```bash
# Linux/macOS
sudo apt install tor    # or brew install tor
# Enable ControlPort 9051 in /etc/tor/torrc
```

---

## ▶ Usage

### 🖥️ GUI Mode (Default)

Launch the full graphical interface:

```bash
python bluecrack.py
```

Or explicitly:

```bash
python bluecrack.py --gui
```

The GUI provides tabbed configuration for target setup, engine settings, Tor proxy, CUPP wordlist generation, and number sequence generation — all with a live stats dashboard and log viewer.

### ⌨️ CLI Mode

Run fully from the command line with Hydra-style flags:

```bash
# Single username, single password
python bluecrack.py -u admin -p password123 --url https://target.com/login --error "incorrect"

# Username file + password file, 4 threads, headless
python bluecrack.py -U users.txt -P passwords.txt --url https://target.com/login \
    --error "invalid" --threads 4 --headless

# With success string validation
python bluecrack.py -u admin -P rockyou.txt --url https://target.com/login \
    --success "dashboard" --threads 2

# With delay, jitter, and rate-limit handling
python bluecrack.py -U users.txt -P pass.txt --url https://target.com/login \
    --error "failed" --delay 1.5 --jitter 0.5 --limit-text "too many requests" --cooldown 15

# With Tor proxy
python bluecrack.py -u admin -P pass.txt --url https://target.com/login \
    --error "incorrect" --proxy socks5://127.0.0.1:9050

# With max attempts and continue-after-success
python bluecrack.py -U users.txt -P pass.txt --url https://target.com/login \
    --error "failed" --max-attempts 100 --continue-after-success

# Export results
python bluecrack.py -u admin -P pass.txt --url https://target.com/login \
    --error "invalid" --output results.txt --json-report report.json
```

#### All CLI Flags

| Flag | Description |
|---|---|
| `-u`, `--user` | Single username to test |
| `-U`, `--userfile` | File containing usernames (one per line) |
| `-p`, `--passw` | Single password to test |
| `-P`, `--passlist` | File containing passwords (one per line) |
| `--url` | Target login page URL |
| `--error` | Error string to detect failed logins |
| `--success` | Success string to confirm valid logins |
| `--threads` | Number of parallel browser threads (default: 1) |
| `--headless` | Run browsers in headless mode (no visible window) |
| `--delay` | Delay between attempts in seconds (default: 0) |
| `--jitter` | Random jitter added to delay (default: 0) |
| `--limit-text` | Text indicating rate limiting (default: "too many requests") |
| `--cooldown` | Seconds to wait after rate limit hit (default: 12) |
| `--proxy` | Single proxy URL (e.g., `http://12.34.56.78:8080`) |
| `--proxy-list` | File containing proxy URLs to rotate |
| `--max-attempts` | Maximum total attempts before stopping |
| `--continue-after-success` | Keep testing after finding valid credentials |
| `--output` | Save found credentials to specified file |
| `--json-report` | Generate JSON session report at specified path |
| `-i`, `--interactive` | Launch the interactive setup wizard |
| `--gui` | Launch the PyQt6 GUI |

### 🧙 Interactive Wizard

For guided setup with step-by-step prompts:

```bash
python bluecrack.py -i
```

The wizard will walk you through configuring the target URL, credentials, engine settings, and optional Tor/proxy configuration.

### 🧪 Demo Server

Start the included Flask demo server for safe, local testing:

```bash
# Default settings (port 5000, 3 max attempts, 10s rate window)
python demo_server.py

# Custom configuration
python demo_server.py --port 8080 --max-attempts 5 --rate-window 30
```

**Demo accounts:** `demo/password99`, `admin/admin123`, `test/test456`

**Endpoints:**
- `GET /login` — Glassmorphism-themed login page with CSRF token
- `POST /login` — Form-based login (validates CSRF token)
- `POST /api/login` — JSON API endpoint (`{"username": "...", "password": "..."}`)

---

## 📊 What's New

- 🎨 **Complete GUI redesign** with glassmorphism dark theme and gradient accents
- 📊 **Live stats dashboard** — elapsed time, speed (attempts/sec), ETA, and hit counter
- ✅ **Success-string validation** for reliable login outcome detection
- 🔄 **Retry budgets** (max 3 retries per credential) to prevent infinite loops
- 🧵 **Thread-safe credential tracking** with `threading.Event` for the `found` state
- 🔁 **Graceful WebDriver restart** with exponential backoff on crashes
- 🔗 **URL redirect detection** heuristic for login success verification
- 📝 **JSON session reports** with full metadata, timing, and results
- 📋 **Export log button** for one-click log file saving
- 🎯 **Max attempts limiter** to cap total credential tests
- ▶️ **Continue-after-success mode** for multi-user testing campaigns
- 🌈 **Colored CLI output** with progress counter and status indicators
- 🖥️ **New CLI flags:** `--max-attempts`, `--continue-after-success`, `--output`, `--json-report`
- 🧪 **Enhanced demo server:** multiple accounts, CSRF simulation, JSON API, glassmorphism theme
- 📄 **Added Changelog** for update tracking

---

## 🔐 Responsible Use Policy

BlueCrack is a security research tool. By using this software, you agree to:

1. **Only test systems you own** or have **explicit written authorization** to test
2. **Never use this tool for unauthorized access** to any computer system or network
3. **Comply with all applicable laws** in your jurisdiction, including but not limited to:
   - Computer Fraud and Abuse Act (CFAA) — United States
   - Computer Misuse Act 1990 — United Kingdom
   - StGB §202a–c — Germany
   - Equivalent legislation in your country
4. **Accept full responsibility** for any actions taken using this tool
5. **Report vulnerabilities responsibly** through proper disclosure channels

The developers of BlueCrack:
- Provide this tool **"as-is"** for educational and authorized testing purposes only
- Accept **no liability** for damages resulting from misuse
- Actively **discourage** any illegal or unethical use

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025–2026 Muhammad Taezeem Tariq

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👤 Author

**Muhammad Taezeem Tariq**

---

<p align="center">
  <sub>Built with ❤️ for the security research community</sub>
</p>
