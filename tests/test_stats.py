"""Tests for chronicle.stats."""

from __future__ import annotations

import json
from datetime import datetime, date, timezone
from pathlib import Path

from chronicle.models import Entry
from chronicle.stats import generate_stats


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


def test_stats_no_processed_file(tmp_path: Path):
    entries = [_make_entry()]
    result = generate_stats(entries, tmp_path / "nonexistent.json")
    assert "No processed entries" in result


def test_stats_with_categories(tmp_path: Path):
    entries = [
        _make_entry(id="e1", body="Landed the client contract"),
        _make_entry(id="e2", body="Waiting on API access"),
    ]
    processed_path = tmp_path / "ai_processed.json"
    processed_path.write_text(json.dumps({
        "e1": {"categories": ["win"], "summary": "Landed client contract"},
        "e2": {"categories": ["block"], "summary": "Waiting on API access"},
    }))

    result = generate_stats(entries, processed_path)
    assert "Chronicle Stats" in result
    assert "Wins (1):" in result
    assert "Blocks (1):" in result
    assert "Landed client contract" in result


def test_stats_category_filter(tmp_path: Path):
    entries = [
        _make_entry(id="e1", body="A win"),
        _make_entry(id="e2", body="A block"),
    ]
    processed_path = tmp_path / "ai_processed.json"
    processed_path.write_text(json.dumps({
        "e1": {"categories": ["win"], "summary": "A win"},
        "e2": {"categories": ["block"], "summary": "A block"},
    }))

    result = generate_stats(entries, processed_path, category="win")
    assert "Wins" in result
    assert "Blocks" not in result


def test_stats_date_filter(tmp_path: Path):
    entries = [
        _make_entry(id="e1", body="January entry"),
        Entry(
            id="e2",
            timestamp=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
            entry_type="entry",
            tags=[],
            people=[],
            review_date=None,
            ref=None,
            body="March entry",
        ),
    ]
    processed_path = tmp_path / "ai_processed.json"
    processed_path.write_text(json.dumps({
        "e1": {"categories": ["win"], "summary": "January win"},
        "e2": {"categories": ["win"], "summary": "March win"},
    }))

    result = generate_stats(
        entries, processed_path, from_date=date(2026, 2, 1), to_date=date(2026, 12, 31)
    )
    assert "March win" in result
    assert "January win" not in result
