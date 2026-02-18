"""Tests for chronicle.parser.validate."""

from chronicle.parser import validate


def test_valid_file():
    text = """\
@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 win [coding]
Great day.
@end
"""
    assert validate(text) == []


def test_missing_end():
    text = """\
@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 win
Body text.
"""
    errors = validate(text)
    assert len(errors) == 1
    assert "Unclosed" in errors[0]


def test_duplicate_ids():
    text = """\
@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 win
First.
@end

@entry 20260101-1200-ab12 2026-01-01T13:00:00+00:00 block
Duplicate ID.
@end
"""
    errors = validate(text)
    assert len(errors) == 1
    assert "Duplicate ID" in errors[0]


def test_malformed_timestamp():
    text = """\
@entry 20260101-1200-ab12 not-a-timestamp win
Body.
@end
"""
    errors = validate(text)
    assert len(errors) >= 1
    assert any("timestamp" in e.lower() or "invalid" in e.lower() for e in errors)


def test_malformed_header():
    text = """\
@entry 20260101-1200-ab12
Body.
@end
"""
    errors = validate(text)
    assert len(errors) >= 1


def test_end_without_entry():
    text = """\
@end
"""
    errors = validate(text)
    assert len(errors) == 1
    assert "@end without" in errors[0]


def test_entry_without_end_then_new_entry():
    text = """\
@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 win
First.
@entry 20260102-0800-cd34 2026-01-02T08:00:00+00:00 block
Second.
@end
"""
    errors = validate(text)
    assert len(errors) >= 1
    assert any("@entry without closing @end" in e for e in errors)
