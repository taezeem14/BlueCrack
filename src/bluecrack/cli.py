#!/usr/bin/env python3
"""
BlueCrack CLI — Command-Line Interface Dispatcher
====================================================
Routes subcommands to the appropriate module.

Usage::

    bluecrack              # Launch Web UI (default)
    bluecrack web          # Launch Web UI explicitly
    bluecrack attack ...   # CLI brute-force mode
    bluecrack demo         # Launch demo login server
    bluecrack doctor       # Environment diagnostics
    bluecrack plugin       # CUPP / wordlist utilities
"""

import argparse
import sys

from bluecrack._version import __version__


def _configure_encoding() -> None:
    """Reconfigure stdout/stderr to UTF-8 on Windows to prevent encoding crashes."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════
# SUBCOMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════

def _cmd_web(args: argparse.Namespace) -> None:
    """Launch the Flask Web UI."""
    from bluecrack.web import run_server
    run_server(host=args.host, port=args.port, debug=args.debug)


def _cmd_attack(args: argparse.Namespace) -> None:
    """Run CLI brute-force attack."""
    from bluecrack.attack import run_attack_cli
    run_attack_cli(args)


def _cmd_demo(args: argparse.Namespace) -> None:
    """Launch the demo login server."""
    from bluecrack.demo import run_demo
    run_demo(port=args.port, max_attempts=args.max_attempts, rate_window=args.rate_window)


def _cmd_doctor(args: argparse.Namespace) -> None:
    """Run environment diagnostics."""
    from bluecrack.doctor import run_doctor
    run_doctor()


def _cmd_plugin(args: argparse.Namespace) -> None:
    """Run CUPP or wordlist plugin utilities."""
    import os
    if args.plugin_action == "cupp":
        os.system(f"{sys.executable} -m bluecrack.vendor.cupp -i")
    elif args.plugin_action == "sequence":
        from bluecrack.utils import generate_sequence_wordlist
        path = generate_sequence_wordlist(
            start=args.start,
            end=args.end,
            prefix=args.prefix,
            suffix=args.suffix,
            pad_width=args.pad_width,
            output_path=args.output,
            log_callback=lambda msg: print(msg),
        )
        if path:
            print(f"Wordlist saved to: {path}")
    elif args.plugin_action == "list":
        print("Available plugins:")
        print("  cupp       — CUPP interactive password profiler")
        print("  sequence   — Numeric sequence wordlist generator")
    else:
        print("Use: bluecrack plugin cupp | sequence | list")
        print("Run 'bluecrack plugin --help' for details.")


# ═══════════════════════════════════════════════════════════════════
# PARSER CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════

def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with subcommands."""

    parser = argparse.ArgumentParser(
        prog="bluecrack",
        description="BlueCrack — Advanced Browser Penetration Framework",
        epilog="Run 'bluecrack <command> --help' for subcommand details.",
    )
    parser.add_argument(
        "-V", "--version", action="version",
        version=f"BlueCrack {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── bluecrack web ──────────────────────────────────────────────
    web_parser = subparsers.add_parser(
        "web", help="Launch the Flask Web UI (default if no command given)",
    )
    web_parser.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    web_parser.add_argument("--port", type=int, default=5000, help="port number (default: 5000)")
    web_parser.add_argument("--debug", action="store_true", help="enable Flask debug mode")
    web_parser.set_defaults(func=_cmd_web)

    # ── bluecrack attack ───────────────────────────────────────────
    atk = subparsers.add_parser(
        "attack", help="Run CLI brute-force attack",
    )

    # Attack mode
    atk.add_argument(
        "--mode", choices=["browser", "http"], default="browser",
        help="attack mode: 'browser' (Selenium, default) or 'http' (raw HTTP, Hydra-style — much faster)",
    )

    # Username input
    atk.add_argument("-u", "--user", dest="username", help="single username to test")
    atk.add_argument("-U", "--userfile", dest="userfile", help="file containing list of usernames")

    # Password input
    atk.add_argument("-p", "--passw", dest="password", help="single password to test")
    atk.add_argument("-P", "--passlist", dest="passfile", help="file containing list of passwords")

    # Engine settings
    atk.add_argument("--threads", type=int, default=1, help="number of threads")
    atk.add_argument("--url", help="login page URL", required=False)
    atk.add_argument("--error", default="", help="error message string for failed login detection")
    atk.add_argument("--success", default="", help="success message string for login verification")
    atk.add_argument("--headless", action="store_true", help="run browsers in headless mode (browser mode only)")
    atk.add_argument("--delay", type=float, default=0.0, help="delay between attempts (seconds)")
    atk.add_argument("--limit-text", default="too many requests", help="text indicating rate limit")
    atk.add_argument("--cooldown", type=int, default=12, help="cooldown timer for rate-limit bypass")
    atk.add_argument("--jitter", type=float, default=0.0, help="random jitter up to X seconds")

    # Proxy settings
    atk.add_argument("--proxy", help="single proxy (e.g., http://12.34.56.78:8080)")
    atk.add_argument("--proxy-list", dest="proxyfile", help="file containing list of proxies")

    # Mode settings
    atk.add_argument("-i", "--interactive", action="store_true", help="interactive setup wizard")

    # Additional CLI settings
    atk.add_argument("--max-attempts", type=int, default=0, help="max total attempts (0 = unlimited)")
    atk.add_argument("--continue-after-success", action="store_true", help="continue testing after finding credentials")
    atk.add_argument("--output", type=str, default="credentials.txt", help="output file for found credentials")
    atk.add_argument("--json-report", action="store_true", help="save a JSON report when finished")

    # HTTP-mode-specific options
    atk.add_argument("--form-action", default="", help="POST endpoint URL (HTTP mode; auto-detected if omitted)")
    atk.add_argument("--username-field", default="", help="form field name for username (HTTP mode; auto-detected)")
    atk.add_argument("--password-field", default="", help="form field name for password (HTTP mode; auto-detected)")
    atk.add_argument("--csrf-field", default="", help="CSRF token field name for auto-extraction (HTTP mode)")
    atk.add_argument(
        "--extra-fields", default="",
        help="additional POST fields as key=value,key2=value2 (HTTP mode)",
    )
    atk.add_argument(
        "--follow-redirects", action="store_true",
        help="follow HTTP redirects (HTTP mode; default: don't follow)",
    )
    atk.set_defaults(func=_cmd_attack)

    # ── bluecrack demo ─────────────────────────────────────────────
    demo_parser = subparsers.add_parser(
        "demo", help="Launch the demo login server for testing",
    )
    demo_parser.add_argument("--port", type=int, default=5001, help="port (default: 5001)")
    demo_parser.add_argument("--max-attempts", type=int, default=3, help="max login attempts before rate-limit")
    demo_parser.add_argument("--rate-window", type=int, default=10, help="rate-limit window in seconds")
    demo_parser.set_defaults(func=_cmd_demo)

    # ── bluecrack doctor ───────────────────────────────────────────
    doctor_parser = subparsers.add_parser(
        "doctor", help="Check environment and dependencies",
    )
    doctor_parser.set_defaults(func=_cmd_doctor)

    # ── bluecrack plugin ───────────────────────────────────────────
    plugin_parser = subparsers.add_parser(
        "plugin", help="Wordlist generation plugins (CUPP, sequence)",
    )
    plugin_sub = plugin_parser.add_subparsers(dest="plugin_action")

    # plugin cupp
    plugin_sub.add_parser("cupp", help="Run CUPP interactive profiler")


    # plugin sequence
    seq_p = plugin_sub.add_parser("sequence", help="Generate numeric sequence wordlist")
    seq_p.add_argument("--start", type=int, default=0, help="start number")
    seq_p.add_argument("--end", type=int, default=100, help="end number")
    seq_p.add_argument("--prefix", default="", help="string prefix")
    seq_p.add_argument("--suffix", default="", help="string suffix")
    seq_p.add_argument("--pad-width", type=int, default=0, help="zero-padding width")
    seq_p.add_argument("--output", default="sequence_wordlist.txt", help="output file path")

    # plugin list
    plugin_sub.add_parser("list", help="List available plugins")

    plugin_parser.set_defaults(func=_cmd_plugin)

    return parser


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    """BlueCrack CLI entry point — called by the ``bluecrack`` console_scripts command."""
    _configure_encoding()

    parser = _build_parser()
    args = parser.parse_args()

    # Default: no subcommand → launch web UI
    if args.command is None:
        args.host = "127.0.0.1"
        args.port = 5000
        args.debug = False
        _cmd_web(args)
        return

    # Dispatch to subcommand handler
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
