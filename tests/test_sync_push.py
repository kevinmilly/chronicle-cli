"""Tests for chronicle.sync.push — push logic with mock backend."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from chronicle.models import Entry
from chronicle.parser import parse_log
from chronicle.storage import append_entry, format_entry
from chronicle.sync.backend import SyncBackend
from chronicle.sync.crypto import decrypt_payload, encrypt_payload, generate_key
from chronicle.sync.push import push


class MockBackend(SyncBackend):
    """In-memory backend for testing."""

    def __init__(self, content: str = ""):
        self.content = content

    def read(self) -> str:
        return self.content

    def write(self, content: str) -> None:
        self.content = content

    def append(self, line: str) -> None:
        if self.content and not self.content.endswith("\n"):
            self.content += "\n"
        self.content += line + "\n"


def _make_entry(entry_id: str, body: str) -> Entry:
    return Entry(
        id=entry_id,
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        entry_type="entry",
        tags=[],
        people=[],
        review_date=None,
        ref=None,
        body=body,
    )


@pytest.fixture
def key():
    return generate_key()


class TestPush:
    def test_empty_log(self, tmp_path, key):
        log = tmp_path / "chronicle.log"
        log.touch()
        backend = MockBackend()
        assert push(backend, key, log) == 0
        assert backend.content == ""

    def test_push_single_entry(self, tmp_path, key):
        log = tmp_path / "chronicle.log"
        log.touch()
        entry = _make_entry("20260101-1200-aa11", "Local entry")
        append_entry(entry, log)

        backend = MockBackend()
        count = push(backend, key, log)
        assert count == 1

        # Verify the remote content is encrypted and can be decrypted back
        tokens = [t for t in backend.content.strip().splitlines() if t.strip()]
        assert len(tokens) == 1
        plaintext = decrypt_payload(tokens[0], key)
        parsed = parse_log(plaintext)
        assert len(parsed) == 1
        assert parsed[0].id == "20260101-1200-aa11"
        assert parsed[0].body == "Local entry"

    def test_push_multiple_entries(self, tmp_path, key):
        log = tmp_path / "chronicle.log"
        log.touch()
        for i in range(3):
            entry = _make_entry(f"20260101-120{i}-aa1{i}", f"Entry {i}")
            append_entry(entry, log)

        backend = MockBackend()
        count = push(backend, key, log)
        assert count == 3

        tokens = [t for t in backend.content.strip().splitlines() if t.strip()]
        assert len(tokens) == 3

    def test_push_overwrites_remote(self, tmp_path, key):
        log = tmp_path / "chronicle.log"
        log.touch()
        entry = _make_entry("20260101-1200-aa11", "Entry one")
        append_entry(entry, log)

        backend = MockBackend("old-encrypted-stuff\n")
        push(backend, key, log)

        # Remote should NOT contain old content
        assert "old-encrypted-stuff" not in backend.content
        tokens = [t for t in backend.content.strip().splitlines() if t.strip()]
        assert len(tokens) == 1

    def test_nonexistent_log(self, tmp_path, key):
        log = tmp_path / "nonexistent.log"
        backend = MockBackend()
        assert push(backend, key, log) == 0
