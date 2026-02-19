"""Encryption layer for Chronicle sync — Fernet symmetric encryption."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


def generate_key() -> bytes:
    """Generate a random Fernet key (URL-safe base64-encoded 32 bytes)."""
    return Fernet.generate_key()


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
