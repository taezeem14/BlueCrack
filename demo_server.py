#!/usr/bin/env python3
"""
A minimal Flask app providing a local test login page.

This demo server is intentionally simple and insecure by design;
it is only for local, educational testing and must NOT be exposed
to the public internet.
"""
from flask import Flask, request, render_template_string, redirect, url_for

import time

app = Flask(__name__)

# --- RATE LIMITING SIMULATION ---
ATTEMPT_TRACKER = {}
MAX_ATTEMPTS = 3
RATE_LIMIT_WINDOW = 10 # seconds

RATE_LIMIT_PAGE = """
<!doctype html>
<html lang="en">
<head>
    <title>Rate Limited</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-warning text-dark d-flex align-items-center justify-content-center vh-100">
    <div class="text-center">
        <h1 class="display-4 fw-bold">Too Many Requests</h1>
        <p class="lead">You are being rate limited. Please cool down for 10 seconds.</p>
        <a href="/" class="btn btn-dark mt-3">Try Again</a>
    </div>
</body>
</html>
"""

LOGIN_PAGE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Demo Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .login-card { width: 100%; max-width: 400px; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); background: white; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2 class="text-center mb-4 text-primary">Secure Portal</h2>
        <form method="post" action="/login">
            <div class="mb-3">
                <label class="form-label">Username</label>
                <input type="text" name="username" class="form-control" placeholder="Enter username" required />
            </div>
            <div class="mb-3">
                <label class="form-label">Password</label>
                <input type="password" name="password" class="form-control" placeholder="Enter password" required />
            </div>
            <button type="submit" class="btn btn-primary w-100">Login</button>
        </form>
    </div>
</body>
</html>
"""

SUCCESS_PAGE = """
<!doctype html>
<html lang="en">
<head>
    <title>Success</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-success text-white d-flex align-items-center justify-content-center vh-100">
    <div class="text-center">
        <h1 class="display-4">Login Successful!</h1>
        <p class="lead">Welcome securely, {{ user }}!</p>
        <a href="/" class="btn btn-light mt-3">Logout</a>
    </div>
</body>
</html>
"""

FAIL_PAGE = """
<!doctype html>
<html lang="en">
<head>
    <title>Failed</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-danger text-white d-flex align-items-center justify-content-center vh-100">
    <div class="text-center">
        <h1 class="display-4">Login Failed</h1>
        <p class="lead">Invalid credentials. Please try again.</p>
        <a href="/" class="btn btn-light mt-3">Go Back</a>
    </div>
</body>
</html>
"""

# Demo credentials (for local testing only)
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "password99"

@app.route("/login", methods=["GET", "POST"])
def login():
    client_ip = request.remote_addr
    now = time.time()
    
    # Check IP limits
    if client_ip in ATTEMPT_TRACKER:
        # Reset if window expired
        if now - ATTEMPT_TRACKER[client_ip]['start'] > RATE_LIMIT_WINDOW:
            ATTEMPT_TRACKER[client_ip] = {'count': 0, 'start': now}
    else:
        ATTEMPT_TRACKER[client_ip] = {'count': 0, 'start': now}
        
    # Increment counter conditionally on POST
    if request.method == "POST":
        ATTEMPT_TRACKER[client_ip]['count'] += 1
        # Block if exceeded rate limit criteria
        if ATTEMPT_TRACKER[client_ip]['count'] > MAX_ATTEMPTS:
            return render_template_string(RATE_LIMIT_PAGE), 429

    if request.method == "GET":
        return render_template_string(LOGIN_PAGE)
        
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if username == DEMO_USERNAME and password == DEMO_PASSWORD:
        return render_template_string(SUCCESS_PAGE, user=username)
    return render_template_string(FAIL_PAGE), 401

@app.route("/")
def index():
    return redirect(url_for("login"))

if __name__ == "__main__":
    # WARNING: Run only locally for demo purposes
    app.run(host="127.0.0.1", port=5000, debug=True)
