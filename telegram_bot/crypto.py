"""Standalone crypto helpers for the Telegram bot.

Duplicated from chronicle.sync.crypto so the bot has no dependency on the
chronicle package and can be deployed independently.
"""

from __future__ import annotations

from cryptography.fernet import Fernet


def encrypt_payload(plaintext: str, key: bytes) -> str:
    """Encrypt a plaintext string with a Fernet key."""
    f = Fernet(key)
    return f.encrypt(plaintext.encode("utf-8")).decode("ascii")
