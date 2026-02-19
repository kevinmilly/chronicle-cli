"""Chronicle Telegram Bot — Google Cloud Function entry point (webhook mode).

Receives Telegram updates via webhook, formats the message as a chronicle
entry, encrypts it, and appends it to a GitHub Gist.

Deploy with:
    gcloud functions deploy chronicle-bot \
        --runtime python312 --trigger-http --allow-unauthenticated \
        --source telegram_bot --entry-point webhook \
        --set-env-vars CHRONICLE_BOT_TOKEN=...,CHRONICLE_AUTHORIZED_USER_ID=...,\
    CHRONICLE_GITHUB_TOKEN=...,CHRONICLE_GIST_ID=...,CHRONICLE_SYNC_KEY=...

Then set the webhook:
    curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<CLOUD_FUNCTION_URL>"
"""

from __future__ import annotations

import json
import logging
import secrets
import urllib.error
import urllib.request
from datetime import datetime, timezone

import config
import crypto

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

GIST_FILENAME = "chronicle_sync.enc"


# ── Telegram helpers ─────────────────────────────────────────────────

def _send_message(chat_id: int, text: str) -> None:
    """Send a message via the Telegram Bot API."""
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        resp.read()


# ── Gist helpers ─────────────────────────────────────────────────────

def _gist_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _gist_read() -> str:
    url = f"https://api.github.com/gists/{config.GIST_ID}"
    req = urllib.request.Request(url, headers=_gist_headers())
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    file_info = data.get("files", {}).get(GIST_FILENAME)
    return file_info.get("content", "") if file_info else ""


def _gist_write(content: str) -> None:
    url = f"https://api.github.com/gists/{config.GIST_ID}"
    payload = json.dumps({"files": {GIST_FILENAME: {"content": content}}}).encode()
    req = urllib.request.Request(url, data=payload, headers=_gist_headers(), method="PATCH")
    with urllib.request.urlopen(req) as resp:
        resp.read()


def _gist_append(line: str) -> None:
    existing = _gist_read()
    if existing and not existing.endswith("\n"):
        new_content = existing + "\n" + line + "\n"
    elif existing:
        new_content = existing + line + "\n"
    else:
        new_content = line + "\n"
    _gist_write(new_content)


# ── Entry formatting ─────────────────────────────────────────────────

def _format_entry(body: str, *, entry_type: str = "entry") -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    hex_suffix = secrets.token_hex(2)
    entry_id = f"{now.strftime('%Y%m%d-%H%M')}-{hex_suffix}"

    header = f"@entry {entry_id} {now.isoformat()} {entry_type}"
    lines = [header, body, "@end"]
    return entry_id, "\n".join(lines)


# ── Cloud Function entry point ───────────────────────────────────────

def webhook(request):
    """HTTP Cloud Function entry point.

    Telegram sends a JSON update to this endpoint. We parse the message,
    encrypt it, append to the Gist, and reply to the user.
    """
    if request.method != "POST":
        return ("Method not allowed", 405)

    try:
        update = request.get_json(silent=True)
    except Exception:
        return ("Bad request", 400)

    if not update:
        return ("No update payload", 400)

    # Extract the message (ignore edits, channel posts, etc.)
    message = update.get("message")
    if not message:
        return ("OK", 200)

    # Auth check
    from_user = message.get("from", {})
    user_id = from_user.get("id")
    if user_id != config.AUTHORIZED_USER_ID:
        logger.warning("Unauthorized user %s", user_id)
        return ("OK", 200)

    # Only handle text messages (skip commands starting with /)
    text = message.get("text", "").strip()
    if not text or text.startswith("/"):
        return ("OK", 200)

    chat_id = message["chat"]["id"]

    # Format, encrypt, upload
    entry_id, formatted = _format_entry(text)
    encrypted = crypto.encrypt_payload(formatted, config.SYNC_KEY)

    try:
        _gist_append(encrypted)
        _send_message(chat_id, f"Logged: {entry_id}")
    except Exception as e:
        logger.error("Failed to upload: %s", e)
        _send_message(chat_id, f"Failed to sync: {e}")

    return ("OK", 200)
