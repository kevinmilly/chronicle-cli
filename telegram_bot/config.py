"""Configuration for the Chronicle Telegram bot — all via environment variables."""

from __future__ import annotations

import os


def _require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


# Telegram
TELEGRAM_BOT_TOKEN: str = _require_env("CHRONICLE_BOT_TOKEN")
AUTHORIZED_USER_ID: int = int(_require_env("CHRONICLE_AUTHORIZED_USER_ID"))

# GitHub Gist
GITHUB_TOKEN: str = _require_env("CHRONICLE_GITHUB_TOKEN")
GIST_ID: str = _require_env("CHRONICLE_GIST_ID")

# Encryption
SYNC_PASSPHRASE: str = _require_env("CHRONICLE_SYNC_PASSPHRASE")
SYNC_SALT_HEX: str = _require_env("CHRONICLE_SYNC_SALT")
SYNC_SALT: bytes = bytes.fromhex(SYNC_SALT_HEX)
