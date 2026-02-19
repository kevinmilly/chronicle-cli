"""Configuration for the Chronicle Telegram bot.

Reads from ~/.chronicle/config.toml (same file used by `chronicle telegram setup`
and `chronicle sync setup`), with environment variable overrides.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path


def _load_toml() -> dict:
    """Load the chronicle config.toml if it exists."""
    toml_path = Path.home() / ".chronicle" / "config.toml"
    if toml_path.exists():
        with open(toml_path, "rb") as f:
            return tomllib.load(f)
    return {}


def _get(env_name: str, toml_section: str, toml_key: str, *, data: dict) -> str:
    """Return env var if set, otherwise fall back to the TOML value."""
    env_val = os.environ.get(env_name, "")
    if env_val:
        return env_val
    return str(data.get(toml_section, {}).get(toml_key, ""))


def _require(value: str, name: str) -> str:
    if not value:
        raise RuntimeError(
            f"{name} is not configured. "
            f"Run 'chronicle telegram setup' / 'chronicle sync setup' or set the env var."
        )
    return value


_data = _load_toml()

# Telegram
TELEGRAM_BOT_TOKEN: str = _require(
    _get("CHRONICLE_BOT_TOKEN", "telegram", "bot_token", data=_data),
    "CHRONICLE_BOT_TOKEN / [telegram] bot_token",
)
AUTHORIZED_USER_ID: int = int(_require(
    _get("CHRONICLE_AUTHORIZED_USER_ID", "telegram", "user_id", data=_data),
    "CHRONICLE_AUTHORIZED_USER_ID / [telegram] user_id",
))

# GitHub Gist
GITHUB_TOKEN: str = _require(
    _get("CHRONICLE_GITHUB_TOKEN", "sync", "github_token", data=_data),
    "CHRONICLE_GITHUB_TOKEN / [sync] github_token",
)
GIST_ID: str = _require(
    _get("CHRONICLE_GIST_ID", "sync", "gist_id", data=_data),
    "CHRONICLE_GIST_ID / [sync] gist_id",
)

# Encryption
SYNC_KEY: bytes = _require(
    _get("CHRONICLE_SYNC_KEY", "sync", "encryption_key", data=_data),
    "CHRONICLE_SYNC_KEY / [sync] encryption_key",
).encode("ascii")
