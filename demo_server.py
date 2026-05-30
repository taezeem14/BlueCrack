#!/usr/bin/env python3
"""
BlueCrack v2.0 — Demo Login Server

A local Flask app providing a modern glassmorphism-themed login page
for testing BlueCrack against. Features CSRF token simulation,
multiple demo accounts, JSON API endpoint, and configurable rate limits.

This server is intentionally simple and insecure by design;
it is only for local, educational testing and must NOT be exposed
to the public internet.
"""

import argparse
import time
import uuid

from flask import Flask, request, render_template_string, redirect, url_for, jsonify

# ── CLI Configuration ──────────────────────────────────────────────
cli = argparse.ArgumentParser(description="BlueCrack Demo Login Server")
cli.add_argument(
    "--max-attempts",
    type=int,
    default=3,
    help="max login attempts before rate-limiting (default: 3)",
)
cli.add_argument(
    "--rate-window",
    type=int,
    default=10,
    help="rate-limit window in seconds (default: 10)",
)
cli.add_argument(
    "--port",
    type=int,
    default=5000,
    help="port to run the server on (default: 5000)",
)
cli_args = cli.parse_args()

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

# ── Rate Limiting ──────────────────────────────────────────────────
ATTEMPT_TRACKER: dict = {}
MAX_ATTEMPTS: int = cli_args.max_attempts
RATE_LIMIT_WINDOW: int = cli_args.rate_window

# ── Demo Credentials (local testing only) ──────────────────────────
DEMO_ACCOUNTS: dict[str, str] = {
    "demo": "password99",
    "admin": "admin123",
    "test": "test456",
}

# ── CSRF Token Store ──────────────────────────────────────────────
CSRF_TOKENS: set[str] = set()

# ═══════════════════════════════════════════════════════════════════
# HTML TEMPLATES — Dark Glassmorphism Theme
# ═══════════════════════════════════════════════════════════════════

