"""
BlueCrack Demo Login Server
============================
A local Flask app providing a modern glassmorphism-themed login page
for testing BlueCrack against. Features CSRF token simulation,
multiple demo accounts, JSON API endpoint, and configurable rate limits.
"""

import argparse
import time
import uuid
from flask import Flask, request, render_template_string, redirect, url_for, jsonify

# ═══════════════════════════════════════════════════════════════════
# GLOBALS & APP INITIALIZATION
# ═══════════════════════════════════════════════════════════════════
app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

# Rate Limiting & Demo settings
ATTEMPT_TRACKER: dict = {}
MAX_ATTEMPTS: int = 3
RATE_LIMIT_WINDOW: int = 10

DEMO_ACCOUNTS: dict[str, str] = {
    "demo": "password99",
    "admin": "admin123",
    "test": "test456",
}

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
        position: absolute;
        width: 300px;
        height: 300px;
        border-radius: 50%;
        filter: blur(100px);
        z-index: -1;
        animation: float-around 20s infinite alternate;
    }

    body::before {
        background: #4f46e5;
        top: 15%;
        left: 20%;
    }

    body::after {
        background: #06b6d4;
        bottom: 15%;
        right: 20%;
        animation-delay: -10s;
    }

    @keyframes float-around {
        0% { transform: translate(0, 0) scale(1); }
        100% { transform: translate(50px, 50px) scale(1.2); }
    }

    .glass-card {
        background: rgba(15, 23, 42, 0.45);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 40px;
        width: 100%;
        max-width: 420px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        text-align: left;
    }

    .icon {
        font-size: 3rem;
        margin-bottom: 20px;
        text-align: center;
    }

    h2 {
        color: #fff;
        font-weight: 700;
        font-size: 1.8rem;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
        text-align: center;
    }

    p.lead {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 30px;
        text-align: center;
        line-height: 1.5;
    }

    .form-group {
        margin-bottom: 20px;
        position: relative;
    }

    .form-group label {
        display: block;
        color: #94a3b8;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }

    .form-control {
        width: 100%;
        padding: 12px 16px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: #fff;
        font-family: inherit;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }

    .form-control:focus {
        outline: none;
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }

    .btn-glass {
        display: block;
        width: 100%;
        padding: 14px;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        border: none;
        border-radius: 8px;
        color: #fff;
        font-family: inherit;
        font-size: 0.95rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        text-decoration: none;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }

    .btn-glass:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
    }

    .btn-glass:active {
        transform: translateY(0);
    }

    .alert {
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-size: 0.88rem;
        line-height: 1.4;
    }

    .alert-danger {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.25);
        color: #fca5a5;
    }

    .alert-success {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.25);
        color: #6ee7b7;
    }
</style>
"""

LOGIN_PAGE = (
    """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Secure Vault — Access Portal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """
    + _COMMON_STYLES
    + """
</head>
<body>
    <div class="glass-card">
        <div class="icon">🔒</div>
        <h2>Access Portal</h2>
        <p class="lead">Audit Environment Login Page</p>
        
        <form action="/login" method="POST" id="loginForm">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" class="form-control" placeholder="Audit target..." required autocomplete="off">
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" class="form-control" placeholder="••••••••" required autocomplete="off">
            </div>
            
            <button type="submit" class="btn-glass">Sign In</button>
        </form>
    </div>
</body>
</html>
"""
)

SUCCESS_PAGE = (
    """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Access Granted</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """
    + _COMMON_STYLES
    + """
    <style>
        body::before { background: #10b981; }
        body::after  { background: #059669; }
    </style>
</head>
<body>
    <div class="glass-card" style="text-align:center;">
        <div class="icon">🔓</div>
        <h2>Access Granted</h2>
        <p class="lead">Successful Authentication</p>
        <div class="alert alert-success">
            <strong>Welcome, {{ user }}!</strong><br>
            Audit signature verified. Access logged successfully.
        </div>
        <a href="/" class="btn-glass">← Return to Portal</a>
    </div>
</body>
</html>
"""
)

FAIL_PAGE = (
    """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Access Denied</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """
    + _COMMON_STYLES
    + """
    <style>
        body::before { background: #ef4444; }
        body::after  { background: #dc2626; }
    </style>
</head>
<body>
    <div class="glass-card" style="text-align:center;">
        <div class="icon">🚫</div>
        <h2>Access Denied</h2>
        <p class="lead">Failed Authentication</p>
        <div class="alert alert-danger">
            <strong>Invalid credentials</strong><br>
            Please check your audit params and try again.
        </div>
        <a href="/" class="btn-glass">← Retry</a>
    </div>
</body>
</html>
"""
)

RATE_LIMIT_PAGE = (
    """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Rate Limit Exceeded</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """
    + _COMMON_STYLES
    + """
    <style>
        body::before { background: #f59e0b; }
        body::after  { background: #d97706; }
    </style>
</head>
<body>
    <div class="glass-card" style="text-align:center;">
        <div class="icon">⏳</div>
        <h2>Rate Limited</h2>
        <p class="lead">Too Many Requests</p>
        <div class="alert alert-danger" style="background:rgba(245,158,11,0.15); border-color:rgba(245,158,11,0.25); color:#fde68a;">
            <strong>too many requests</strong><br>
            Security throttle activated. Please wait before retrying.
        </div>
        <a href="/" class="btn-glass" style="background:linear-gradient(135deg, #f59e0b 0%, #d97706 100%); box-shadow:0 4px 12px rgba(217,119,6,0.3);">← Try Again</a>
    </div>
</body>
</html>
"""
)

CSRF_FAIL_PAGE = (
    """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CSRF Token Validation Failed</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
# HELPER ACTIONS & ROUTES
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

    # GET: render login page with fresh CSRF token
    if request.method == "GET":
        token = str(uuid.uuid4())
        CSRF_TOKENS.add(token)
        return render_template_string(LOGIN_PAGE, csrf_token=token)

    # POST: validate login
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
# SERVER RUNNERS
# ═══════════════════════════════════════════════════════════════════
def run_demo(port: int = 5001, max_attempts: int = 3, rate_window: int = 10) -> None:
    """Set configurations and launch the Flask app."""
    global MAX_ATTEMPTS, RATE_LIMIT_WINDOW
    MAX_ATTEMPTS = max_attempts
    RATE_LIMIT_WINDOW = rate_window

    print(f"\n  BlueCrack Demo Server")
    print(f"  -------------------------------------")
    print(f"  Port:          {port}")
    print(f"  Max attempts:  {MAX_ATTEMPTS}")
    print(f"  Rate window:   {RATE_LIMIT_WINDOW}s")
    print(f"  Accounts:      {', '.join(DEMO_ACCOUNTS.keys())}")
    print(f"  JSON API:      POST /api/login")
    print(f"  -------------------------------------\n")

    # Run app locally only
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BlueCrack Demo Login Server")
    parser.add_argument(
        "--port", type=int, default=5001, help="Port to run on (default: 5001)"
    )
    parser.add_argument(
        "--max-attempts", type=int, default=3, help="Attempts before limit"
    )
    parser.add_argument(
        "--rate-window", type=int, default=10, help="Rate limit window"
    )
    args = parser.parse_args()

    run_demo(args.port, args.max_attempts, args.rate_window)
