"""
BlueCrack Demo Testing Server
===============================
A local Flask app serving as a comprehensive multi-feature testing sandbox.
Supports:
  - Standard HTML form with CSRF validation (`/login`)
  - Redirect on Success authentication model (`/login-redirect`)
  - Custom Form Field names validation (`/login-custom`)
  - JSON API endpoints (`/api/login` and `/login-json`)
  - Aggressive Rate-Limiting mock target (`/login-rate-limited`)
  - Custom Headers required mock target (`/login-headers`)
  - Live statistics dashboard home page (`/`)
"""

import argparse
import threading
import time
import uuid
from typing import Dict

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

# ═══════════════════════════════════════════════════════════════════
# GLOBALS & APP INITIALIZATION
# ═══════════════════════════════════════════════════════════════════
app = Flask(__name__)
app.secret_key = uuid.uuid4().hex
_demo_lock = threading.Lock()

# Rate Limiting & Demo settings
ATTEMPT_TRACKER: dict = {}
MAX_ATTEMPTS: int = 3
RATE_LIMIT_WINDOW: int = 10

# Live Stats Tracker for sandbox audit testing
STATS: Dict[str, int] = {
    "total_attempts": 0,
    "successes": 0,
    "failures": 0,
    "rate_limits": 0,
    "csrf_blocks": 0,
    "header_blocks": 0,
}

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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }

    :root {
        --indigo: #6366f1;
        --emerald: #10b981;
        --rose: #f43f5e;
        --amber: #f59e0b;
        --slate-900: #0f172a;
    }

    body {
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #0a0e17 0%, #16192b 50%, #0a0e17 100%);
        color: #f8fafc;
        padding: 40px 20px;
        position: relative;
    }

    /* Animated background orbs */
    body::before, body::after {
        content: '';
        position: absolute;
        width: 350px;
        height: 350px;
        border-radius: 50%;
        filter: blur(120px);
        z-index: -1;
        animation: float-around 25s infinite alternate;
    }

    body::before {
        background: rgba(99, 102, 241, 0.25);
        top: 10%;
        left: 15%;
    }

    body::after {
        background: rgba(6, 182, 212, 0.2);
        bottom: 10%;
        right: 15%;
        animation-delay: -12s;
    }

    @keyframes float-around {
        0% { transform: translate(0, 0) scale(1); }
        100% { transform: translate(60px, 40px) scale(1.15); }
    }

    .glass-card {
        background: rgba(15, 23, 42, 0.55);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 40px;
        width: 100%;
        max-width: 480px;
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.45);
        text-align: left;
    }

    .dashboard-card {
        max-width: 900px;
    }

    .icon {
        font-size: 2.5rem;
        margin-bottom: 16px;
        text-align: center;
    }

    h2 {
        color: #fff;
        font-weight: 700;
        font-size: 1.7rem;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
        text-align: center;
    }

    p.lead {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 24px;
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
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: #fff;
        font-family: inherit;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }

    .form-control:focus {
        outline: none;
        border-color: var(--indigo);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25);
    }

    .btn-glass {
        display: block;
        width: 100%;
        padding: 14px;
        background: linear-gradient(135deg, var(--indigo) 0%, #4f46e5 100%);
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
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);
    }

    .btn-glass:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.45);
    }

    .alert {
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    .alert-danger {
        background: rgba(244, 63, 94, 0.12);
        border: 1px solid rgba(244, 63, 94, 0.25);
        color: #fca5a5;
    }

    .alert-success {
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.25);
        color: #6ee7b7;
    }

    /* Grid layout for Dashboard */
    .grid-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 16px;
        margin-bottom: 30px;
    }

    .stat-box {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }

    .stat-box .number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #fff;
        margin-bottom: 4px;
        font-family: 'Fira Code', monospace;
    }

    .stat-box .label {
        font-size: 0.7rem;
        text-transform: uppercase;
        color: #94a3b8;
        font-weight: 600;
        letter-spacing: 0.05em;
    }

    .grid-endpoints {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
    }

    .endpoint-card {
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 20px;
        transition: all 0.3s ease;
    }

    .endpoint-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        background: rgba(15, 23, 42, 0.6);
        transform: translateY(-2px);
    }

    .endpoint-title {
        font-size: 1rem;
        font-weight: 700;
        color: #fff;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .endpoint-badge {
        font-size: 0.65rem;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 700;
        text-transform: uppercase;
    }

    .badge-post { background: rgba(99, 102, 241, 0.2); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); }
    .badge-redirect { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-json { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-lock { background: rgba(244, 63, 94, 0.2); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }

    .endpoint-desc {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-bottom: 12px;
        line-height: 1.4;
    }

    .endpoint-info {
        font-size: 0.72rem;
        font-family: 'Fira Code', monospace;
        background: rgba(0, 0, 0, 0.2);
        padding: 8px 10px;
        border-radius: 6px;
        color: #cbd5e1;
        margin-bottom: 12px;
        overflow-x: auto;
    }

    .endpoint-link {
        font-size: 0.8rem;
        color: var(--indigo);
        text-decoration: none;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .endpoint-link:hover {
        color: #818cf8;
        text-decoration: underline;
    }
</style>
"""

# ═══════════════════════════════════════════════════════════════════
# TEMPLATE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

INDEX_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BlueCrack Auditing Sandbox Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {{ common_styles | safe }}
</head>
<body>
    <div class="glass-card dashboard-card">
        <div class="icon">🌌</div>
        <h2>BlueCrack Testing Sandbox</h2>
        <p class="lead">Interactive local environment to verify all auditing engines, field selectors, and evasive capabilities.</p>

        <!-- Live Server Statistics -->
        <h3 style="color:#fff; font-size:1.1rem; margin-bottom:12px; font-weight:600;">📊 Live Audit Metrics</h3>
        <div class="grid-stats">
            <div class="stat-box">
                <div class="number">{{ stats.total_attempts }}</div>
                <div class="label">Attempts</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:var(--emerald);">{{ stats.successes }}</div>
                <div class="label">Successes</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:var(--rose);">{{ stats.failures }}</div>
                <div class="label">Failures</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:var(--amber);">{{ stats.rate_limits }}</div>
                <div class="label">Rate Limits</div>
            </div>
            <div class="stat-box">
                <div class="number" style="color:#a855f7;">{{ stats.csrf_blocks }}</div>
                <div class="label">CSRF Blocks</div>
            </div>
        </div>

        <!-- Testing Endpoints -->
        <h3 style="color:#fff; font-size:1.1rem; margin-bottom:12px; font-weight:600;">🔗 Configured Target Endpoints</h3>
        <div class="grid-endpoints">

            <!-- Standard Login -->
            <div class="endpoint-card">
                <div class="endpoint-title">
                    <span>Standard Portal</span>
                    <span class="endpoint-badge badge-post">POST</span>
                </div>
                <p class="endpoint-desc">Default login with active CSRF token validation and session checks.</p>
                <div class="endpoint-info">
                    Route: /login<br>
                    Fields: username, password, csrf_token
                </div>
                <a href="/login" class="endpoint-link">Open Target →</a>
            </div>

            <!-- Redirect Target -->
            <div class="endpoint-card">
                <div class="endpoint-title">
                    <span>Redirect Success</span>
                    <span class="endpoint-badge badge-redirect">302</span>
                </div>
                <p class="endpoint-desc">Returns a 302 redirect header upon successful auth instead of inline body strings.</p>
                <div class="endpoint-info">
                    Route: /login-redirect<br>
                    Success URL: /dashboard
                </div>
                <a href="/login-redirect" class="endpoint-link">Open Target →</a>
            </div>

            <!-- Custom Form Fields -->
            <div class="endpoint-card">
                <div class="endpoint-title">
                    <span>Custom Selectors</span>
                    <span class="endpoint-badge badge-post">CUSTOM</span>
                </div>
                <p class="endpoint-desc">Form field names mapped specifically to test manual attribute overrides.</p>
                <div class="endpoint-info">
                    Route: /login-custom<br>
                    Fields: user_id, pass_word, sec_token
                </div>
                <a href="/login-custom" class="endpoint-link">Open Target →</a>
            </div>

            <!-- JSON API Endpoint -->
            <div class="endpoint-card">
                <div class="endpoint-title">
                    <span>REST JSON API</span>
                    <span class="endpoint-badge badge-json">JSON</span>
                </div>
                <p class="endpoint-desc">Accepts both application/json payload and standard url-encoded parameters.</p>
                <div class="endpoint-info">
                    Route: /login-json<br>
                    Response: {"success": true/false}
                </div>
                <a href="/login-json" class="endpoint-link">Open Target →</a>
            </div>

            <!-- Rate-Limiter Target -->
            <div class="endpoint-card">
                <div class="endpoint-title">
                    <span>Aggressive Limits</span>
                    <span class="endpoint-badge badge-lock">LIMIT</span>
                </div>
                <p class="endpoint-desc">Triggers rate limit triggers after only 2 failures to test auto-throttle.</p>
                <div class="endpoint-info">
                    Route: /login-rate-limited<br>
                    Throttle: 2 attempts / 30s
                </div>
                <a href="/login-rate-limited" class="endpoint-link">Open Target →</a>
            </div>

            <!-- Custom Headers Target -->
            <div class="endpoint-card">
                <div class="endpoint-title">
                    <span>Headers Required</span>
                    <span class="endpoint-badge badge-lock">HEADERS</span>
                </div>
                <p class="endpoint-desc">Rejects all connections unless configured with custom audit headers.</p>
                <div class="endpoint-info">
                    Route: /login-headers<br>
                    Header: X-Custom-Audit: BlueCrack
                </div>
                <a href="/login-headers" class="endpoint-link">Open Target →</a>
            </div>

        </div>

        <div style="margin-top:24px; font-size:0.8rem; color:#94a3b8; text-align:center;">
            Demo Accounts: <code style="color:#fff; font-family:monospace;">admin / admin123</code> | <code style="color:#fff; font-family:monospace;">demo / password99</code>
        </div>
    </div>
</body>
</html>
"""

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {{ common_styles | safe }}
</head>
<body>
    <div class="glass-card">
        <div class="icon">{{ icon }}</div>
        <h2>{{ title }}</h2>
        <p class="lead">{{ desc }}</p>

        {% if error %}
            <div class="alert alert-danger">{{ error }}</div>
        {% endif %}

        <form action="{{ post_url }}" method="POST" id="loginForm">
            {% if csrf_field %}
                <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
            {% endif %}

            <div class="form-group">
                <label for="username">{{ user_label }}</label>
                <input type="text" id="username" name="{{ user_field }}" class="form-control" placeholder="Target username..." required autocomplete="off">
            </div>

            <div class="form-group">
                <label for="password">{{ pass_label }}</label>
                <input type="password" id="password" name="{{ pass_field }}" class="form-control" placeholder="••••••••" required autocomplete="off">
            </div>

            <button type="submit" class="btn-glass">Authenticate</button>
        </form>

        <a href="/" style="display:block; text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:20px; text-decoration:none;">← Return to Sandbox Dashboard</a>
    </div>
</body>
</html>
"""

SUCCESS_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Access Granted</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {{ common_styles | safe }}
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
        <a href="/" class="btn-glass">← Return to Dashboard</a>
    </div>
</body>
</html>
"""

FAIL_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Access Denied</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {{ common_styles | safe }}
</head>
<body>
    <div class="glass-card" style="text-align:center;">
        <div class="icon">🚫</div>
        <h2>Access Denied</h2>
        <p class="lead">Failed Authentication</p>
        <div class="alert alert-danger">
            <strong>{{ error or 'Invalid credentials' }}</strong><br>
            Please check your audit params and try again.
        </div>
        <a href="{{ return_url }}" class="btn-glass">← Retry</a>
    </div>
</body>
</html>
"""

RATE_LIMIT_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Rate Limit Exceeded</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {{ common_styles | safe }}
</head>
<body>
    <div class="glass-card" style="text-align:center;">
        <div class="icon">⏳</div>
        <h2>Rate Limited</h2>
        <p class="lead">Too Many Requests</p>
        <div class="alert alert-danger" style="background:rgba(245,158,11,0.12); border-color:rgba(245,158,11,0.25); color:#fde68a;">
            <strong>too many requests</strong><br>
            Security throttle activated. Please wait before retrying.
        </div>
        <a href="/" class="btn-glass" style="background:linear-gradient(135deg, #f59e0b 0%, #d97706 100%); box-shadow:0 4px 12px rgba(217,119,6,0.3);">← Try Again</a>
    </div>
</body>
</html>
"""

CSRF_FAIL_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CSRF Token Validation Failed</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {{ common_styles | safe }}
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

# ═══════════════════════════════════════════════════════════════════
# HELPER ACTIONS & ROUTES
# ═══════════════════════════════════════════════════════════════════
def _check_rate_limit(client_ip: str, limit: int = 3, window: int = 10) -> bool:
    """Return True if the client is rate-limited."""
    now = time.time()
    with _demo_lock:
        if client_ip in ATTEMPT_TRACKER:
            if now - ATTEMPT_TRACKER[client_ip]["start"] > window:
                ATTEMPT_TRACKER[client_ip] = {"count": 0, "start": now}
        else:
            ATTEMPT_TRACKER[client_ip] = {"count": 0, "start": now}

        ATTEMPT_TRACKER[client_ip]["count"] += 1
        return ATTEMPT_TRACKER[client_ip]["count"] > limit


def _validate_credentials(username: str, password: str) -> bool:
    """Check username/password against demo accounts."""
    return DEMO_ACCOUNTS.get(username) == password


@app.route("/")
def index():
    """Render the central testing control dashboard."""
    return render_template_string(
        INDEX_PAGE,
        common_styles=_COMMON_STYLES,
        stats=STATS,
    )


# ─── 1. Standard Login Endpoint ────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    """Default form login with CSRF token protection."""
    client_ip = request.remote_addr

    if request.method == "GET":
        token = str(uuid.uuid4())
        CSRF_TOKENS.add(token)
        return render_template_string(
            LOGIN_PAGE,
            common_styles=_COMMON_STYLES,
            title="Standard Portal",
            desc="Authentic login simulator with CSRF validation.",
            icon="🔒",
            post_url="/login",
            csrf_field="csrf_token",
            csrf_token=token,
            user_label="Username",
            user_field="username",
            pass_label="Password",
            pass_field="password",
        )

    # POST validation
    STATS["total_attempts"] += 1

    # Rate limiting (standard)
    if _check_rate_limit(client_ip, MAX_ATTEMPTS, RATE_LIMIT_WINDOW):
        STATS["rate_limits"] += 1
        return render_template_string(RATE_LIMIT_PAGE, common_styles=_COMMON_STYLES), 429

    # CSRF check
    submitted_token = request.form.get("csrf_token", "")
    if submitted_token not in CSRF_TOKENS:
        STATS["csrf_blocks"] += 1
        return render_template_string(CSRF_FAIL_PAGE, common_styles=_COMMON_STYLES), 403
    CSRF_TOKENS.discard(submitted_token)

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if _validate_credentials(username, password):
        STATS["successes"] += 1
        return render_template_string(SUCCESS_PAGE, common_styles=_COMMON_STYLES, user=username)

    STATS["failures"] += 1
    return render_template_string(
        FAIL_PAGE,
        common_styles=_COMMON_STYLES,
        return_url="/login",
    ), 401


# ─── 2. Redirect Success Endpoint ──────────────────────────────────
@app.route("/login-redirect", methods=["GET", "POST"])
def login_redirect():
    """Simulates targets that redirect to dashboard on successful authentication."""
    if request.method == "GET":
        return render_template_string(
            LOGIN_PAGE,
            common_styles=_COMMON_STYLES,
            title="Redirect Portal",
            desc="Redirects the browser using 302 header on successful login.",
            icon="🔄",
            post_url="/login-redirect",
            csrf_field="",
            user_label="Username",
            user_field="username",
            pass_label="Password",
            pass_field="password",
        )

    # POST validation
    STATS["total_attempts"] += 1
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if _validate_credentials(username, password):
        STATS["successes"] += 1
        return redirect(url_for("dashboard", user=username))

    STATS["failures"] += 1
    return redirect(url_for("denied"))


@app.route("/dashboard")
def dashboard():
    """Successful redirect destination."""
    user = request.args.get("user", "Guest")
    return render_template_string(SUCCESS_PAGE, common_styles=_COMMON_STYLES, user=user)


@app.route("/denied")
def denied():
    """Failed redirect destination."""
    return render_template_string(
        FAIL_PAGE,
        common_styles=_COMMON_STYLES,
        return_url="/login-redirect",
    ), 401


# ─── 3. Custom Fields Endpoint ─────────────────────────────────────
@app.route("/login-custom", methods=["GET", "POST"])
def login_custom():
    """Uses non-standard field names user_id and pass_word, and CSRF sec_token."""
    if request.method == "GET":
        token = str(uuid.uuid4())
        CSRF_TOKENS.add(token)
        return render_template_string(
            LOGIN_PAGE,
            common_styles=_COMMON_STYLES,
            title="Custom Selectors Portal",
            desc="Uses custom input parameters to verify selector locking overrides.",
            icon="🛡️",
            post_url="/login-custom",
            csrf_field="sec_token",
            csrf_token=token,
            user_label="Account Code (user_id)",
            user_field="user_id",
            pass_label="Passkey (pass_word)",
            pass_field="pass_word",
        )

    # POST validation
    STATS["total_attempts"] += 1

    # CSRF check
    submitted_token = request.form.get("sec_token", "")
    if submitted_token not in CSRF_TOKENS:
        STATS["csrf_blocks"] += 1
        return render_template_string(CSRF_FAIL_PAGE, common_styles=_COMMON_STYLES), 403
    CSRF_TOKENS.discard(submitted_token)

    username = request.form.get("user_id", "")
    password = request.form.get("pass_word", "")

    if _validate_credentials(username, password):
        STATS["successes"] += 1
        return render_template_string(SUCCESS_PAGE, common_styles=_COMMON_STYLES, user=username)

    STATS["failures"] += 1
    return render_template_string(
        FAIL_PAGE,
        common_styles=_COMMON_STYLES,
        return_url="/login-custom",
    ), 401


# ─── 4. REST JSON API Endpoint ─────────────────────────────────────
@app.route("/login-json", methods=["GET", "POST"])
def login_json():
    """Standard HTML landing page for JSON endpoints."""
    if request.method == "GET":
        return render_template_string(
            LOGIN_PAGE,
            common_styles=_COMMON_STYLES,
            title="JSON Portal",
            desc="Handles JSON credentials payload and returns serialized status data.",
            icon="🖥️",
            post_url="/api/login",
            csrf_field="",
            user_label="API Username",
            user_field="username",
            pass_label="API Password",
            pass_field="password",
        )


@app.route("/api/login", methods=["POST"])
def api_login():
    """Universal programmatic JSON API endpoint."""
    with _demo_lock:
        STATS["total_attempts"] += 1
    client_ip = request.remote_addr

    # Support JSON requests as well as standard forms
    if request.is_json:
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "error": "invalid_payload",
                "message": "JSON body must be an object.",
            }), 400
        username = data.get("username", "")
        password = data.get("password", "")
    else:
        username = request.form.get("username", "")
        password = request.form.get("password", "")

    # Rate limiting
    if _check_rate_limit(client_ip, MAX_ATTEMPTS, RATE_LIMIT_WINDOW):
        STATS["rate_limits"] += 1
        return jsonify({
            "success": False,
            "error": "too many requests",
            "message": "Rate limit exceeded.",
        }), 429

    if not username or not password:
        STATS["failures"] += 1
        return jsonify({
            "success": False,
            "error": "missing_credentials",
            "message": "Username and password required.",
        }), 400

    if _validate_credentials(username, password):
        STATS["successes"] += 1
        return jsonify({
            "success": True,
            "message": f"Welcome, {username}!",
            "token": str(uuid.uuid4()),
        }), 200

    STATS["failures"] += 1
    return jsonify({
        "success": False,
        "error": "invalid_credentials",
        "message": "Invalid credentials.",
    }), 401


# ─── 5. Aggressive Rate Limiter ────────────────────────────────────
@app.route("/login-rate-limited", methods=["GET", "POST"])
def login_rate_limited():
    """Rate limit target triggerable after just 2 failures in 30s."""
    client_ip = request.remote_addr

    if request.method == "GET":
        return render_template_string(
            LOGIN_PAGE,
            common_styles=_COMMON_STYLES,
            title="Throttled Portal",
            desc="Rate limits clients aggressively after only 2 attempts in 30s.",
            icon="⏳",
            post_url="/login-rate-limited",
            csrf_field="",
            user_label="Username",
            user_field="username",
            pass_label="Password",
            pass_field="password",
        )

    # POST validation
    STATS["total_attempts"] += 1

    # Aggressive throttle checking (2 attempts / 30 seconds)
    if _check_rate_limit(client_ip, 2, 30):
        STATS["rate_limits"] += 1
        return render_template_string(RATE_LIMIT_PAGE, common_styles=_COMMON_STYLES), 429

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if _validate_credentials(username, password):
        STATS["successes"] += 1
        return render_template_string(SUCCESS_PAGE, common_styles=_COMMON_STYLES, user=username)

    STATS["failures"] += 1
    return render_template_string(
        FAIL_PAGE,
        common_styles=_COMMON_STYLES,
        return_url="/login-rate-limited",
    ), 401


# ─── 6. Custom Headers Target ──────────────────────────────────────
@app.route("/login-headers", methods=["GET", "POST"])
def login_headers():
    """Requires specific custom header X-Custom-Audit to be present."""
    if request.method == "GET":
        return render_template_string(
            LOGIN_PAGE,
            common_styles=_COMMON_STYLES,
            title="Header Verification Portal",
            desc="Rejects all attempts unless configured with the custom header 'X-Custom-Audit: BlueCrack'.",
            icon="🛡️",
            post_url="/login-headers",
            csrf_field="",
            user_label="Username",
            user_field="username",
            pass_label="Password",
            pass_field="password",
        )

    # Check for custom header requirement
    header_val = request.headers.get("X-Custom-Audit", "")
    if header_val != "BlueCrack":
        STATS["header_blocks"] += 1
        return render_template_string(
            FAIL_PAGE,
            common_styles=_COMMON_STYLES,
            return_url="/login-headers",
            error="Blocked: Missing required custom header 'X-Custom-Audit: BlueCrack'."
        ), 400

    # POST validation
    STATS["total_attempts"] += 1
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if _validate_credentials(username, password):
        STATS["successes"] += 1
        return render_template_string(SUCCESS_PAGE, common_styles=_COMMON_STYLES, user=username)

    STATS["failures"] += 1
    return render_template_string(
        FAIL_PAGE,
        common_styles=_COMMON_STYLES,
        return_url="/login-headers",
    ), 401


# ═══════════════════════════════════════════════════════════════════
# SERVER RUNNER
# ═══════════════════════════════════════════════════════════════════
def run_demo(port: int = 5001, max_attempts: int = 3, rate_window: int = 10) -> None:
    """Set configurations and launch the Flask app."""
    global MAX_ATTEMPTS, RATE_LIMIT_WINDOW
    MAX_ATTEMPTS = max_attempts
    RATE_LIMIT_WINDOW = rate_window

    print("\n  ========================================")
    print("     BlueCrack Testing Sandbox Server")
    print("  ========================================")
    print(f"  Port:          {port}")
    print(f"  Max attempts:  {MAX_ATTEMPTS}")
    print(f"  Rate window:   {RATE_LIMIT_WINDOW}s")
    print(f"  Accounts:      {', '.join(DEMO_ACCOUNTS.keys())}")
    print(f"  Portal Home:   http://127.0.0.1:{port}/")
    print("  ========================================\n")

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
