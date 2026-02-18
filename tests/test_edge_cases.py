"""Edge case tests."""

from datetime import datetime, date, timezone

from chronicle.models import Entry
from chronicle.parser import parse_log
from chronicle.storage import format_entry
from chronicle.exporters.weekly import generate_weekly_brief
from chronicle.exporters.markdown import entry_to_markdown


def _make_entry(**kwargs) -> Entry:
    defaults = dict(
        id="20260101-1200-ab12",
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        entry_type="win",
        tags=[],
        people=[],
        review_date=None,
        ref=None,
        body="Hello.",
    )
    defaults.update(kwargs)
    return Entry(**defaults)


def test_zero_entries_weekly():
    brief = generate_weekly_brief([], date(2026, 1, 1), date(2026, 1, 7))
    assert "Weekly Brief" in brief
    assert "No entries this week" in brief


def test_boundary_dates_inclusive():
    e1 = _make_entry(
        id="e1",
        timestamp=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
    )
    e2 = _make_entry(
        id="e2",
        timestamp=datetime(2026, 1, 7, 23, 59, tzinfo=timezone.utc),
    )
    e3 = _make_entry(
        id="e3",
        timestamp=datetime(2026, 1, 8, 0, 0, tzinfo=timezone.utc),
    )
    entries = [e1, e2, e3]
    start = date(2026, 1, 1)
    end = date(2026, 1, 7)
    filtered = [e for e in entries if start <= e.timestamp.date() <= end]
    assert len(filtered) == 2
    assert filtered[0].id == "e1"
    assert filtered[1].id == "e2"


def test_large_body():
    body = "\n".join([f"Line {i}" for i in range(500)])
    entry = _make_entry(body=body)
    text = format_entry(entry) + "\n"
    entries = parse_log(text)
    assert len(entries) == 1
    assert entries[0].body.count("\n") == 499


def test_unicode_and_emoji():
    body = "Today was great! \U0001f389\nJapanese: \u65e5\u672c\u8a9e\nArabic: \u0645\u0631\u062d\u0628\u0627"
    entry = _make_entry(body=body)
    text = format_entry(entry) + "\n"
    entries = parse_log(text)
    assert "\U0001f389" in entries[0].body
    assert "\u65e5\u672c\u8a9e" in entries[0].body


def test_empty_tags_and_people_in_markdown():
    entry = _make_entry(tags=[], people=[])
    md = entry_to_markdown(entry)
    assert "tags:" not in md
    assert "people:" not in md
