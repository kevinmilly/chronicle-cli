"""Tests for chronicle.sync.crypto — key generation and encrypt/decrypt."""

from __future__ import annotations

import pytest

from chronicle.sync.crypto import (
    decrypt_payload,
    encrypt_payload,
    generate_key,
)


class TestGenerateKey:
    def test_returns_bytes(self):
        key = generate_key()
        assert isinstance(key, bytes)

    def test_valid_fernet_key(self):
        from cryptography.fernet import Fernet

        key = generate_key()
        # Should not raise — valid Fernet key
        Fernet(key)

    def test_unique_each_call(self):
        assert generate_key() != generate_key()


class TestEncryptDecrypt:
    def test_roundtrip(self):
        key = generate_key()
        plaintext = "Hello, Chronicle!"
        ciphertext = encrypt_payload(plaintext, key)
        assert ciphertext != plaintext
        result = decrypt_payload(ciphertext, key)
        assert result == plaintext

    def test_roundtrip_multiline(self):
        key = generate_key()
        plaintext = "@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 entry\nHello world\n@end"
        ciphertext = encrypt_payload(plaintext, key)
        assert decrypt_payload(ciphertext, key) == plaintext

    def test_wrong_key_raises(self):
        from cryptography.fernet import InvalidToken

        key_good = generate_key()
        key_bad = generate_key()
        ciphertext = encrypt_payload("secret", key_good)

        with pytest.raises(InvalidToken):
            decrypt_payload(ciphertext, key_bad)

    def test_unicode_content(self):
        key = generate_key()
        plaintext = "Had a great day! 🎉 Très bien."
        assert decrypt_payload(encrypt_payload(plaintext, key), key) == plaintext
