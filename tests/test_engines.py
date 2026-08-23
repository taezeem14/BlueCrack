"""Unit tests for BlueCrack core engines and report generator."""

import json
import time

from bluecrack.engine import AttackEngine
from bluecrack.http_engine import HTTPAttackEngine
from bluecrack.reporter import ReportGenerator


def test_attack_engine_init_and_metrics():
    """Test AttackEngine initialization, metrics structure, and thread safety."""
    engine = AttackEngine()
    assert not engine.is_running
    metrics = engine.get_metrics()
    assert metrics["attempted"] == 0
    assert metrics["successes"] == 0
    assert metrics["failures"] == 0
    assert metrics["errors"] == 0
    assert metrics["speed"] == 0.0
    assert metrics["eta"] == 0.0
    assert metrics["hits"] == 0
    assert engine.get_found_creds() == []
    assert engine.get_logs() == []


def test_http_attack_engine_init_and_metrics():
    """Test HTTPAttackEngine initialization and metrics structure."""
    engine = HTTPAttackEngine()
    assert not engine.is_running
    metrics = engine.get_metrics()
    assert metrics["attempted"] == 0
    assert metrics["successes"] == 0
    assert metrics["failures"] == 0
    assert metrics["errors"] == 0
    assert metrics["speed"] == 0.0
    assert metrics["eta"] == 0.0
    assert metrics["hits"] == 0
    assert engine.get_found_creds() == []
    assert engine.get_logs() == []


def test_report_generator_html_and_json():
    """Test ReportGenerator generates valid HTML and JSON output with escaping."""
    metrics = {
        "attempted": 100,
        "successes": 2,
        "failures": 95,
        "errors": 3,
        "skipped_empty": 0,
        "skipped_solved_user": 0,
    }
    creds = [("admin", "<script>alert(1)</script>"), ("user2", "pass2")]
    logs = ["[+] Started", "[*] Trying admin / pass", "[+] Hit!"]
    config = {
        "target_url": "http://example.com/login?param=<test>",
        "threads": 4,
        "delay": 0.1,
        "jitter": 0.05,
        "headless": True,
        "use_tor": False,
    }
    start = time.time() - 10
    end = time.time()

    html_out = ReportGenerator.generate_html(
        metrics=metrics,
        found_creds=creds,
        logs=logs,
        config=config,
        start_time=start,
        end_time=end,
    )
    assert "<!DOCTYPE html>" in html_out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_out
    assert "<script>alert(1)</script>" not in html_out  # Verify XSS escaped
    assert "param=&lt;test&gt;" in html_out

    json_out = ReportGenerator.generate_json(
        metrics=metrics,
        found_creds=creds,
        config=config,
        start_time=start,
        end_time=end,
    )
    data = json.loads(json_out)
    assert data["metrics"]["attempted"] == 100
    assert data["metrics"]["successes"] == 2
    assert len(data["found_credentials"]) == 2
    assert data["found_credentials"][0]["username"] == "admin"
    assert data["found_credentials"][0]["password"] == "<script>alert(1)</script>"


def test_engine_found_callback():
    """Verify that found_callback is triggered when emit_found is called."""
    engine = AttackEngine()
    found = []

    def _found_cb(u, p, target):
        found.append((u, p, target))

    engine.set_callbacks(found_cb=_found_cb)
    engine._emit_found("admin", "secret123", "http://test.com/login")
    assert len(found) == 1
    assert found[0] == ("admin", "secret123", "http://test.com/login")

    http_engine = HTTPAttackEngine()
    http_found = []
    http_engine.set_callbacks(found_cb=lambda u, p, t: http_found.append((u, p, t)))
    http_engine._emit_found("user1", "pass123", "http://test.com/http-login")
    assert len(http_found) == 1
    assert http_found[0] == ("user1", "pass123", "http://test.com/http-login")

