"""Tests for HTML and JSON ReportGenerator."""

import json

from bluecrack.reporter import ReportGenerator


def test_generate_html_report():
    """Verify ReportGenerator.generate_html produces valid HTML."""
    metrics = {
        "attempted": 50,
        "successes": 1,
        "failures": 48,
        "errors": 1,
        "skipped_empty": 0,
        "skipped_solved_user": 0,
    }
    found_creds = [("admin", "correctpass")]
    logs = ["[+] Attack started", "[+] VALID CREDENTIALS: admin / correctpass"]
    config = {"target_url": "https://example.com/login", "threads": 4}

    html = ReportGenerator.generate_html(
        metrics=metrics,
        found_creds=found_creds,
        logs=logs,
        config=config,
        start_time=1000.0,
        end_time=1050.0,
    )

    assert "<!DOCTYPE html>" in html
    assert "BlueCrack Attack Report" in html
    assert "https://example.com/login" in html
    assert "admin" in html
    assert "correctpass" in html
    assert "Chart" in html


def test_generate_json_report():
    """Verify ReportGenerator.generate_json produces valid parseable JSON."""
    metrics = {"attempted": 10, "successes": 1}
    found_creds = [("root", "toor")]
    config = {"target_url": "https://target.com/login"}

    json_str = ReportGenerator.generate_json(
        metrics=metrics,
        found_creds=found_creds,
        config=config,
        start_time=1000.0,
        end_time=1010.0,
    )

    data = json.loads(json_str)
    assert data["target_url"] == "https://target.com/login"
    assert data["metrics"]["attempted"] == 10
    assert len(data["found_credentials"]) == 1
    assert data["found_credentials"][0]["username"] == "root"


def test_generate_report_none_safety():
    """Verify ReportGenerator gracefully handles None/empty inputs without raising TypeError."""
    html = ReportGenerator.generate_html(
        metrics=None,
        found_creds=None,
        logs=None,
        config=None,
        start_time=None,
        end_time=None,
    )
    assert "<!DOCTYPE html>" in html

    json_str = ReportGenerator.generate_json(
        metrics=None,
        found_creds=None,
        config=None,
        start_time=None,
        end_time=None,
    )
    data = json.loads(json_str)
    assert data["elapsed_seconds"] == 0.0
    assert data["found_credentials"] == []

