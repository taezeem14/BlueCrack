"""Tests for command-line interface argument parsing."""

from bluecrack.cli import _build_parser


def test_cli_parser_subcommands():
    """Verify subcommands and flags in CLI parser."""
    parser = _build_parser()

    # Web command
    args_web = parser.parse_args(["web", "--host", "0.0.0.0", "--port", "8080", "--debug", "--reload"])
    assert args_web.command == "web"
    assert args_web.host == "0.0.0.0"
    assert args_web.port == 8080
    assert args_web.debug is True
    assert args_web.reload is True

    # Fingerprint command
    args_fp = parser.parse_args(["fingerprint", "https://example.com"])
    assert args_fp.command == "fingerprint"
    assert args_fp.url == "https://example.com"

    # Attack command with new flags
    args_atk = parser.parse_args([
        "attack",
        "-u", "admin",
        "-p", "pass123",
        "--url", "https://example.com/login",
        "--mode", "http",
        "--json-mode",
        "--headers", "Authorization: Bearer test",
        "--cookies", "session=123",
    ])
    assert args_atk.command == "attack"
    assert args_atk.username == "admin"
    assert args_atk.password == "pass123"
    assert args_atk.mode == "http"
    assert args_atk.json_mode is True
    assert args_atk.headers == "Authorization: Bearer test"
    assert args_atk.cookies == "session=123"


def test_cli_parser_doctor_flag():
    """Verify root --doctor flag."""
    parser = _build_parser()
    args = parser.parse_args(["--doctor"])
    assert args.doctor is True
