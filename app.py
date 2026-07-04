#!/usr/bin/env python3
"""
BlueCrack Web UI — Flask Application
======================================
Serves the BlueCrack web interface with real-time WebSocket updates
via Flask-SocketIO. Bridges the Selenium attack engine with the
browser-based frontend.
"""

import os
import sys
import json
import threading
import time
import subprocess
import socket
import atexit
from typing import Any, Dict, List, Optional

from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit

from engine import (
    AttackEngine,
    generate_cupp_wordlist,
    generate_sequence_wordlist,
    print_banner,
)

# ═══════════════════════════════════════════════════════════════════
# APP INITIALIZATION
# ═══════════════════════════════════════════════════════════════════
app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

# Global engine instance
engine = AttackEngine()

# Store last generated wordlist path
_last_wordlist_path: str = ""
_wordlist_lock = threading.Lock()


# ═══════════════════════════════════════════════════════════════════
# ENGINE CALLBACKS → SOCKETIO EVENTS
# ═══════════════════════════════════════════════════════════════════
def _on_log(msg: str) -> None:
    """Forward engine log messages to all connected clients."""
    socketio.emit("log", {"message": msg})


def _on_progress(current: int, total: int) -> None:
    """Forward progress updates to all connected clients."""
    socketio.emit("progress", {"current": current, "total": total})


def _on_metrics(metrics: Dict[str, Any]) -> None:
    """Forward metrics snapshot to all connected clients."""
    socketio.emit("metrics", metrics)


def _on_finished(found: bool, message: str) -> None:
    """Forward attack completion to all connected clients."""
    socketio.emit("finished", {"found": found, "message": message})


# Wire up engine callbacks
engine.set_callbacks(
    log_cb=_on_log,
    progress_cb=_on_progress,
    metrics_cb=_on_metrics,
    finished_cb=_on_finished,
)


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
@app.route("/api/attack/start", methods=["POST"])
def start_attack():
    """Start a brute-force attack with the given configuration.

    Expects JSON body with attack configuration fields.
    """
    if engine.is_running:
        return jsonify({"status": "error", "message": "Attack already running."}), 409

    data = request.get_json(silent=True) or {}

    # Parse target URL
    target_url = data.get("target_url", "").strip()
    if not target_url:
        return jsonify({"status": "error", "message": "Target URL is required."}), 400
    if not target_url.startswith("http"):
        target_url = "http://" + target_url

    # Parse users
    users: List[str] = []
    user_input = data.get("username", "").strip()
    if user_input:
        if os.path.isfile(user_input):
            with open(user_input, encoding="utf-8", errors="ignore") as f:
                users = [x.strip() for x in f if x.strip()]
        else:
            users = [user_input]

    if not users:
        return jsonify({"status": "error", "message": "Username is required."}), 400

    # Parse passwords
    passwords: List[str] = []
    pass_input = data.get("password", "").strip()
    if pass_input:
        if os.path.isfile(pass_input):
            with open(pass_input, encoding="utf-8", errors="ignore") as f:
                passwords = [x.strip() for x in f if x.strip()]
        else:
            passwords = [pass_input]

    if not passwords:
        return jsonify({"status": "error", "message": "Password is required."}), 400

    # Parse proxies
    proxies: List[str] = []
    proxy_input = data.get("proxy", "").strip()
    if proxy_input:
        if os.path.isfile(proxy_input):
            with open(proxy_input, encoding="utf-8", errors="ignore") as f:
                proxies = [x.strip() for x in f if x.strip()]
        else:
            proxies = [proxy_input]

    # Build context
    ctx: Dict[str, Any] = {
        "target_url": target_url,
        "users": users,
        "passwords": passwords,
        "threads": max(1, min(50, int(data.get("threads", 1)))),
        "delay": float(data.get("delay", 0)),
        "jitter": float(data.get("jitter", 0)),
        "error_msg": data.get("error_msg", "").strip().lower(),
        "success_msg": data.get("success_msg", "").strip(),
        "limit_text": data.get("limit_text", "too many requests").strip().lower(),
        "cooldown": int(data.get("cooldown", 12)),
        "headless": bool(data.get("headless", False)),
        "proxies": proxies,
        "use_tor": bool(data.get("use_tor", False)),
        "tor_port": int(data.get("tor_port", 9051)),
        "tor_shift_every": int(data.get("tor_shift_every", 10)),
        "max_attempts": int(data.get("max_attempts", 0)),
        "continue_after_success": bool(data.get("continue_after_success", False)),
    }

    total = len(users) * len(passwords)
    engine.start(ctx)

    return jsonify({
        "status": "ok",
        "message": f"Attack started: {len(users)} user(s) × {len(passwords)} password(s) = {total} combos",
        "total": total,
    })


@app.route("/api/attack/stop", methods=["POST"])
def stop_attack():
    """Stop the currently running attack."""
    if not engine.is_running:
        return jsonify({"status": "error", "message": "No attack is running."}), 409

    engine.stop()
    return jsonify({"status": "ok", "message": "Stop signal sent."})


