"""Tests for chronicle.exporters.markdown."""

from datetime import datetime, date, timezone
from pathlib import Path

from chronicle.models import Entry
from chronicle.exporters.markdown import entry_to_markdown, export_all, export_split


def _make_entry(**kwargs) -> Entry:
    defaults = dict(
        id="20260101-1200-ab12",
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        entry_type="win",
        tags=["coding", "python"],
        people=["Alice"],
        review_date=None,
        ref=None,
        body="Great day coding.",
    )
    defaults.update(kwargs)
    return Entry(**defaults)


def test_front_matter_correctness():
    e = _make_entry()
    md = entry_to_markdown(e)
    assert md.startswith("---\n")
    assert "id: 20260101-1200-ab12" in md
    assert "type: win" in md
    assert "tags: [coding, python]" in md
    assert "people: [Alice]" in md


def test_body_after_front_matter():
    e = _make_entry(body="Hello world.")
    md = entry_to_markdown(e)
    parts = md.split("---")
    # parts[0] is empty, parts[1] is front matter, parts[2] is body
    assert "Hello world." in parts[2]


def test_optional_fields_omitted():
    e = _make_entry(tags=[], people=[], review_date=None, ref=None)
    md = entry_to_markdown(e)
    assert "tags:" not in md
    assert "people:" not in md
    assert "review_date:" not in md
    assert "ref:" not in md


def test_review_date_and_ref_included():
    e = _make_entry(review_date=date(2026, 6, 1), ref="20250101-0800-0000")
    md = entry_to_markdown(e)
    assert "review_date: 2026-06-01" in md
    assert "ref: 20250101-0800-0000" in md


def test_export_all():
    entries = [
        _make_entry(id="20260101-1200-ab12"),
        _make_entry(id="20260102-0800-cd34"),
    ]
    result = export_all(entries)
    assert result.count("---") == 4  # 2 entries x 2 delimiters each


def test_export_split(tmp_path: Path):
    entries = [
        _make_entry(id="20260101-1200-ab12"),
        _make_entry(id="20260102-0800-cd34"),
    ]
    paths = export_split(entries, tmp_path)
    assert len(paths) == 2
    assert (tmp_path / "20260101-1200-ab12.md").exists()
    assert (tmp_path / "20260102-0800-cd34.md").exists()

    content = (tmp_path / "20260101-1200-ab12.md").read_text()
    assert "id: 20260101-1200-ab12" in content
