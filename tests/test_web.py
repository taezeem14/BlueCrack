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
    """Verify index HTML page loads with 200 OK."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"BLUECRACK" in resp.data


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
    """Verify /api/targets/list and /api/targets/add."""
    # List targets
    resp = client.get("/api/targets/list")
    assert resp.status_code == 200

    # Add target
    add_resp = client.post("/api/targets/add", json={
        "config": {"target_url": "https://test.com/login", "username": "admin", "password": "123"}
    })
    assert add_resp.status_code == 200
    assert add_resp.get_json()["status"] == "ok"


def test_schedule_api(client):
    """Verify /api/schedule/list endpoint."""
    resp = client.get("/api/schedule/list")
    assert resp.status_code == 200
    assert "scheduled" in resp.get_json()
