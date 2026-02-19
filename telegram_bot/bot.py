"""Chronicle Telegram Bot — captures messages and syncs to GitHub Gist.

Listens for text messages from an authorized Telegram user, formats them
as chronicle entries, encrypts with Fernet, and appends to a GitHub Gist.

Commands:
  /tag work,python       — set tags for the next entry
  /people Alice,Bob      — set people for the next entry
  /type decision         — set entry type (default: entry)
  /status                — show bot status
"""

from __future__ import annotations

import json
import logging
import secrets
import urllib.error
import urllib.request
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
import crypto

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

GIST_FILENAME = "chronicle_sync.enc"


# ── Gist helpers ───────────────────────────────────────────────────────

def _gist_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _gist_read() -> str:
    """Read current Gist content."""
    url = f"https://api.github.com/gists/{config.GIST_ID}"
    req = urllib.request.Request(url, headers=_gist_headers())
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    file_info = data.get("files", {}).get(GIST_FILENAME)
    return file_info.get("content", "") if file_info else ""


def _gist_write(content: str) -> None:
    """Overwrite Gist content."""
    url = f"https://api.github.com/gists/{config.GIST_ID}"
    payload = json.dumps({"files": {GIST_FILENAME: {"content": content}}}).encode()
    req = urllib.request.Request(url, data=payload, headers=_gist_headers(), method="PATCH")
    with urllib.request.urlopen(req) as resp:
        resp.read()


def _gist_append(line: str) -> None:
    """Append an encrypted line to the Gist."""
    existing = _gist_read()
    if existing and not existing.endswith("\n"):
        new_content = existing + "\n" + line + "\n"
    elif existing:
        new_content = existing + line + "\n"
    else:
        new_content = line + "\n"
    _gist_write(new_content)


# ── Entry formatting ──────────────────────────────────────────────────

def _format_entry(
    body: str,
    *,
    entry_type: str = "entry",
    tags: list[str] | None = None,
    people: list[str] | None = None,
) -> tuple[str, str]:
    """Format a chronicle entry and return (entry_id, formatted_text)."""
    now = datetime.now(timezone.utc)
    hex_suffix = secrets.token_hex(2)
    entry_id = f"{now.strftime('%Y%m%d-%H%M')}-{hex_suffix}"

    parts = [f"@entry {entry_id} {now.isoformat()} {entry_type}"]
    if tags:
        parts.append(f"[{','.join(tags)}]")
    if people:
        parts.append(f"[people:{','.join(people)}]")

    header = " ".join(parts)
    lines = [header, body, "@end"]
    return entry_id, "\n".join(lines)


# ── Per-user state ────────────────────────────────────────────────────

# Pending metadata for the next entry (cleared after use)
user_state: dict[str, str | list[str]] = {
    "tags": [],
    "people": [],
    "type": "entry",
}


def _reset_state() -> None:
    user_state["tags"] = []
    user_state["people"] = []
    user_state["type"] = "entry"


# ── Auth check ────────────────────────────────────────────────────────

def _is_authorized(update: Update) -> bool:
    return update.effective_user is not None and update.effective_user.id == config.AUTHORIZED_USER_ID


# ── Handlers ──────────────────────────────────────────────────────────

async def cmd_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    if context.args:
        user_state["tags"] = [t.strip() for t in " ".join(context.args).split(",") if t.strip()]
        await update.message.reply_text(f"Tags set: {', '.join(user_state['tags'])}")
    else:
        await update.message.reply_text("Usage: /tag work,python")


async def cmd_people(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    if context.args:
        user_state["people"] = [p.strip() for p in " ".join(context.args).split(",") if p.strip()]
        await update.message.reply_text(f"People set: {', '.join(user_state['people'])}")
    else:
        await update.message.reply_text("Usage: /people Alice,Bob")


async def cmd_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    if context.args:
        user_state["type"] = context.args[0].strip()
        await update.message.reply_text(f"Entry type set: {user_state['type']}")
    else:
        await update.message.reply_text("Usage: /type decision")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        return
    await update.message.reply_text(
        f"Chronicle Bot active\n"
        f"Gist: {config.GIST_ID[:8]}...\n"
        f"Pending tags: {user_state.get('tags', [])}\n"
        f"Pending people: {user_state.get('people', [])}\n"
        f"Entry type: {user_state.get('type', 'entry')}"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any text message — create a journal entry."""
    if not _is_authorized(update):
        logger.warning("Unauthorized user %s", update.effective_user.id)
        return

    body = update.message.text.strip()
    if not body:
        return

    tags = user_state.get("tags", [])
    people = user_state.get("people", [])
    entry_type = user_state.get("type", "entry")

    entry_id, formatted = _format_entry(
        body,
        entry_type=entry_type,
        tags=tags if tags else None,
        people=people if people else None,
    )

    # Encrypt and upload
    key = crypto.derive_key(config.SYNC_PASSPHRASE, config.SYNC_SALT)
    encrypted = crypto.encrypt_payload(formatted, key)

    try:
        _gist_append(encrypted)
        await update.message.reply_text(f"Logged: {entry_id}")
    except Exception as e:
        logger.error("Failed to upload: %s", e)
        await update.message.reply_text(f"Failed to sync: {e}")

    # Reset pending metadata
    _reset_state()


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("tag", cmd_tag))
    application.add_handler(CommandHandler("people", cmd_people))
    application.add_handler(CommandHandler("type", cmd_type))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot starting...")
    application.run_polling()


if __name__ == "__main__":
    main()
