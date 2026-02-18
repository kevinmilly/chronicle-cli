"""Tests for chronicle.ai.process."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from chronicle.ai.process import (
    load_processed,
    save_processed,
    ProcessedResult,
    _build_batch_prompt,
)
from chronicle.models import Entry


def _make_entry(id: str = "20260101-1200-ab12", body: str = "Hello.") -> Entry:
    return Entry(
        id=id,
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        entry_type="entry",
        tags=[],
        people=[],
        review_date=None,
        ref=None,
        body=body,
    )


def test_load_processed_missing_file(tmp_path: Path):
    result = load_processed(tmp_path / "nonexistent.json")
    assert result == {}


def test_load_processed_existing(tmp_path: Path):
    path = tmp_path / "ai_processed.json"
    data = {"20260101-1200-ab12": {"categories": ["win"], "summary": "Test"}}
    path.write_text(json.dumps(data))

    result = load_processed(path)
    assert result["20260101-1200-ab12"]["categories"] == ["win"]


def test_save_processed(tmp_path: Path):
    path = tmp_path / "ai_processed.json"
    data = {"id1": {"categories": ["block"], "summary": "Blocked"}}
    save_processed(data, path)

    loaded = json.loads(path.read_text())
    assert loaded["id1"]["categories"] == ["block"]


def test_build_batch_prompt():
    entries = [
        _make_entry(id="e1", body="First entry body."),
        _make_entry(id="e2", body="Second entry body."),
    ]
    prompt = _build_batch_prompt(entries)
    assert "Entry ID: e1" in prompt
    assert "Entry ID: e2" in prompt
    assert "First entry body." in prompt
    assert "Second entry body." in prompt


def test_processed_result_dataclass():
    r = ProcessedResult(
        id="e1",
        categories=["win", "lesson_learned"],
        summary="A win and a lesson",
        corrected_body="Corrected text.",
    )
    assert r.id == "e1"
    assert "win" in r.categories
    assert r.corrected_body == "Corrected text."
