"""Round-trip tests: format -> parse -> verify."""

from datetime import datetime, date, timezone

from chronicle.models import Entry
from chronicle.parser import parse_log
from chronicle.storage import format_entry, append_entry


def _make_entry(**kwargs) -> Entry:
    defaults = dict(
        id="20260101-1200-ab12",
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        entry_type="win",
        tags=["coding", "python"],
        people=["Alice"],
        review_date=None,
        ref=None,
        body="Finished the first module.",
    )
    defaults.update(kwargs)
    return Entry(**defaults)


def test_format_then_parse():
    entry = _make_entry()
    text = format_entry(entry) + "\n"
    entries = parse_log(text)
    assert len(entries) == 1
    parsed = entries[0]
    assert parsed.id == entry.id
    assert parsed.entry_type == entry.entry_type
    assert parsed.tags == entry.tags
    assert parsed.people == entry.people
    assert parsed.body == entry.body


def test_format_then_parse_with_all_fields():
    entry = _make_entry(
        review_date=date(2026, 6, 1),
        ref="20250101-0800-0000",
    )
    text = format_entry(entry) + "\n"
    entries = parse_log(text)
    parsed = entries[0]
    assert parsed.review_date == date(2026, 6, 1)
    assert parsed.ref == "20250101-0800-0000"


def test_append_then_parse(tmp_path):
    log_path = tmp_path / "chronicle.log"
    log_path.touch()

    e1 = _make_entry(id="20260101-1200-ab12")
    e2 = _make_entry(id="20260102-0800-cd34", body="Second entry.")

    append_entry(e1, log_path)
    append_entry(e2, log_path)

    text = log_path.read_text()
    entries = parse_log(text)
    assert len(entries) == 2
    assert entries[0].id == "20260101-1200-ab12"
    assert entries[1].id == "20260102-0800-cd34"


def test_multiple_appends_preserve_order(tmp_path):
    log_path = tmp_path / "chronicle.log"
    log_path.touch()

    ids = [f"20260101-{i:04d}-abcd" for i in range(5)]
    for eid in ids:
        append_entry(_make_entry(id=eid), log_path)

    entries = parse_log(log_path.read_text())
    assert [e.id for e in entries] == ids
