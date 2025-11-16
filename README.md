# Browser Automation Demo (Safe & Educational)

A small, safe demonstration repository that shows how to automate a single login attempt using Selenium against a local test server. This project is intended for learning, development, and defensive testing only.

Important: This repository does NOT include or support credential stuffing, brute-force testing, or any other automated attack techniques. If you need to perform stress or security testing against systems you own, consult a professional and obtain written authorization. Misuse may be illegal.

## Contents

- demo_server.py — Simple Flask app that exposes a local test login page.
- bluecrack.py — A minimal Selenium script to perform a single login attempt against the demo server.
- README.md — This file.

## Features

- Safe local demo environment (Flask).
- Clean, minimal Selenium example for automation and integration testing.
- Clear instructions and ethical usage guidance.

## Prerequisites

- Python 3.8+
- pip
- Google Chrome and chromedriver (matching Chrome version) in your PATH, or adjust the code to point to your webdriver executable.
- Recommended virtualenv to isolate dependencies.

Install Python dependencies:

```bash
pip install -r requirements.txt
# or
pip install flask selenium
```

(There is no requirements.txt in this skeleton; install the minimal dependencies above.)

## Running the demo (local, safe)

1. Start the demo server (in a terminal):

```bash
python demo_server.py
```

The server starts on http://127.0.0.1:5000 and exposes a simple login form. The correct credential for the demo is:

- Username: demo
- Password: password123

2. In a separate terminal, run the Selenium demo:

```bash
python bluecrack.py --url http://127.0.0.1:5000/login --user demo
```

This will open a Chrome window, fill the username and password, submit the form, and print the server's response. The demo performs a single, explicit login attempt so you can learn Selenium interactions without engaging in abusive behavior.

## Security & Ethics

- Only ever run automated tests against systems you own or have explicit written permission to test.
- This repository is for learning and local testing only.
- If you need to perform authorized security testing, follow a formal authorization process (scope, rules of engagement, and reporting) and use established tools and frameworks.

## Contributing

Contributions are welcome for the safe demo and documentation. Please do not submit code that automates brute-force attacks or otherwise facilitates unauthorized access.

## License

Specify a license for your project here (e.g., MIT). This repository contains only educational code and documentation.
