"""Tests for Flask Web API endpoints."""

import pytest

from bluecrack.web import app


@pytest.fixture
def client():
    """Create Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_index_page(client):
    """Verify index HTML page loads with 200 OK and no-cache headers."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"BLUECRACK" in resp.data
    assert "no-cache" in resp.headers.get("Cache-Control", "")


def test_doctor_api(client):
    """Verify /api/doctor returns structured diagnostics."""
    resp = client.get("/api/doctor")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "report" in data
    assert "checks" in data["report"]


def test_session_status_api(client):
    """Verify /api/session/status returns session availability."""
    resp = client.get("/api/session/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "has_session" in data


def test_targets_queue_api(client):
    """Verify /api/targets/list, /api/targets, /api/targets/add, and /api/targets/clear."""
    # List targets
    resp = client.get("/api/targets")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"

    # Add target
    add_resp = client.post("/api/targets/add", json={
        "config": {"target_url": "https://test.com/login", "username": "admin", "password": "123"}
    })
    assert add_resp.status_code == 200
    assert add_resp.get_json()["status"] == "ok"

    # Clear targets
    clear_resp = client.post("/api/targets/clear")
    assert clear_resp.status_code == 200
    assert clear_resp.get_json()["status"] == "ok"


def test_schedule_api(client):
    """Verify /api/schedule, /api/schedule/list, /api/schedule/create, and /api/schedule/cancel."""
    resp = client.get("/api/schedule")
    assert resp.status_code == 200
    assert "tasks" in resp.get_json()

    # Create scheduled task
    create_resp = client.post("/api/schedule/create", json={
        "target_url": "http://127.0.0.1:5001/login",
        "run_at": "2030-01-01T00:00:00",
        "config": {"target_url": "http://127.0.0.1:5001/login", "username": "admin", "password": "123"}
    })
    assert create_resp.status_code == 200
    task_id = create_resp.get_json()["id"]

    # Cancel scheduled task
    cancel_resp = client.post("/api/schedule/cancel", json={"task_id": task_id})
    assert cancel_resp.status_code == 200
    assert cancel_resp.get_json()["status"] == "ok"


def test_demo_server_lifecycle_api(client):
    """Verify /api/demo/status and /api/demo/stop."""
    status_resp = client.get("/api/demo/status")
    assert status_resp.status_code == 200
    assert "running" in status_resp.get_json()

    stop_resp = client.post("/api/demo/stop")
    assert stop_resp.status_code == 200
    assert stop_resp.get_json()["status"] == "ok"


def test_cupp_and_sequence_generators_api(client):
    """Verify /api/cupp/generate and /api/sequence/generate endpoints."""
    cupp_resp = client.post("/api/cupp/generate", json={
        "first_name": "targetuser",
        "last_name": "smith",
        "keywords": "summer,admin,2026",
    })
    assert cupp_resp.status_code == 200
    assert cupp_resp.get_json()["status"] == "ok"

    seq_resp = client.post("/api/sequence/generate", json={
        "start": 0,
        "end": 20,
        "pad_width": 2,
    })
    assert seq_resp.status_code == 200
    assert seq_resp.get_json()["status"] == "ok"


def test_config_save_load_reset_api(client):
    """Verify saving, loading, and resetting configuration."""
    payload = {"target_url": "https://custom-target.com", "threads": "8"}
    save_resp = client.post("/api/config/save", json=payload)
    assert save_resp.status_code == 200
    assert save_resp.get_json()["status"] == "ok"

    load_resp = client.get("/api/config/load")
    assert load_resp.status_code == 200
    data = load_resp.get_json()
    assert data["status"] == "ok"
    assert data["config"]["target_url"] == "https://custom-target.com"

    reset_resp = client.post("/api/config/reset")
    assert reset_resp.status_code == 200

    load_after_reset = client.get("/api/config/load")
    assert load_after_reset.get_json()["config"] == {}


def test_notifications_config_api(client):
    """Verify notification configuration and retrieval endpoints."""
    config_resp = client.get("/api/notifications/config")
    assert config_resp.status_code == 200
    assert "config" in config_resp.get_json()

    set_resp = client.post("/api/notifications/configure", json={
        "discord_url": "https://discord.com/api/webhooks/test/url"
    })
    assert set_resp.status_code == 200
    cfg = set_resp.get_json()["config"]
    assert any(c.get("type") == "discord" for c in cfg)


def test_attack_status_and_logs_api(client):
    """Verify attack status, log retrieval and log clearing."""
    status_resp = client.get("/api/attack/status")
    assert status_resp.status_code == 200
    data = status_resp.get_json()
    assert "running" in data
    assert "metrics" in data
    assert "recent_logs" in data

    logs_resp = client.get("/api/logs")
    assert logs_resp.status_code == 200
    assert "logs" in logs_resp.get_json()

    clear_resp = client.post("/api/logs/clear")
    assert clear_resp.status_code == 200


