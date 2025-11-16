# 🚀 **BlueCrack – Browser‑Based Login Tester**

*A Selenium‑powered login testing tool inspired by Hydra workflows.*

BlueCrack lets you test login forms **inside a real browser** (Chrome), without headless mode, without manually inspecting elements.
You just **click the input fields**, lock the selectors, load your wordlist, and start testing inside the browser UI.

⚠️ **For educational + authorized testing only.**

---

## ✨ Features

* Click‑to‑Select username & password fields
* Auto‑generates CSS selectors from clicked elements
* Multi‑threaded testing (Hydra‑style `--threads`)
* Full browser automation using Selenium
* Real‑time attempt logging
* Works on any HTML login form (no rate‑limit = faster)

---

## 📂 Repository Structure

```
BlueCrack/
│
├── bluecrack.py        # Main brute testing engine
├── requirements.txt     # Selenium + keyboard + dependencies
└── README.md            # You are reading this
```

---

## 🛠️ Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

Make sure Chrome + ChromeDriver are installed.

---

## ▶️ Usage
```
### Single username + passlist
python bluecrack.py -u USERNAME -P PASSLIST.txt --threads 10 --url "https://target.com/login"

### Userlist + single pass
python bluecrack.py -U USERLIST.txt -p PASSWORD --threads 10 --url "https://target.com/login"

### Userlist + passlist
python bluecrack.py -U USERLIST.txt -P PASSLIST.txt --threads 10 --url "https://target.com/login"

### Single username + single password
python bluecrack.py -u USERNAME -p PASSWORD --threads 10 --url "https://target.com/login"
```

### Example:

```bash
python bluecrack.py --u admin --wordlist passwords.txt --threads 5 --url "http://localhost/login"
```

---

## 🧩 How It Works

1. Launches the target login page in Chrome.
2. You click the username field → press **S**.
3. You click the password field → press **T**.
4. Press **ENTER** to begin.
5. Threads start submitting credentials inside the live browser.
6. If a login does **not** trigger an “incorrect” message, it's marked as a possible success.

---

## 📜 Arguments

| Flag         | Description           |
| ------------ | --------------------- |
| `--u`        | Username to test with |
| `--wordlist` | Password list file    |
| `--threads`  | Thread count          |
| `--url`      | Login page URL        |

---

## ⚠️ Legal Disclaimer

This tool is for **educational**, **research**, and **authorized penetration testing** only.
Do **not** use it on systems you don't own or have permission to test.
