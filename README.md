# 🚀 BlueCrack – Browser-Based Login Security Testing Framework

BlueCrack is a Selenium-powered login security testing tool designed for controlled security research, educational environments, and authorized penetration testing.

It allows researchers and students to evaluate login form behavior inside a real browser (Chrome), analyze authentication responses, and study defensive mechanisms such as rate limiting and input validation.

> ⚠️ This tool must only be used in controlled lab environments or on systems where explicit written authorization has been granted.

---

## 🎯 Project Purpose

BlueCrack was built as an experimentation project to explore:

* Browser automation using Selenium
* Multi-threaded request coordination
* Login form state detection
* Rate limiting behavior
* Defensive mechanism analysis
* Wordlist-based credential testing logic

The focus is on understanding how authentication systems respond under repeated login attempts — not bypassing security controls.

---

## ✨ Core Features

* **Interactive Wizard Mode (`-i`)**
  Guided setup to configure targets, selectors, and wordlists.

* **CSS Selector Auto-Detection**
  Automatically identifies username and password fields in common login forms.

* **Manual Field Locking**
  Allows users to click and bind specific input elements when auto-detection fails.

* **Multi-threaded Execution (`--threads`)**
  Enables controlled parallel testing for analyzing rate limiting and server response patterns.

* **Headless Mode (`--headless`)**
  Runs browser instances invisibly for performance testing in lab environments.

* **Configurable Timing Controls**

  * `--delay` – Base delay between attempts
  * `--jitter` – Randomized delay variation to simulate non-uniform user behavior

* **Rate Limit Detection**

  * Detects HTTP 429 or custom limit text
  * Implements cooldown logic for controlled retry analysis

* **CUPP Integration**
  Supports integration with profile-based wordlist generation using `cupp.py` for password strength evaluation research.

---

## 📂 Repository Structure

```
BlueCrack/
│
├── bluecrack.py         # Main testing engine
├── cupp.py              # Profile-based wordlist generator
├── pass.txt             # Sample password list
├── demo_server.py       # Local Flask demo login app
├── requirements.txt     # Dependencies
└── README.md            # Documentation
```

---

## 🛠 Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

Requirements:

* Python 3.x
* Google Chrome
* ChromeDriver (matching your Chrome version)

---

## ▶ Usage

### Interactive Mode (Recommended for Learning)

```bash
python bluecrack.py -i
```

The wizard will:

* Configure target URL
* Detect or bind login fields
* Load wordlists
* Configure timing and threading

---

### CLI Mode

Single username + password list:

```bash
python bluecrack.py -u admin -P passlist.txt --threads 5 --url "http://localhost:5000/login"
```

Username list + password list:

```bash
python bluecrack.py -U users.txt -P passlist.txt --threads 10 --url "http://localhost:5000/login"
```

---

## 🧠 How It Works

1. Launches the target login page in Chrome.
2. Identifies or binds login input fields.
3. Iterates through credential combinations.
4. Monitors:

   * URL changes
   * Error message presence
   * Rate limit responses
5. Logs results for analysis.

The included `demo_server.py` provides a safe local Flask login app for controlled testing.

---

## 📜 Available Flags

| Flag                  | Description                                 |
| --------------------- | ------------------------------------------- |
| `-i`, `--interactive` | Launch interactive setup wizard             |
| `-u`, `--user`        | Single username                             |
| `-U`, `--userfile`    | File of usernames                           |
| `-p`, `--passw`       | Single password                             |
| `-P`, `--passlist`    | Password wordlist                           |
| `--threads`           | Number of parallel workers                  |
| `--delay`             | Base delay between attempts                 |
| `--jitter`            | Randomized delay variation                  |
| `--proxy`             | Optional proxy (for lab network simulation) |
| `--proxy-list`        | Proxy list file                             |
| `--url`               | Target login page                           |
| `--error`             | Failure detection string                    |
| `--limit-text`        | Rate limit detection string                 |
| `--cooldown`          | Cooldown duration after limit detected      |
| `--headless`          | Run browsers invisibly                      |

---

## 🔐 Responsible Use Policy

BlueCrack is intended strictly for:

* Educational cybersecurity labs
* Personal research environments
* Authorized penetration testing
* Studying authentication system behavior

It must **never** be used against:

* School portals
* Government systems
* Production websites
* Any service without explicit written authorization

Misuse may violate local laws and regulations.

---

## 📘 Learning Outcomes

This project demonstrates practical understanding of:

* Selenium automation
* Concurrency & threading
* State-based response detection
* Rate limiting analysis
* Authentication flow modeling
* Secure software testing concepts

---

## 📄 License

MIT License © 2025 Muhammad Taezeem Tariq
