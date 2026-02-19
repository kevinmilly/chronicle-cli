"""Encryption layer for Chronicle sync — Fernet + PBKDF2 key derivation."""

from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def generate_salt() -> bytes:
    """Generate a random 16-byte salt."""
    return os.urandom(16)


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a Fernet key from a passphrase and salt using PBKDF2-HMAC-SHA256.

    Uses 480,000 iterations per OWASP recommendations.
    Returns a URL-safe base64-encoded 32-byte key suitable for Fernet.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    raw_key = kdf.derive(passphrase.encode("utf-8"))
    return base64.urlsafe_b64encode(raw_key)


def encrypt_payload(plaintext: str, key: bytes) -> str:
    """Encrypt a plaintext string with a Fernet key.

    Returns a base64-encoded Fernet token as a string.
    """
    f = Fernet(key)
    return f.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_payload(ciphertext: str, key: bytes) -> str:
    """Decrypt a Fernet token back to a plaintext string.

    Raises cryptography.fernet.InvalidToken on wrong key or tampered data.
    """
    f = Fernet(key)
    return f.decrypt(ciphertext.encode("ascii")).decode("utf-8")
