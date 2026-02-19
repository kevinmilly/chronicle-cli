"""Tests for chronicle.sync.pull — pull logic with mock backend."""

from __future__ import annotations

from pathlib import Path

import pytest

from chronicle.sync.backend import SyncBackend
from chronicle.sync.crypto import encrypt_payload, generate_key
from chronicle.sync.pull import pull
from chronicle.storage import format_entry
from chronicle.parser import parse_file
from chronicle.models import Entry

from datetime import datetime, timezone


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


class TestPull:
    def test_empty_remote(self, tmp_path, key):
        log = tmp_path / "chronicle.log"
        log.touch()
        backend = MockBackend("")
        assert pull(backend, key, log) == 0

    def test_pull_single_entry(self, tmp_path, key):
        log = tmp_path / "chronicle.log"
        log.touch()

        entry = _make_entry("20260101-1200-aa11", "Hello from remote")
        plaintext = format_entry(entry)
        token = encrypt_payload(plaintext, key)
        backend = MockBackend(token + "\n")

        added = pull(backend, key, log)
        assert added == 1
        entries = parse_file(log)
        assert len(entries) == 1
        assert entries[0].id == "20260101-1200-aa11"
        assert entries[0].body == "Hello from remote"

    def test_pull_multiple_entries(self, tmp_path, key):
        log = tmp_path / "chronicle.log"
        log.touch()

        tokens = []
        for i in range(3):
            entry = _make_entry(f"20260101-120{i}-aa1{i}", f"Entry {i}")
            tokens.append(encrypt_payload(format_entry(entry), key))

        backend = MockBackend("\n".join(tokens) + "\n")
        added = pull(backend, key, log)
        assert added == 3

    def test_deduplication(self, tmp_path, key):
        log = tmp_path / "chronicle.log"

        # Pre-populate local with one entry
        entry_local = _make_entry("20260101-1200-aa11", "Already local")
        from chronicle.storage import append_entry
        log.touch()
        append_entry(entry_local, log)

        # Remote has same entry + one new one
        entry_remote_dup = _make_entry("20260101-1200-aa11", "Already local")
        entry_remote_new = _make_entry("20260102-0900-bb22", "New from remote")
        tokens = [
            encrypt_payload(format_entry(entry_remote_dup), key),
            encrypt_payload(format_entry(entry_remote_new), key),
        ]
        backend = MockBackend("\n".join(tokens) + "\n")

        added = pull(backend, key, log)
        assert added == 1
        entries = parse_file(log)
        assert len(entries) == 2
        ids = {e.id for e in entries}
        assert "20260101-1200-aa11" in ids
        assert "20260102-0900-bb22" in ids

    def test_pull_idempotent(self, tmp_path, key):
        log = tmp_path / "chronicle.log"
        log.touch()

        entry = _make_entry("20260101-1200-aa11", "Hello")
        token = encrypt_payload(format_entry(entry), key)
        backend = MockBackend(token + "\n")

        assert pull(backend, key, log) == 1
        assert pull(backend, key, log) == 0  # second pull: no new entries
