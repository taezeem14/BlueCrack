# BlueCrack

```
██████╗ ██╗     ██╗   ██╗███████╗  ██████╗██████╗  █████╗  ██████╗██╗  ██╗
██╔══██╗██║     ██║   ██║██╔════╝ ██╔════╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝
██████╔╝██║     ██║   ██║█████╗   ██║     ██████╔╝███████║██║     █████╔╝
██╔══██╗██║     ██║   ██║██╔══╝   ██║     ██╔══██╗██╔══██║██║     ██╔═██╗
██████╔╝███████╗╚██████╔╝███████╗ ╚██████╗██║  ██║██║  ██║╚██████╗██║  ██╗
╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
```

[![PyPI Version](https://img.shields.io/pypi/v/bluecrack.svg?style=flat-square)](https://pypi.org/project/bluecrack/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/bluecrack.svg?style=flat-square)](https://pypi.org/project/bluecrack/)
[![Python Versions](https://img.shields.io/pypi/pyversions/bluecrack.svg?style=flat-square)](https://pypi.org/project/bluecrack/)
[![License](https://img.shields.io/pypi/l/bluecrack.svg?style=flat-square)](https://github.com/taezeem14/BlueCrack/blob/main/LICENSE)
[![CI Status](https://github.com/taezeem14/BlueCrack/actions/workflows/publish.yml/badge.svg?branch=main)](https://github.com/taezeem14/BlueCrack/actions/workflows/publish.yml)


**BlueCrack** is an advanced, Hydra-style browser-based login tester powered by Selenium and Flask. By driving actual Google Chrome instances in parallel, BlueCrack automates credential auditing against complex authentication portals that traditional HTTP-based brute-forcers cannot handle. It is wrapped in a premium, ultra-responsive dark web console streaming real-time statistics and execution logs.

---

> ## ⚠️ Responsible Use Warning
>
> **BlueCrack is designed strictly for authorized security testing, educational research, and infrastructure auditing.** Unauthorized access to computer systems is illegal under international computer misuse laws (including the US CFAA and UK Computer Misuse Act). The developers assume **no liability** for misuse. Always obtain explicit written authorization before testing target environments.

---

## 🏗️ Architecture & Topology

Unlike simple script-based brute-forcers, BlueCrack implements a decoupled **Client-Server-Worker** model. The backend serves REST APIs and WebSockets to synchronize states, while thread-safe worker queues drive isolated automated browsers.

### System Topology Map

The diagram below illustrates the relationship between the client dashboard, the Flask server, the background attack engine, and the automation instances:

```mermaid
graph TD
    subgraph Client ["Client Browser (Frontend)"]
        UI["Web Dashboard (HTML5/CSS3)"]
        JS["app.js (Socket.IO client & state)"]
        UI <--> JS
    end

    subgraph Backend ["Python Server (Backend)"]
        App["app.py (Flask Web Server)"]
        Engine["engine.py (AttackEngine & callbacks)"]
        App <--> Engine
    end

    subgraph BrowserWorkers ["Browser Automation"]
        Driver1["Chrome WebDriver (Thread 1)"]
        Driver2["Chrome WebDriver (Thread 2)"]
        DriverN["Chrome WebDriver (Thread N)"]
    end

    subgraph TargetSystem ["Target Environment"]
        Target["Target Login Form"]
        DemoSrv["demo_server.py (Subprocess)"]
    end

    JS <-->|Socket.IO & REST APIs| App
    Engine -->|Spawns| Driver1
    Engine -->|Spawns| Driver2
    Engine -->|Spawns| DriverN

    Driver1 -->|Automates Login| Target
    Driver2 -->|Automates Login| Target
    DriverN -->|Automates Login| Target

    App -.->|Subprocess Popen| DemoSrv
    Driver1 -.->|Optionally tests| DemoSrv
```

### Attack Execution Data Flow

This sequence chart outlines the step-by-step lifecycle of an active credential audit:

```mermaid
sequenceDiagram
    autonumber
    actor User as Security Tester
    participant UI as Web Dashboard
    participant App as app.py (Flask)
    participant Queue as Thread-Safe Queue
    participant Engine as AttackEngine (engine.py)
    participant Worker as WebDriver Worker Thread
    participant Target as Target Login Webpage

    User->>UI: Input Target URL, Credentials & hit Start
    UI->>App: POST /api/attack/start (JSON config)
    App->>Engine: start(ctx)
    activate Engine
    Engine->>Queue: Populate (User, Pass) combos
    Engine->>Worker: Spawn N worker threads
    activate Worker

    loop Until Queue is empty or Stopped
        Queue->>Worker: Get next combo (user, pwd)
        Worker->>Target: Load login URL
        Worker->>Target: Auto-detect & inject User/Pass inputs
        Worker->>Target: Click Submit Button
        Worker->>Target: Inspect result page (DOM / Redirect)
        alt Success Detected
            Worker->>Engine: Log credentials found
            Engine->>App: Emit "log" & "finished"
            App->>UI: Stream live credentials & success sound
        else Rate Limit Detected
            Worker->>Engine: Report rate limit hit
            Engine->>App: Emit "log" & cooldown metrics
            App->>UI: Stream status & cooldown timer
            Note over Worker: Cooldown sleep or Tor circuit shift
        else Failure/Error
            Worker->>Engine: Record failure/error metric
            Engine->>App: Emit "progress" & "metrics"
            App->>UI: Update live ETA & counter stats
        end
    end

    deactivate Worker
    deactivate Engine
    Engine->>App: finished(success_flag)
    App->>UI: Socket.IO finished event (Enable buttons)
```

---

## 🎯 Features

### Core Capabilities
* **Full JavaScript Compatibility**: Handles React, Angular, Vue, and vanilla JS portals by rendering pages in full browser sessions.
* **Auto-Selector Engine**: Employs heuristic-based JS injection to automatically identify input fields for usernames, passwords, and submit buttons.
* **Tor Proxy & IP Shift**: Rotates IP addresses automatically using Tor circuits by communicating with the Tor Control Port.
* **Thread-Safe Concurrent Workers**: Run up to 50 concurrent headless or GUI browser instances with synchronized queue mechanisms.
* **Dynamic Rate-Limit Evasion**: Pause testing, add jitter, or cycle proxy gateways when encountering rate-limiting string triggers.
* **CUPP & Sequence Profilers**: Built-in credential profiling and sequential zero-padded range wordlist generators.

### Premium UI Enhancements
* **Lag-Free Logging**: Handles high-frequency console updates using `requestAnimationFrame` queue batching and `DocumentFragment` inserts to eliminate layout thrashing.
* **Cosmic Eco-Astral Theme**: Includes a stunning forest-green and celestial-purple space aesthetic toggle with persistent `LocalStorage` preferences.
* **Local Sandbox Mode**: Instantly launches a secure mock login server in the background and populates the dashboard for immediate training.

---

## 📁 Project Structure

```
BlueCrack/
├── pyproject.toml         # PEP 621 metadata & entry point definitions
├── MANIFEST.in            # Bundles static web templates & configuration data
├── LICENSE                # MIT Open Source License
├── requirements.txt       # Unified project dependency manifests
│
├── src/
│   └── bluecrack/         # Source code package
│       ├── __init__.py    # Version and API initialization
│       ├── __main__.py    # Entry point for python -m bluecrack
│       ├── cli.py         # Subcommand dispatcher
│       ├── web.py         # Flask Web UI & SocketIO bridge
│       ├── engine.py      # Core Selenium AttackEngine
│       ├── attack.py      # CLI brute-force execution flow
│       ├── demo.py        # Sandbox authentication server
│       ├── doctor.py      # System diagnostic check utility
│       ├── constants.py   # Shared scripts & ANSI styling
│       ├── utils.py       # Tor rotation, chromedriver & wordlist generation
│       │
│       ├── data/          # Embedded package configuration
│       │   ├── cupp.cfg   # Wordlist rules database
│       │   └── pass.txt   # Demo password list
│       │
│       ├── templates/     # Web templates
│       │   └── index.html # Glassmorphism dashboard
│       │
│       └── static/        # Static stylesheets & JS
│           ├── css/style.css
│           └── js/app.js
```

---

## 🛠️ Installation

### 1. From PyPI (Recommended)
You can install BlueCrack directly as an executable package:
```bash
pip install bluecrack
```

### 2. From Source (Development Mode)
Clone the repository and install it in editable mode:
```bash
git clone https://github.com/taezeem14/BlueCrack.git
cd BlueCrack
pip install -e .
```

### 3. Prerequisites
* **Python 3.9+**
* **Google Chrome Browser**
* **ChromeDriver** (Selenium Manager automatically fetches the correct version for you)

---

## ▶️ Usage Subcommands

After installation, the unified `bluecrack` binary is added to your terminal PATH.

### 1. 🌐 Web UI (Default)
Launch the graphical dashboard:
```bash
bluecrack
# or explicitly
bluecrack web --port 5000
```
Navigate to `http://127.0.0.1:5000` in your web browser.

### 2. ⌨️ CLI Attack Mode
Run dictionary attacks directly inside the terminal:
```bash
# Basic single login test
bluecrack attack -u admin -p admin123 --url http://target.local/login --error "wrong password"

# Multi-threaded dictionary attack
bluecrack attack -U users.txt -P rockyou.txt --url http://target.local/login \
    --success "Welcome" --threads 4 --headless
```

### 3. 🧙 Interactive Wizard Mode
Let the system guide you through setup step-by-step:
```bash
bluecrack attack -i
```

### 4. 🧪 Local Sandbox
Launch the demo login server on an isolated port:
```bash
bluecrack demo --port 5001 --max-attempts 3
```

### 5. 🩺 Doctor Diagnostic Tool
Check system dependencies, browser version, and chromedriver availability:
```bash
bluecrack doctor
```

### 6. 🔌 Plugin CLI Utilities
Generate sequences or run CUPP interactively:
```bash
bluecrack plugin cupp
bluecrack plugin sequence --start 1000 --end 9999 --output sequence.txt
```

---

## ⚙️ CLI Flag Reference (`bluecrack attack`)

| Flag | Parameter | Description |
|---|---|---|
| `-u`, `--user` | `TEXT` | Single target username |
| `-U`, `--userfile` | `FILE` | File containing list of usernames |
| `-p`, `--passw` | `TEXT` | Single password to test |
| `-P`, `--passlist` | `FILE` | File containing list of passwords |
| `--url` | `URL` | Web URL containing target login form |
| `--error` | `TEXT` | Substring on page indicating login failure |
| `--success` | `TEXT` | Substring on page indicating login success |
| `--threads` | `INT` | Parallel browser workers (default: 1) |
| `--headless` | `FLAG` | Runs browser without rendering UI windows |
| `--delay` | `FLOAT` | Throttling time delay in seconds |
| `--jitter` | `FLOAT` | Randomized variance added to the delay |
| `--limit-text` | `TEXT` | Substring indicating rate limits |
| `--cooldown` | `INT` | Wait time in seconds when rate limited |
| `--proxy` | `URL` | Single SOCKS/HTTP proxy server url |
| `--proxy-list` | `FILE` | File containing multiple proxy IPs |
| `--output` | `FILE` | Saves found credentials to output file |
| `--json-report` | `FLAG` | Exports full execution run history to JSON |

---

## 🧪 Local Sandbox Testing
To practice or demonstrate credential testing safely without hitting live servers:
1. Open the Web UI (`bluecrack`).
2. Click **`🚀 Demo Mode`** at the top right.
3. The server will spin up `bluecrack demo` in the background and auto-populate all target URLs and fields.
4. Click **`▶ Start Attack`** to watch the worker threads execute live!

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
