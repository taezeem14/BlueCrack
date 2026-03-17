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
* **Auto CSS Selector Bindings**
  Includes a built-in browser-listener! Press `s` on any element to lock the Username target, and `t` to lock the Password target dynamically.
* **Multi-threaded Execution Engine**
  Spawns true parallel headless Chrome drivers simultaneously slicing through immense combos rapidly without RAM-locking. Seamlessly tears down and re-starts browser engines upon session death or successful authentication routes.
* **Intelligent Output Logs**
  Any successful session hit is aggressively parsed and cleanly appended to an integrated `credentials.txt` natively on the machine while bypassing subsequent multi-dimensional errors.
* **Advanced Networking & Routing**
  * Auto Tor Proxy support (`socks5://127.0.0.1:9050`)
  * Dynamic IP Shifting logic (`Change IP every X attempts`) utilizing native Tor signals
  * Support for external `.txt` proxy arrays.
* **CUPP Integration & Sequence Generators**
  Built-in support for generating intelligent wordlists using `cupp.py` and a custom mathematical Sequence Generator that outputs sequential combinations natively inside the application.

---

## 🛠 Installation

Install dependencies:
```bash
pip install -r requirements.txt
```
Requirements:
* Python 3.10+
* Google Chrome
* PyQt6
* Selenium

---

## ▶ Usage

Launch the GUI interface:

```bash
python bluecrack.py
```

1. **Target Setup:** Map your target URL. The browser will spawn to allow you to detect fields. Hover over login fields, pressing `s` and `t` respectively.
2. **Payload Settings:** Map your isolated Usernames, Passwords, or load external dictionary arrays. Single passwords traversing 100K users or isolated combos. 
3. **Engine Settings:** Dial in your `delay`, browser pool `threads`, headless invisibility triggers, and rate-detection string limits (e.g. `Too many attempts`). 
4. **Deploy:** Hit Start Attack! Output streams directly to your console logs and exports all valid credentials to `credentials.txt`.

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
