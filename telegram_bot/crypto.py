"""Standalone crypto helpers for the Telegram bot.

Duplicated from chronicle.sync.crypto so the bot has no dependency on the
chronicle package and can be deployed independently.
"""

from __future__ import annotations

import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a Fernet key from a passphrase and salt using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    raw_key = kdf.derive(passphrase.encode("utf-8"))
    return base64.urlsafe_b64encode(raw_key)


def encrypt_payload(plaintext: str, key: bytes) -> str:
    """Encrypt a plaintext string with a Fernet key."""
    f = Fernet(key)
    return f.encrypt(plaintext.encode("utf-8")).decode("ascii")