_COMMON_STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #0a0e17 0%, #1a1a2e 50%, #0a0e17 100%);
        overflow: hidden;
    }

    /* Animated background orbs */
    body::before, body::after {
        content: '';
        position: fixed;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.15;
        z-index: 0;
        animation: drift 20s ease-in-out infinite alternate;
    }
    body::before {
        width: 500px; height: 500px;
        background: #4f8cff;
        top: -150px; left: -150px;
    }
    body::after {
        width: 400px; height: 400px;
        background: #6366f1;
        bottom: -100px; right: -100px;
        animation-delay: -10s;
    }

    @keyframes drift {
        0%   { transform: translate(0, 0) scale(1); }
        100% { transform: translate(60px, 40px) scale(1.1); }
    }

    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-10px); }
    }

    .glass-card {
        position: relative;
        z-index: 1;
        width: 100%;
        max-width: 420px;
        padding: 2.5rem 2rem;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow:
            0 8px 32px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        animation: float 6s ease-in-out infinite;
    }

    .glass-card h2 {
        text-align: center;
        margin-bottom: 0.25rem;
        font-weight: 700;
        font-size: 1.75rem;
        letter-spacing: -0.5px;
    }

    .glass-card .subtitle {
        text-align: center;
        font-size: 0.85rem;
        margin-bottom: 2rem;
        opacity: 0.5;
    }

    .glass-card .icon {
        text-align: center;
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    .glass-card p.lead {
        text-align: center;
        font-size: 1rem;
        opacity: 0.7;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }

    .btn-glass {
        display: inline-block;
        padding: 0.7rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.9rem;
        text-decoration: none;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .btn-glass:hover {
        background: rgba(255, 255, 255, 0.12);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
</style>
"""

LOGIN_PAGE = (
    """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Demo Login — BlueCrack</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    """
    + _COMMON_STYLES
    + """
    <style>
        .glass-card h2 {
            background: linear-gradient(135deg, #4f8cff, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .form-floating {
            position: relative;
            margin-bottom: 1.25rem;
        }

        .form-floating input {
            width: 100%;
            padding: 1rem 1rem 0.5rem;
            font-size: 0.95rem;
            color: #e2e8f0;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            outline: none;
            transition: border-color 0.3s ease, box-shadow 0.3s ease, background 0.3s ease;
            font-family: 'Inter', sans-serif;
        }

        .form-floating input:focus {
            border-color: #4f8cff;
            box-shadow: 0 0 0 3px rgba(79, 140, 255, 0.15);
            background: rgba(255, 255, 255, 0.06);
        }

        .form-floating label {
            position: absolute;
            top: 50%;
            left: 1rem;
            transform: translateY(-50%);
            color: rgba(255, 255, 255, 0.35);
            font-size: 0.9rem;
            pointer-events: none;
            transition: all 0.3s ease;
        }

        .form-floating input:focus + label,
        .form-floating input:not(:placeholder-shown) + label {
            top: 0.45rem;
            transform: translateY(0);
            font-size: 0.7rem;
            color: #4f8cff;
        }

        .btn-submit {
            width: 100%;
            padding: 0.85rem;
            border: none;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            color: #fff;
            background: linear-gradient(135deg, #4f8cff 0%, #6366f1 100%);
            cursor: pointer;
            transition: all 0.3s ease;
            letter-spacing: 0.5px;
            font-family: 'Inter', sans-serif;
            margin-top: 0.5rem;
        }

        .btn-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(79, 140, 255, 0.35);
        }

        .btn-submit:active {
            transform: translateY(0);
        }

        .demo-hint {
            text-align: center;
            margin-top: 1.5rem;
            font-size: 0.75rem;
            color: rgba(255, 255, 255, 0.25);
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="glass-card">
        <h2>Secure Portal</h2>
        <p class="subtitle">BlueCrack Demo Server</p>

        <form method="post" action="/login" autocomplete="off">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

            <div class="form-floating">
                <input type="text" name="username" id="username" placeholder=" " required autofocus>
                <label for="username">Username</label>
            </div>

            <div class="form-floating">
                <input type="password" name="password" id="password" placeholder=" " required>
                <label for="password">Password</label>
            </div>

            <button type="submit" class="btn-submit">Sign In</button>
        </form>

        <div class="demo-hint">
            Demo accounts: demo / password99 &nbsp;·&nbsp; admin / admin123 &nbsp;·&nbsp; test / test456
        </div>
    </div>
</body>
</html>
"""
)

SUCCESS_PAGE = (
    """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Login Successful</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    """
    + _COMMON_STYLES
    + """
    <style>
        body::before { background: #22c55e; }
        body::after  { background: #10b981; }

        .glass-card h2 { color: #4ade80; }
        .glass-card .icon { color: #4ade80; }
        .glass-card p.lead { color: #d1fae5; }
        .btn-glass { color: #4ade80; border-color: rgba(74, 222, 128, 0.2); }
        .btn-glass:hover { background: rgba(74, 222, 128, 0.1); color: #86efac; }

        .user-badge {
            display: inline-block;
            padding: 0.3rem 1rem;
            border-radius: 20px;
            background: rgba(74, 222, 128, 0.1);
            border: 1px solid rgba(74, 222, 128, 0.2);
            color: #4ade80;
            font-weight: 600;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="glass-card" style="text-align:center;">
        <div class="icon">✅</div>
        <h2>Login Successful!</h2>
        <br>
        <span class="user-badge">{{ user }}</span>
        <p class="lead">Welcome securely. Your session has been authenticated.</p>
        <a href="/" class="btn-glass">← Sign Out</a>
    </div>
</body>
</html>
"""
)

FAIL_PAGE = (
    """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Login Failed</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    """
    + _COMMON_STYLES
    + """
    <style>
        body::before { background: #ef4444; }
        body::after  { background: #dc2626; }

        .glass-card h2 { color: #f87171; }
        .glass-card .icon { color: #f87171; }
        .glass-card p.lead { color: #fecaca; }
        .btn-glass { color: #f87171; border-color: rgba(248, 113, 113, 0.2); }
        .btn-glass:hover { background: rgba(248, 113, 113, 0.1); color: #fca5a5; }
    </style>
</head>
<body>
    <div class="glass-card" style="text-align:center;">
        <div class="icon">❌</div>
        <h2>Login Failed</h2>
        <p class="lead">Invalid credentials. Please try again.</p>
        <a href="/" class="btn-glass">← Try Again</a>
    </div>
</body>
</html>
"""
)

RATE_LIMIT_PAGE = (
    """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Rate Limited</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    """
    + _COMMON_STYLES
    + """
    <style>
        body::before { background: #f59e0b; }
        body::after  { background: #d97706; }

        .glass-card h2 { color: #fbbf24; }
        .glass-card .icon { color: #fbbf24; }
        .glass-card p.lead { color: #fef3c7; }
        .btn-glass { color: #fbbf24; border-color: rgba(251, 191, 36, 0.2); }
        .btn-glass:hover { background: rgba(251, 191, 36, 0.1); color: #fcd34d; }

        .countdown {
            font-size: 2.5rem;
            font-weight: 700;
            color: #fbbf24;
            margin: 1rem 0;
            font-variant-numeric: tabular-nums;
        }
    </style>
</head>
<body>
    <div class="glass-card" style="text-align:center;">
        <div class="icon">⚠️</div>
        <h2>Too Many Requests</h2>
        <div class="countdown" id="timer">"""
    + str(RATE_LIMIT_WINDOW)
    + """</div>
        <p class="lead">You are being rate limited.<br>Please cool down before retrying.</p>
        <a href="/" class="btn-glass">← Try Again</a>
    </div>

    <script>
        (function() {
            let s = """
    + str(RATE_LIMIT_WINDOW)
    + """;
            const el = document.getElementById('timer');
            const iv = setInterval(() => {
                s--;
                el.textContent = s;
                if (s <= 0) { clearInterval(iv); el.textContent = '0'; }
            }, 1000);
        })();
    </script>
</body>
</html>
"""
)

CSRF_FAIL_PAGE = (
    """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>CSRF Validation Failed</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    """
    + _COMMON_STYLES
    + """
    <style>
        body::before { background: #ef4444; }
        body::after  { background: #dc2626; }

        .glass-card h2 { color: #f87171; }
        .glass-card .icon { color: #f87171; }
        .glass-card p.lead { color: #fecaca; }
        .btn-glass { color: #f87171; border-color: rgba(248, 113, 113, 0.2); }
        .btn-glass:hover { background: rgba(248, 113, 113, 0.1); color: #fca5a5; }
    </style>
</head>
<body>
    <div class="glass-card" style="text-align:center;">
        <div class="icon">🛡️</div>
        <h2>CSRF Token Invalid</h2>
        <p class="lead">Your session token has expired or is invalid.<br>Please reload the page and try again.</p>
        <a href="/" class="btn-glass">← Reload</a>
    </div>
</body>
</html>
"""
)


# ═══════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════


def _check_rate_limit(client_ip: str) -> bool:
    """Return True if the client is rate-limited."""
    now = time.time()
    if client_ip in ATTEMPT_TRACKER:
        if now - ATTEMPT_TRACKER[client_ip]["start"] > RATE_LIMIT_WINDOW:
            ATTEMPT_TRACKER[client_ip] = {"count": 0, "start": now}
    else:
        ATTEMPT_TRACKER[client_ip] = {"count": 0, "start": now}

    ATTEMPT_TRACKER[client_ip]["count"] += 1
    return ATTEMPT_TRACKER[client_ip]["count"] > MAX_ATTEMPTS


def _validate_credentials(username: str, password: str) -> bool:
    """Check username/password against demo accounts."""
    return DEMO_ACCOUNTS.get(username) == password


@app.route("/")
def index():
    """Redirect root to the login page."""
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Render the login form (GET) or process login (POST)."""
    client_ip = request.remote_addr

    # ── GET: render login page with fresh CSRF token ──
    if request.method == "GET":
        token = str(uuid.uuid4())
        CSRF_TOKENS.add(token)
        return render_template_string(LOGIN_PAGE, csrf_token=token)

    # ── POST: validate login ──
    # Rate-limit check
    if _check_rate_limit(client_ip):
        return render_template_string(RATE_LIMIT_PAGE), 429

    # CSRF check
    submitted_token = request.form.get("csrf_token", "")
    if submitted_token not in CSRF_TOKENS:
        return render_template_string(CSRF_FAIL_PAGE), 403
    CSRF_TOKENS.discard(submitted_token)

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if _validate_credentials(username, password):
        return render_template_string(SUCCESS_PAGE, user=username)

    return render_template_string(FAIL_PAGE), 401


@app.route("/api/login", methods=["POST"])
def api_login():
    """JSON API endpoint for programmatic login testing."""
    client_ip = request.remote_addr

    # Rate-limit check
    if _check_rate_limit(client_ip):
        return jsonify({
            "success": False,
            "error": "too many requests",
            "message": f"Rate limited. Try again in {RATE_LIMIT_WINDOW} seconds.",
        }), 429

    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    if not username or not password:
        return jsonify({
            "success": False,
            "error": "missing_fields",
            "message": "Both 'username' and 'password' are required.",
        }), 400

    if _validate_credentials(username, password):
        return jsonify({
            "success": True,
            "message": f"Login successful. Welcome, {username}!",
            "user": username,
        }), 200

    return jsonify({
        "success": False,
        "error": "invalid_credentials",
        "message": "Invalid credentials. Please try again.",
    }), 401


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"\n  BlueCrack Demo Server v2.0")
    print(f"  ─────────────────────────────────────")
    print(f"  Port:          {cli_args.port}")
    print(f"  Max attempts:  {MAX_ATTEMPTS}")
    print(f"  Rate window:   {RATE_LIMIT_WINDOW}s")
    print(f"  Accounts:      {', '.join(DEMO_ACCOUNTS.keys())}")
    print(f"  JSON API:      POST /api/login")
    print(f"  ─────────────────────────────────────\n")

    # WARNING: Run only locally for demo purposes
    app.run(host="127.0.0.1", port=cli_args.port, debug=True)
