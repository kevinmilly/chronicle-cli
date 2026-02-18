"""Tests for chronicle.parser."""

from datetime import datetime, date, timezone

from chronicle.parser import parse_header, parse_log


def test_basic_parse():
    text = """\
@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 win [coding,python]
Finished the first module.
@end
"""
    entries = parse_log(text)
    assert len(entries) == 1
    e = entries[0]
    assert e.id == "20260101-1200-ab12"
    assert e.entry_type == "win"
    assert e.tags == ["coding", "python"]
    assert e.body == "Finished the first module."


def test_multi_entry():
    text = """\
@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 win
First entry body.
@end

@entry 20260102-0800-cd34 2026-01-02T08:00:00+00:00 block
Second entry body.
@end
"""
    entries = parse_log(text)
    assert len(entries) == 2
    assert entries[0].id == "20260101-1200-ab12"
    assert entries[1].id == "20260102-0800-cd34"


def test_all_header_fields():
    text = """\
@entry 20260115-0900-cd34 2026-01-15T09:00:00+00:00 decision [career] [people:Alice,Bob] [review:2026-04-15] [ref:20260101-1200-ab12]
Made a big decision.
@end
"""
    entries = parse_log(text)
    e = entries[0]
    assert e.entry_type == "decision"
    assert e.tags == ["career"]
    assert e.people == ["Alice", "Bob"]
    assert e.review_date == date(2026, 4, 15)
    assert e.ref == "20260101-1200-ab12"


def test_minimal_header():
    text = """\
@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 freestyle
Just a thought.
@end
"""
    entries = parse_log(text)
    e = entries[0]
    assert e.tags == []
    assert e.people == []
    assert e.review_date is None
    assert e.ref is None


def test_body_preservation():
    text = """\
@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 freestyle
Line one.

Line three after blank.

  Indented line.
@end
"""
    entries = parse_log(text)
    assert "Line one.\n\nLine three after blank.\n\n  Indented line." == entries[0].body


def test_empty_body():
    text = """\
@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 win
@end
"""
    entries = parse_log(text)
    assert entries[0].body == ""


def test_empty_file():
    entries = parse_log("")
    assert entries == []


def test_body_leading_trailing_blank_lines_stripped():
    text = """\
@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 win

Hello world.

@end
"""
    entries = parse_log(text)
    assert entries[0].body == "Hello world."
