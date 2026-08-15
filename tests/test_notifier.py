"""Tests for Discord and Telegram notification alerts."""

from unittest.mock import patch

from bluecrack.notifier import Notifier


def test_notifier_configuration():
    """Test setting and checking notifier backends."""
    n = Notifier()
    assert len(n._backends) == 0

    n.add_discord("https://discord.com/api/webhooks/123/abc")
    n.add_telegram("123456:ABC-DEF", "987654321")
    assert len(n._backends) == 2


def test_notifier_payload_dispatch():
    """Test notify triggers HTTP requests with formatted payloads."""
    n = Notifier()
    n.add_discord("https://discord.com/api/webhooks/test")
    n.add_telegram("test_token", "test_chat")

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200

        n.notify(
            event="credential_found",
            data={
                "username": "admin",
                "password": "secretpassword",
                "target_url": "https://target.com/login",
            },
        )

        assert mock_post.called
        assert mock_post.call_count == 2
