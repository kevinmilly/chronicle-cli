"""Tests for chronicle.sync.crypto — key derivation and encrypt/decrypt."""

from __future__ import annotations

import pytest

from chronicle.sync.crypto import (
    decrypt_payload,
    derive_key,
    encrypt_payload,
    generate_salt,
)


class TestGenerateSalt:
    def test_returns_16_bytes(self):
        salt = generate_salt()
        assert isinstance(salt, bytes)
        assert len(salt) == 16

    def test_unique_each_call(self):
        assert generate_salt() != generate_salt()


class TestDeriveKey:
    def test_deterministic(self):
        salt = b"0123456789abcdef"
        key1 = derive_key("my-passphrase", salt)
        key2 = derive_key("my-passphrase", salt)
        assert key1 == key2

    def test_different_passphrase_different_key(self):
        salt = b"0123456789abcdef"
        key1 = derive_key("passphrase-a", salt)
        key2 = derive_key("passphrase-b", salt)
        assert key1 != key2

    def test_different_salt_different_key(self):
        key1 = derive_key("same-pass", b"salt_aaaaaaaaaaaa")
        key2 = derive_key("same-pass", b"salt_bbbbbbbbbbbb")
        assert key1 != key2

    def test_key_is_valid_fernet_key(self):
        from cryptography.fernet import Fernet

        salt = generate_salt()
        key = derive_key("test", salt)
        # Should not raise — valid Fernet key
        Fernet(key)


class TestEncryptDecrypt:
    def test_roundtrip(self):
        salt = generate_salt()
        key = derive_key("test-passphrase", salt)
        plaintext = "Hello, Chronicle!"
        ciphertext = encrypt_payload(plaintext, key)
        assert ciphertext != plaintext
        result = decrypt_payload(ciphertext, key)
        assert result == plaintext

    def test_roundtrip_multiline(self):
        salt = generate_salt()
        key = derive_key("pass", salt)
        plaintext = "@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 entry\nHello world\n@end"
        ciphertext = encrypt_payload(plaintext, key)
        assert decrypt_payload(ciphertext, key) == plaintext

    def test_wrong_passphrase_raises(self):
        from cryptography.fernet import InvalidToken

        salt = generate_salt()
        key_good = derive_key("correct-pass", salt)
        key_bad = derive_key("wrong-pass", salt)
        ciphertext = encrypt_payload("secret", key_good)

        with pytest.raises(InvalidToken):
            decrypt_payload(ciphertext, key_bad)

    def test_unicode_content(self):
        salt = generate_salt()
        key = derive_key("pass", salt)
        plaintext = "Had a great day! 🎉 Très bien."
        assert decrypt_payload(encrypt_payload(plaintext, key), key) == plaintext
