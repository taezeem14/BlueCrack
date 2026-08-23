"""Tests for Discord and Telegram notification alerts."""

import time
from unittest.mock import MagicMock, patch

from bluecrack.notifier import Notifier


def test_notifier_configuration():
    """Test setting and checking notifier backends."""
    n = Notifier()
    assert len(n._backends) == 0

    n.add_discord("https://discord.com/api/webhooks/123/abc")
    n.add_telegram("123456:ABC-DEF", "987654321")
    assert len(n._backends) == 2
    assert n.has_backends is True

    cfg = n.get_config()
    assert len(cfg) == 2
    assert cfg[0]["type"] == "discord"
    assert cfg[1]["type"] == "telegram"


def test_notifier_test_dispatch():
    """Test synchronous test method sends to all backends."""
    n = Notifier()
    n.add_discord("https://discord.com/api/webhooks/test")
    n.add_telegram("test_token", "test_chat")

    with patch("bluecrack.notifier.requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        results = n.test()
        assert results.get("discord") is True
        assert results.get("telegram") is True
        assert mock_post.call_count == 2


def test_notifier_payload_dispatch():
    """Test notify triggers HTTP requests with formatted payloads."""
    n = Notifier()
    n.add_discord("https://discord.com/api/webhooks/test")
    n.add_telegram("test_token", "test_chat")

    with patch("bluecrack.notifier.requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        n.notify(
            event="credential_found",
            data={
                "username": "admin",
                "password": "secretpassword",
                "target_url": "https://target.com/login",
            },
        )

        # Allow background daemon threads to fire
        for _ in range(20):
            if mock_post.call_count >= 2:
                break
            time.sleep(0.05)

        assert mock_post.called
        assert mock_post.call_count == 2


def test_notifier_headers_and_attack_complete():
    """Verify headers and attack_complete notification dispatch."""
    n = Notifier()
    n.add_discord("https://discord.com/api/webhooks/test")

    with patch("bluecrack.notifier.requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        n.notify("attack_complete", {"successes": 1, "attempted": 10, "elapsed": 5.2})

        for _ in range(20):
            if mock_post.call_count >= 1:
                break
            time.sleep(0.05)

        assert mock_post.called
        _, kwargs = mock_post.call_args
        assert "headers" in kwargs
        assert kwargs["headers"]["User-Agent"] == "BlueCrack-Notifier/4.2"


