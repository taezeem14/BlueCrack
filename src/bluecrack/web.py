"""
BlueCrack Web UI — Flask Application
====================================
Serves the BlueCrack web interface with real-time WebSocket updates
via Flask-SocketIO. Bridges the Selenium attack engine with the
browser-based frontend.
"""

import atexit
import json
import os
import socket
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, Response, jsonify, render_template, request
from flask_socketio import SocketIO, emit

from .doctor import diagnose
from .engine import AttackEngine
from .fingerprint import TechnologyDetector
from .http_engine import HTTPAttackEngine
from .notifier import Notifier
from .reporter import ReportGenerator
from .scheduler import AttackScheduler
from .session import SessionManager
from .target_queue import TargetQueue
from .utils import (
    generate_cupp_wordlist,
    generate_sequence_wordlist,
    get_package_data_path,
    print_banner,
)

# ═══════════════════════════════════════════════════════════════════
# APP INITIALIZATION
# ═══════════════════════════════════════════════════════════════════
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(_PKG_DIR, "templates"),
    static_folder=os.path.join(_PKG_DIR, "static"),
)
app.config["SECRET_KEY"] = os.urandom(24).hex()
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")


@app.after_request
def _set_cache_headers(response: Response) -> Response:
    """Disable aggressive browser caching for development and hot edits."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Global engine instance (switchable between AttackEngine and HTTPAttackEngine)
engine: Any = AttackEngine()

# v4.0 feature instances
session_mgr = SessionManager()
target_queue = TargetQueue()
_queue_stop_event = threading.Event()
notifier = Notifier()
attack_scheduler = AttackScheduler()

# Store last generated wordlist path
_last_wordlist_path: str = ""
_wordlist_lock = threading.Lock()
_CONFIG_FILE = os.path.join(os.getcwd(), ".bluecrack_config.json")
_config_lock = threading.Lock()
_log_history: List[str] = []
_log_history_lock = threading.Lock()
_MAX_LOG_HISTORY = 250


def _sync_notifier_from_config(cfg: Dict[str, Any]) -> None:
    """Sync Discord and Telegram backends dynamically from configuration dict."""
    if not isinstance(cfg, dict):
        return

    discord_url = cfg.get("discord_url") or cfg.get("discordWebhook", "")
    telegram_token = cfg.get("telegram_token") or cfg.get("telegramToken", "")
    telegram_chat_id = cfg.get("telegram_chat_id") or cfg.get("telegramChatId", "")

    if isinstance(discord_url, str) and discord_url.strip():
        notifier.add_discord(discord_url.strip())
    elif "discord_url" in cfg or "discordWebhook" in cfg:
        notifier.remove_discord()

    if (
        isinstance(telegram_token, str)
        and telegram_token.strip()
        and isinstance(telegram_chat_id, str)
        and telegram_chat_id.strip()
    ):
        notifier.add_telegram(telegram_token.strip(), telegram_chat_id.strip())
    elif (
        "telegram_token" in cfg
        or "telegramToken" in cfg
        or "telegram_chat_id" in cfg
        or "telegramChatId" in cfg
    ):
        notifier.remove_telegram()


# Restore saved notifications configuration on server startup
if os.path.isfile(_CONFIG_FILE):
    try:
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            _initial_cfg = json.load(f)
            _sync_notifier_from_config(_initial_cfg)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════
# ENGINE CALLBACKS → SOCKETIO EVENTS
# ═══════════════════════════════════════════════════════════════════
def _on_log(msg: str) -> None:
    """Forward engine log messages to all connected clients and buffer history."""
    with _log_history_lock:
        _log_history.append(msg)
        if len(_log_history) > _MAX_LOG_HISTORY:
            _log_history.pop(0)
    socketio.emit("log", {"message": msg})


def _on_progress(current: int, total: int) -> None:
    """Forward progress updates to all connected clients."""
    percent = round((current / total * 100) if total else 0, 1)
    socketio.emit("progress", {"current": current, "total": total, "percent": percent})


def _on_metrics(metrics: Dict[str, Any]) -> None:
    """Forward metrics snapshot to all connected clients."""
    socketio.emit("metrics", metrics)
    socketio.emit("status", {"metrics": metrics, "running": True})


def _on_found(user: str, pwd: str, target_url: str) -> None:
    """Forward found credentials to socket and send instant notification alert."""
    payload = {"username": user, "password": pwd, "target_url": target_url}
    socketio.emit("credential_found", payload)
    socketio.emit("found", payload)
    if notifier and notifier.has_backends:
        try:
            _on_log(f"[+] 📢 Dispatching alert to notifications (User: '{user}')...")
            notifier.notify("credential_found", payload)
        except Exception as exc:
            _on_log(f"[-] Notification dispatch error: {exc}")


def _on_finished(found: bool, message: str) -> None:
    """Forward attack completion to all connected clients and trigger alert."""
    socketio.emit("finished", {"found": found, "message": message, "running": False})
    socketio.emit("status", {"running": False, "finished": True, "message": message})
    if notifier and notifier.has_backends:
        try:
            m = engine.get_metrics() if engine else {}
            notifier.notify(
                "attack_complete",
                {
                    "successes": m.get("hits", m.get("successes", 0)),
                    "attempted": m.get("attempted", 0),
                    "elapsed": m.get("elapsed", 0),
                },
            )
        except Exception as exc:
            _on_log(f"[-] Notification completion error: {exc}")


def _wire_callbacks(eng: Any) -> None:
    """Wire the SocketIO and notification callbacks onto the given engine instance."""
    eng.set_callbacks(
        log_cb=_on_log,
        progress_cb=_on_progress,
        metrics_cb=_on_metrics,
        finished_cb=_on_finished,
        found_cb=_on_found,
    )


# Wire up engine callbacks
_wire_callbacks(engine)


# ═══════════════════════════════════════════════════════════════════
# PAGE ROUTES
# ═══════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    """Serve the main BlueCrack web UI."""
    return render_template("index.html")


# ═══════════════════════════════════════════════════════════════════
# API ROUTES
# ═══════════════════════════════════════════════════════════════════
def _prepare_and_start_attack(data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """Parse configuration data and launch the attack engine.

    Returns:
        (success: bool, message: str, details: dict)
    """
    global engine

    _sync_notifier_from_config(data)

    # Parse attack mode
    attack_mode = str(data.get("mode", "browser")).strip().lower()
    if attack_mode not in ("browser", "http"):
        attack_mode = "browser"

    # Parse target URL
    target_url = str(data.get("target_url", "")).strip()
    if not target_url:
        return False, "Target URL is required.", {}
    if not target_url.startswith("http"):
        target_url = "http://" + target_url

    # Parse users
    users: List[str] = []
    user_input = str(data.get("username", "")).strip()
    if user_input:
        if os.path.isfile(user_input):
            with open(user_input, encoding="utf-8", errors="ignore") as f:
                users = [x.strip() for x in f if x.strip()]
        else:
            users = [user_input]

    if not users:
        return False, "Username is required.", {}

    # Parse passwords
    passwords: List[str] = []
    pass_input = str(data.get("password", "")).strip()
    if pass_input:
        if os.path.isfile(pass_input):
            with open(pass_input, encoding="utf-8", errors="ignore") as f:
                passwords = [x.strip() for x in f if x.strip()]
        else:
            passwords = [pass_input]

    if not passwords:
        return False, "Password is required.", {}

    # Parse proxies
    proxies: List[str] = []
    proxy_input = str(data.get("proxy", "")).strip()
    if proxy_input:
        if os.path.isfile(proxy_input):
            with open(proxy_input, encoding="utf-8", errors="ignore") as f:
                proxies = [x.strip() for x in f if x.strip()]
        else:
            proxies = [proxy_input]

    # Switch engine based on mode
    if attack_mode == "http":
        engine = HTTPAttackEngine()
    else:
        engine = AttackEngine()
    _wire_callbacks(engine)

    # Build context safely
    try:
        threads = max(1, min(50, int(data.get("threads", 1) or 1)))
        delay = float(data.get("delay", 0) or 0)
        jitter = float(data.get("jitter", 0) or 0)
        cooldown = int(data.get("cooldown", 12) or 12)
        tor_port = int(data.get("tor_port", 9051) or 9051)
        tor_shift_every = int(data.get("tor_shift_every", 10) or 10)
        max_attempts = int(data.get("max_attempts", 0) or 0)
    except (ValueError, TypeError) as e:
        return False, f"Invalid configuration parameter: {e}", {}

    ctx: Dict[str, Any] = {
        "target_url": target_url,
        "users": users,
        "passwords": passwords,
        "threads": threads,
        "delay": delay,
        "jitter": jitter,
        "error_msg": str(data.get("error_msg", "")).strip().lower(),
        "success_msg": str(data.get("success_msg", "")).strip(),
        "limit_text": str(data.get("limit_text", "too many requests")).strip().lower(),
        "cooldown": cooldown,
        "headless": bool(data.get("headless", False)),
        "proxies": proxies,
        "use_tor": bool(data.get("use_tor", False)),
        "tor_port": tor_port,
        "tor_shift_every": tor_shift_every,
        "max_attempts": max_attempts,
        "continue_after_success": bool(data.get("continue_after_success", False)),
        "spray_mode": bool(data.get("spray_mode", False)),
    }

    # Add HTTP-mode-specific fields
    if attack_mode == "http":
        ctx["form_action"] = str(data.get("form_action", "")).strip()
        ctx["username_field"] = str(data.get("username_field", "")).strip()
        ctx["password_field"] = str(data.get("password_field", "")).strip()
        ctx["csrf_field"] = str(data.get("csrf_field", "")).strip()
        ctx["follow_redirects"] = bool(data.get("follow_redirects", False))
        ctx["json_mode"] = bool(data.get("json_mode", False))

        # Custom headers
        headers_raw = data.get("custom_headers", "")
        custom_headers: Dict[str, str] = {}
        if isinstance(headers_raw, dict):
            custom_headers = headers_raw
        elif isinstance(headers_raw, str) and headers_raw.strip():
            for line in headers_raw.strip().splitlines():
                if ":" in line:
                    hk, hv = line.split(":", 1)
                    custom_headers[hk.strip()] = hv.strip()
        ctx["custom_headers"] = custom_headers

        # Custom cookies
        cookies_raw = data.get("cookies", "")
        custom_cookies: Dict[str, str] = {}
        if isinstance(cookies_raw, dict):
            custom_cookies = cookies_raw
        elif isinstance(cookies_raw, str) and cookies_raw.strip():
            for pair in cookies_raw.strip().split(";"):
                if "=" in pair:
                    ck, cv = pair.split("=", 1)
                    custom_cookies[ck.strip()] = cv.strip()
        ctx["cookies"] = custom_cookies

        # Status codes
        success_codes_raw = data.get("success_status_codes", "")
        if isinstance(success_codes_raw, str) and success_codes_raw.strip():
            ctx["success_status_codes"] = [
                int(c.strip()) for c in success_codes_raw.split(",") if c.strip().isdigit()
            ]
        elif isinstance(success_codes_raw, list):
            ctx["success_status_codes"] = [int(c) for c in success_codes_raw if str(c).isdigit()]

        # Parse extra_fields from comma-separated key=value pairs
        extra_raw = str(data.get("extra_fields", "")).strip()
        extra_fields: Dict[str, str] = {}
        if extra_raw:
            for pair in extra_raw.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    extra_fields[k.strip()] = v.strip()
        ctx["extra_fields"] = extra_fields

    total = len(users) * len(passwords)
    mode_label = "⚡ HTTP (JSON)" if (attack_mode == "http" and ctx.get("json_mode")) else ("⚡ HTTP" if attack_mode == "http" else "🌐 Browser")
    engine.start(ctx)

    return True, f"{mode_label} attack started: {len(users)} user(s) × {len(passwords)} password(s) = {total} combos", {
        "total": total,
        "mode": attack_mode,
        "users_count": len(users),
        "passwords_count": len(passwords),
        "target_url": target_url,
    }


@app.route("/api/attack/start", methods=["POST"])
def start_attack():
    """Start a brute-force attack with the given configuration."""
    global engine

    if engine.is_running:
        return jsonify({"status": "error", "message": "Attack already running."}), 409

    data = request.get_json(silent=True) or {}
    ok, msg, details = _prepare_and_start_attack(data)
    if not ok:
        return jsonify({"status": "error", "message": msg}), 400

    return jsonify({
        "status": "ok",
        "message": msg,
        **details,
    })


@app.route("/api/attack/stop", methods=["POST"])
def stop_attack():
    """Stop the currently running attack."""
    _queue_stop_event.set()
    if not engine.is_running:
        return jsonify({"status": "error", "message": "No attack is running."}), 409

    engine.stop()
    return jsonify({"status": "ok", "message": "Stop signal sent."})


@app.route("/api/attack/status", methods=["GET"])
def attack_status():
    """Get the current attack status, metrics, and recent logs."""
    with _log_history_lock:
        recent_logs = list(_log_history)
    return jsonify({
        "status": "ok",
        "running": engine.is_running,
        "metrics": engine.get_metrics(),
        "found_credentials": [
            {"username": u, "password": p} for u, p in engine.get_found_creds()
        ],
        "recent_logs": recent_logs,
    })


@app.route("/api/logs", methods=["GET"])
def get_recent_logs():
    """Get recent log lines."""
    with _log_history_lock:
        return jsonify({"status": "ok", "logs": list(_log_history)})


@app.route("/api/logs/clear", methods=["POST"])
def clear_recent_logs():
    """Clear server-side log buffer."""
    with _log_history_lock:
        _log_history.clear()
    return jsonify({"status": "ok", "message": "Logs cleared."})


@app.route("/api/cupp/generate", methods=["POST"])
def generate_cupp():
    """Generate a CUPP wordlist from a user profile."""
    global _last_wordlist_path
    data = request.get_json(silent=True) or {}

    first_name = (data.get("first_name") or data.get("name") or "").strip()
    if not first_name:
        return jsonify({"status": "error", "message": "First name is required."}), 400

    profile = {
        "name": first_name,
        "surname": (data.get("last_name") or data.get("surname") or "").strip(),
        "nick": (data.get("nickname") or data.get("nick") or "").strip(),
        "birthdate": (data.get("birthdate") or "").strip(),
        "wife": (data.get("partner_name") or data.get("wife") or "").strip(),
        "wifen": (data.get("partner_nickname") or data.get("wifen") or "").strip(),
        "wifeb": (data.get("partner_birthdate") or data.get("wifeb") or "").strip(),
        "kid": (data.get("child_name") or data.get("kid") or "").strip(),
        "kidb": (data.get("child_birthdate") or data.get("kidb") or "").strip(),
        "pet": (data.get("pet_name") or data.get("pet") or "").strip(),
        "company": (data.get("company") or "").strip(),
        "words": (
            data.get("words", "").strip().split(",")
            if data.get("words")
            else (data.get("keywords", "").strip().split(",") if data.get("keywords") else [])
        ),
        "spechars1": "y" if (data.get("special_chars") or data.get("spechars1")) else "n",
        "randnum": "y" if (data.get("random_numbers") or data.get("randnum")) else "n",
        "leetmode": "y" if (data.get("leet") or data.get("leet_mode") or data.get("leetmode")) else "n",
    }

    def _run_cupp():
        global _last_wordlist_path
        try:
            result = generate_cupp_wordlist(profile, log_callback=_on_log)
            with _wordlist_lock:
                _last_wordlist_path = result
            cnt = 0
            if result and os.path.exists(result):
                with open(result, encoding="utf-8", errors="ignore") as f:
                    cnt = sum(1 for _ in f)
            socketio.emit("cupp_done", {"path": result, "count": cnt, "success": bool(result)})
        except Exception as e:
            _on_log(f"[-] CUPP generation error: {e}")
            socketio.emit("cupp_done", {"path": None, "count": 0, "success": False, "error": str(e)})

    threading.Thread(target=_run_cupp, daemon=True).start()
    return jsonify({"status": "ok", "message": "CUPP generation started."})


@app.route("/api/sequence/generate", methods=["POST"])
def generate_sequence():
    """Generate a numeric sequence wordlist."""
    global _last_wordlist_path
    data = request.get_json(silent=True) or {}

    try:
        start = int(data.get("start", 0))
        end = int(data.get("end", 100))
        prefix = str(data.get("prefix", "")).strip()
        suffix = str(data.get("suffix", "")).strip()
        pad_width = int(data.get("pad_width", 0))
    except (ValueError, TypeError) as e:
        return jsonify({"status": "error", "message": f"Invalid sequence parameters: {e}"}), 400

    def _run_seq():
        global _last_wordlist_path
        try:
            result = generate_sequence_wordlist(
                start=start,
                end=end,
                prefix=prefix,
                suffix=suffix,
                pad_width=pad_width,
                log_callback=_on_log,
            )
            with _wordlist_lock:
                _last_wordlist_path = result
            cnt = end - start + 1 if (result and os.path.exists(result)) else 0
            socketio.emit("sequence_done", {"path": result, "count": cnt, "success": bool(result)})
        except Exception as e:
            _on_log(f"[-] Sequence generation error: {e}")
            socketio.emit("sequence_done", {"path": None, "count": 0, "success": False, "error": str(e)})

    threading.Thread(target=_run_seq, daemon=True).start()
    return jsonify({"status": "ok", "message": "Sequence generation started."})


@app.route("/api/wordlist/last", methods=["GET"])
def get_last_wordlist():
    """Get the path to the last generated wordlist."""
    with _wordlist_lock:
        return jsonify({"path": _last_wordlist_path})


@app.route("/api/logs/export", methods=["GET"])
def export_logs():
    """Export attack logs as a downloadable text file."""
    logs = engine.get_logs()
    content = "\n".join(logs) if logs else "No logs available."
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=bluecrack_logs.txt"},
    )


@app.route("/api/session/status", methods=["GET"])
def session_status():
    return jsonify({
        "has_session": session_mgr.has_session(),
        "state": session_mgr.load_state() if session_mgr.has_session() else None
    })


@app.route("/api/attack/resume", methods=["POST"])
def resume_attack():
    global engine
    if engine.is_running:
        return jsonify({"status": "error", "message": "Attack already running."}), 409
    state = session_mgr.load_state()
    if not state:
        return jsonify({"status": "error", "message": "No saved session found."}), 404
    ctx = state["ctx"]
    combos = state.get("remaining_combos", [])
    ctx["combos"] = combos
    ctx["users"] = list(dict.fromkeys(c[0] for c in combos)) if combos else ctx.get("users", [])
    ctx["passwords"] = list(dict.fromkeys(c[1] for c in combos)) if combos else ctx.get("passwords", [])
    from .engine import AttackEngine
    from .http_engine import HTTPAttackEngine
    attack_mode = ctx.pop("attack_mode", "browser")
    if attack_mode == "http":
        engine = HTTPAttackEngine()
    else:
        engine = AttackEngine()
    _wire_callbacks(engine)
    engine.start(ctx)
    session_mgr.clear_session()
    return jsonify({"status": "ok", "message": "Attack resumed from saved session."})


@app.route("/api/targets", methods=["GET"])
@app.route("/api/targets/list", methods=["GET"])
def list_targets():
    return jsonify({
        "status": "ok",
        "targets": target_queue.get_targets(),
        "progress": target_queue.get_progress(),
    })


@app.route("/api/targets/add", methods=["POST"])
def add_target():
    data = request.get_json(silent=True) or {}
    index = target_queue.add_target(data)
    return jsonify({"status": "ok", "index": index})


@app.route("/api/targets/remove", methods=["POST"])
def remove_target():
    data = request.get_json(silent=True) or {}
    raw_index = data.get("index", -1)
    try:
        index = int(raw_index)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid target index."}), 400
    ok = target_queue.remove_target(index)
    return jsonify({"status": "ok" if ok else "error"})


@app.route("/api/targets/clear", methods=["POST"])
def clear_targets():
    """Clear all queued targets."""
    target_queue.reset()
    return jsonify({"status": "ok", "message": "Target queue cleared."})


@app.route("/api/targets/start", methods=["POST"])
@app.route("/api/targets/start_all", methods=["POST"])
def start_all_targets():
    """Execute all queued pending targets in sequential succession."""
    global engine
    if engine.is_running:
        return jsonify({"status": "error", "message": "An attack is already running."}), 409

    targets = target_queue.get_targets()
    pending = [t for t in targets if t.get("status") == "pending"]
    if not pending:
        return jsonify({"status": "error", "message": "No pending targets in the queue."}), 400

    def _run_queue_worker():
        _queue_stop_event.clear()
        while not _queue_stop_event.is_set():
            t = target_queue.next_target()
            if not t:
                _on_log("[+] 🎉 Multi-Target Queue: All targets completed!")
                socketio.emit("targets_queue_finished", {"message": "All targets processed."})
                break
            target_idx = t.get("index", 0)
            cfg = dict(t)
            target_name = cfg.get("target_url", "Target")
            _on_log(f"[*] 🎯 Target Queue: Launching next attack on: {target_name}...")
            ok, msg, _ = _prepare_and_start_attack(cfg)
            if not ok:
                _on_log(f"[-] Target Queue: Skipping {target_name} ({msg})")
                target_queue.set_result(target_idx, {"attempted": 0, "hits": 0, "errors": 1}, [])
                continue
            while engine.is_running and not _queue_stop_event.is_set():
                time.sleep(0.5)
            metrics = getattr(engine, "metrics", {"attempted": 0, "hits": 0, "errors": 0})
            creds = getattr(engine, "found_creds", [])
            target_queue.set_result(target_idx, dict(metrics), list(creds))

    threading.Thread(target=_run_queue_worker, daemon=True).start()
    return jsonify({"status": "ok", "message": f"Starting sequential attack for {len(pending)} queued target(s)."})


@app.route("/api/config/load", methods=["GET"])
def load_saved_config():
    """Load persistent UI configuration from disk."""
    with _config_lock:
        if os.path.isfile(_CONFIG_FILE):
            try:
                with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return jsonify({"status": "ok", "config": data})
            except Exception as exc:
                return jsonify({"status": "error", "message": str(exc)}), 500
    return jsonify({"status": "ok", "config": {}})


@app.route("/api/config/save", methods=["POST"])
def save_config_to_disk():
    """Save persistent UI configuration to disk."""
    data = request.get_json(silent=True) or {}
    _sync_notifier_from_config(data)
    with _config_lock:
        try:
            with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return jsonify({"status": "ok", "message": "Configuration saved to disk."})
        except Exception as exc:
            return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/attack/reset", methods=["POST"])
def reset_attack_metrics():
    """Reset attack engine metrics and logs when idle."""
    if engine.is_running:
        return jsonify({"status": "error", "message": "Cannot reset while attack is running."}), 409
    if hasattr(engine, "reset"):
        engine.reset()
    with _log_history_lock:
        _log_history.clear()
    return jsonify({"status": "ok", "message": "Metrics and logs reset."})


@app.route("/api/config/reset", methods=["POST"])
def reset_saved_config():
    """Reset saved configuration on disk and engine state."""
    notifier.clear()
    if hasattr(engine, "reset") and not engine.is_running:
        engine.reset()
    with _log_history_lock:
        _log_history.clear()
    with _config_lock:
        try:
            if os.path.isfile(_CONFIG_FILE):
                os.remove(_CONFIG_FILE)
            return jsonify({"status": "ok", "message": "Saved configuration cleared."})
        except Exception as exc:
            return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/notifications/config", methods=["GET"])
def get_notification_config():
    """Get current notification configuration."""
    return jsonify({"status": "ok", "config": notifier.get_config()})


@app.route("/api/notifications/configure", methods=["POST"])
def configure_notifications():
    data = request.get_json(silent=True) or {}
    _sync_notifier_from_config(data)
    return jsonify({"status": "ok", "config": notifier.get_config()})


@app.route("/api/notifications/test", methods=["POST"])
def test_notifications():
    results = notifier.test()
    return jsonify({"status": "ok", "results": results})


def _on_schedule_fire(config: Dict[str, Any]) -> None:
    """Callback triggered when a scheduled attack timer fires."""
    global engine
    target = config.get("target_url", "Target")
    _on_log(f"[*] ⏰ Scheduled attack timer triggered for: {target}")
    if engine.is_running:
        _on_log(f"[-] ⏰ Skipping scheduled attack for {target}: another attack is currently active.")
        return
    ok, msg, _ = _prepare_and_start_attack(config)
    if not ok:
        _on_log(f"[-] ⏰ Failed to start scheduled attack: {msg}")


attack_scheduler.set_fire_callback(_on_schedule_fire)


@app.route("/api/schedule", methods=["GET"])
@app.route("/api/schedule/list", methods=["GET"])
def list_scheduled():
    tasks = attack_scheduler.list_scheduled()
    return jsonify({"status": "ok", "tasks": tasks, "scheduled": tasks})


@app.route("/api/schedule/create", methods=["POST"])
@app.route("/api/schedule/add", methods=["POST"])
def add_scheduled():
    data = request.get_json(silent=True) or {}
    target_url = str(data.get("target_url", "") or data.get("config", {}).get("target_url", "")).strip()
    run_at_iso = str(data.get("run_at", "")).strip()
    if not target_url or not run_at_iso:
        return jsonify({"status": "error", "message": "target_url and run_at are required."}), 400
    config = dict(data.get("config", data))
    if not config.get("target_url"):
        config["target_url"] = target_url
    try:
        task_id = attack_scheduler.schedule(config, run_at_iso)
        if task_id:
            return jsonify({"status": "ok", "id": task_id, "task_id": task_id})
    except Exception as exc:
        return jsonify({"status": "error", "message": f"Failed to schedule: {exc}"}), 400
    return jsonify({"status": "error", "message": "Failed to schedule attack (invalid time or format)."}), 400


@app.route("/api/schedule/cancel", methods=["POST"])
def cancel_scheduled():
    data = request.get_json(silent=True) or {}
    schedule_id = str(data.get("task_id", "") or data.get("id", "")).strip()
    ok = attack_scheduler.cancel(schedule_id)
    return jsonify({"status": "ok" if ok else "error"})


@app.route("/api/proxies/health", methods=["GET"])
def proxy_health():
    return jsonify({"status": "ok", "message": "No proxies configured for health check."})


# ═══════════════════════════════════════════════════════════════════
# SOCKETIO EVENTS
# ═══════════════════════════════════════════════════════════════════
@socketio.on("connect")
def handle_connect():
    """Handle new client connection with full dynamic state replay."""
    with _log_history_lock:
        recent_logs = list(_log_history)
    emit("status", {
        "running": engine.is_running,
        "metrics": engine.get_metrics(),
        "recent_logs": recent_logs,
    })


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection."""
    pass