@app.route("/api/attack/status", methods=["GET"])
def attack_status():
    """Get the current attack status and metrics."""
    return jsonify({
        "running": engine.is_running,
        "metrics": engine.get_metrics(),
        "found_credentials": [
            {"username": u, "password": p} for u, p in engine.get_found_creds()
        ],
    })


@app.route("/api/cupp/generate", methods=["POST"])
def generate_cupp():
    """Generate a CUPP wordlist from a user profile."""
    global _last_wordlist_path
    data = request.get_json(silent=True) or {}

    profile = {
        "name": data.get("name", "").strip(),
        "surname": data.get("surname", "").strip(),
        "nick": data.get("nick", "").strip(),
        "birthdate": data.get("birthdate", "").strip(),
        "wife": data.get("wife", "").strip(),
        "wifen": data.get("wifen", "").strip(),
        "wifeb": data.get("wifeb", "").strip(),
        "kid": data.get("kid", "").strip(),
        "kidb": data.get("kidb", "").strip(),
        "pet": data.get("pet", "").strip(),
        "company": data.get("company", "").strip(),
        "words": data.get("words", "").strip().split(",") if data.get("words") else [],
        "spechars1": "y" if data.get("special_chars") else "n",
        "randnum": "y" if data.get("random_numbers") else "n",
        "leetmode": "y" if data.get("leet_mode") else "n",
    }

    if not profile["name"]:
        return jsonify({"status": "error", "message": "First name is required."}), 400

    def _run_cupp():
        global _last_wordlist_path
        result = generate_cupp_wordlist(profile, log_callback=_on_log)
        with _wordlist_lock:
            _last_wordlist_path = result
        socketio.emit("cupp_done", {"path": result, "success": bool(result)})

    threading.Thread(target=_run_cupp, daemon=True).start()
    return jsonify({"status": "ok", "message": "CUPP generation started."})


@app.route("/api/sequence/generate", methods=["POST"])
def generate_sequence():
    """Generate a numeric sequence wordlist."""
    global _last_wordlist_path
    data = request.get_json(silent=True) or {}

    start = int(data.get("start", 0))
    end = int(data.get("end", 100))
    prefix = data.get("prefix", "").strip()
    suffix = data.get("suffix", "").strip()
    pad_width = int(data.get("pad_width", 0))

    def _run_seq():
        global _last_wordlist_path
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
        socketio.emit("sequence_done", {"path": result, "success": bool(result)})

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


# ═══════════════════════════════════════════════════════════════════
# SOCKETIO EVENTS
# ═══════════════════════════════════════════════════════════════════
@socketio.on("connect")
def handle_connect():
    """Handle new client connection."""
    emit("log", {"message": "[*] Connected to BlueCrack server."})
    # Send current status
    emit("status", {
        "running": engine.is_running,
        "metrics": engine.get_metrics(),
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
        if demo_process is not None:
            poll = demo_process.poll()
            if poll is None:
                return jsonify({
                    "status": "ok",
                    "message": "Demo server is already running.",
                    "url": f"http://127.0.0.1:{demo_port}/login",
                    "port": demo_port,
                    "default_username": "demo",
                    "default_password_file": os.path.abspath("pass.txt"),
                    "default_error_msg": "Invalid credentials",
                    "default_success_msg": "Successful"
                })
        
        port = find_free_port(5001)
        try:
            demo_process = subprocess.Popen(
                [sys.executable, "demo_server.py", "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
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
                demo_process = None
                return jsonify({
                    "status": "error",
                    "error": "failed_to_bind",
                    "message": f"Demo server failed to start on port {port}."
                }), 500
                
            return jsonify({
                "status": "ok",
                "message": "Demo server launched successfully.",
                "url": f"http://127.0.0.1:{port}/login",
                "port": port,
                "default_username": "demo",
                "default_password_file": os.path.abspath("pass.txt"),
                "default_error_msg": "Invalid credentials",
                "default_success_msg": "Successful"
            })
            
        except Exception as e:
            demo_process = None
            return jsonify({
                "status": "error",
                "error": "exception",
                "message": f"Failed to launch demo server: {str(e)}"
            }), 500


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def run_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False) -> None:
    """Start the Flask-SocketIO server.

    Args:
        host: Bind address (default: 127.0.0.1).
        port: Port number (default: 5000).
        debug: Enable Flask debug mode.
    """
    print_banner()
    print(f"\n\033[36m[*] BlueCrack Web UI starting at http://{host}:{port}\033[0m\n")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BlueCrack Web UI Server")
    parser.add_argument("--host", default="127.0.0.1", help="bind address")
    parser.add_argument("--port", type=int, default=5000, help="port number")
    parser.add_argument("--debug", action="store_true", help="enable debug mode")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port, debug=args.debug)
