#!/usr/bin/env python3
"""
A minimal Flask app providing a local test login page.

This demo server is intentionally simple and insecure by design;
it is only for local, educational testing and must NOT be exposed
to the public internet.
"""
from flask import Flask, request, render_template_string, redirect, url_for

app = Flask(__name__)

LOGIN_PAGE = """
<!doctype html>
<title>Demo Login</title>
<h1>Demo Login</h1>
<form method="post" action="/login">
  <label>Username: <input name="username" /></label><br/>
  <label>Password: <input name="password" type="password" /></label><br/>
  <button type="submit">Login</button>
</form>
"""

SUCCESS_PAGE = """
<!doctype html>
<title>Success</title>
<h1>Login successful</h1>
<p>Welcome, {{ user }}!</p>
"""

FAIL_PAGE = """
<!doctype html>
<title>Failed</title>
<h1>Login failed</h1>
<p>Invalid credentials.</p>
"""

# Demo credentials (for local testing only)
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "password123"

@app.route("/login", methods=["GET", "POST"])
def login():
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