# Global tracking of the demo server process
demo_process: Optional[subprocess.Popen] = None
demo_port: Optional[int] = None
demo_lock = threading.Lock()


def _cleanup_demo_server() -> None:
    """Terminate the demo server process on exit."""
    global demo_process
    with demo_lock:
        if demo_process is not None:
            try:
                demo_process.terminate()
                demo_process.wait(timeout=2)
            except Exception:
                try:
                    demo_process.kill()
                except Exception:
                    pass
            demo_process = None


atexit.register(_cleanup_demo_server)


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def find_free_port(start_port: int = 5001) -> int:
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except socket.error:
                port += 1
    return start_port


@app.route("/api/demo/start", methods=["POST"])
def start_demo_server():
    """Start the local demo login server in a background process if not already running."""
    global demo_process, demo_port

    with demo_lock:
        pass_file_path = get_package_data_path("pass.txt")
        if demo_process is not None:
            poll = demo_process.poll()
            if poll is None:
                return jsonify({
                    "status": "ok",
                    "message": "Demo server is already running.",
                    "url": f"http://127.0.0.1:{demo_port}/login",
                    "port": demo_port,
                    "default_username": "demo",
                    "default_password_file": pass_file_path,
                    "default_error_msg": "Invalid credentials",
                    "default_success_msg": "Successful",
                })

        port = find_free_port(5001)
        try:
            demo_process = subprocess.Popen(
                [sys.executable, "-m", "bluecrack.demo", "--port", str(port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            demo_port = port

            started = False
            for _ in range(20):
                time.sleep(0.1)
                if is_port_in_use(port):
                    started = True
                    break
                if demo_process.poll() is not None:
                    break

            if not started:
                try:
                    demo_process.terminate()
                except Exception:
                    pass
                demo_process = None
                return jsonify({
                    "status": "error",
                    "error": "failed_to_bind",
                    "message": f"Demo server failed to start on port {port}.",
                }), 500

            return jsonify({
                "status": "ok",
                "message": "Demo server launched successfully.",
                "url": f"http://127.0.0.1:{port}/login",
                "port": port,
                "default_username": "demo",
                "default_password_file": pass_file_path,
                "default_error_msg": "Invalid credentials",
                "default_success_msg": "Successful",
            })

        except Exception as e:
            demo_process = None
            return jsonify({
                "status": "error",
                "error": "exception",
                "message": f"Failed to launch demo server: {str(e)}",
            }), 500


@app.route("/api/demo/stop", methods=["POST"])
def stop_demo_server():
    """Stop the background demo server if running."""
    global demo_process, demo_port
    with demo_lock:
        if demo_process is not None:
            try:
                demo_process.terminate()
                demo_process.wait(timeout=2)
            except Exception:
                try:
                    demo_process.kill()
                except Exception:
                    pass
            demo_process = None
            demo_port = None
            return jsonify({"status": "ok", "message": "Demo server stopped."})
        return jsonify({"status": "ok", "message": "Demo server was not running."})


@app.route("/api/demo/status", methods=["GET"])
def get_demo_status():
    """Check if demo server is currently active."""
    global demo_process, demo_port
    with demo_lock:
        is_running = demo_process is not None and demo_process.poll() is None
        return jsonify({
            "status": "ok",
            "running": is_running,
            "port": demo_port if is_running else None,
            "url": f"http://127.0.0.1:{demo_port}/login" if is_running else None,
        })


# ═══════════════════════════════════════════════════════════════════
# DIAGNOSTICS & SYSTEM DOCTOR
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/doctor", methods=["GET"])
def api_doctor():
    """Run environment checkup and return structured diagnostics."""
    try:
        report = diagnose()
        return jsonify({"status": "ok", "report": report})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════
# TARGET FINGERPRINTING & CSRF DISCOVERY
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/target/fingerprint", methods=["POST"])
def api_target_fingerprint():
    """Analyze target URL to fingerprint technologies and extract form & CSRF details."""
    data = request.get_json(force=True, silent=True) or {}
    target_url = data.get("target_url", "").strip()
    if not target_url:
        return jsonify({"status": "error", "message": "target_url is required."}), 400

    try:
        import requests
        resp = requests.get(target_url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        analysis = TechnologyDetector.analyze(
            url=target_url,
            body=resp.text,
            headers=dict(resp.headers),
        )
        return jsonify({"status": "ok", "fingerprint": analysis})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fingerprint probe failed: {e}"}), 500


# ═══════════════════════════════════════════════════════════════════
# REPORT DOWNLOAD ENDPOINTS
# ═══════════════════════════════════════════════════════════════════
@app.route("/api/report/html", methods=["GET"])
def api_report_html():
    """Generate and return standalone HTML report."""
    metrics = engine.get_metrics()
    found = engine.get_found_creds()
    logs = engine.get_logs()
    start_time = getattr(engine, "_start_time", 0.0) or (time.time() - 60)
    end_time = time.time()
    target_url = getattr(engine, "_target_url", "") or getattr(engine, "_ctx", {}).get("target_url", "Target")

    html_content = ReportGenerator.generate_html(
        metrics=metrics,
        found_creds=found,
        logs=logs,
        config={"target_url": target_url},
        start_time=start_time,
        end_time=end_time,
    )
    return Response(
        html_content,
        mimetype="text/html",
        headers={"Content-Disposition": "attachment; filename=bluecrack_report.html"},
    )


@app.route("/api/report/json", methods=["GET"])
def api_report_json():
    """Generate and return standalone JSON report."""
    metrics = engine.get_metrics()
    found = engine.get_found_creds()
    start_time = getattr(engine, "_start_time", 0.0) or (time.time() - 60)
    end_time = time.time()
    target_url = getattr(engine, "_target_url", "") or getattr(engine, "_ctx", {}).get("target_url", "Target")

    json_content = ReportGenerator.generate_json(
        metrics=metrics,
        found_creds=found,
        config={"target_url": target_url},
        start_time=start_time,
        end_time=end_time,
    )
    return Response(
        json_content,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=bluecrack_report.json"},
    )


def run_server(
    host: str = "127.0.0.1",
    port: int = 5000,
    debug: bool = False,
    use_reloader: Optional[bool] = None,
) -> None:
    """Start the Flask-SocketIO server with optional auto-reloader for dynamic code updates."""
    print_banner()
    print(f"\n\033[36m[*] BlueCrack Web UI starting at http://{host}:{port}\033[0m\n")

    if use_reloader is None:
        use_reloader = debug or bool(os.getenv("BLUECRACK_RELOAD"))

    extra_files: List[str] = []
    if use_reloader:
        for root, _, files in os.walk(_PKG_DIR):
            for f in files:
                if f.endswith((".py", ".html", ".js", ".css", ".json", ".txt")):
                    extra_files.append(os.path.join(root, f))
        print(f"\033[33m[*] Auto-reloader active (watching {len(extra_files)} source & asset files)\033[0m\n")

    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        use_reloader=use_reloader,
        extra_files=extra_files if extra_files else None,
        allow_unsafe_werkzeug=True,
    )
