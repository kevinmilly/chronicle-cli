"""Log file parsing and validation."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from chronicle.models import Entry


class ParseError(Exception):
    def __init__(self, message: str, line_number: int | None = None):
        self.line_number = line_number
        super().__init__(message)


def _parse_bracket_fields(
    tokens: list[str],
) -> tuple[list[str], list[str], date | None, str | None]:
    """Parse bracket fields from header tokens.

    Bracket fields: [tags] [people:...] [review:...] [ref:...]
    No prefix = tags; known prefix = people/review/ref.
    """
    tags: list[str] = []
    people: list[str] = []
    review_date: date | None = None
    ref: str | None = None

    for token in tokens:
        if not (token.startswith("[") and token.endswith("]")):
            continue
        inner = token[1:-1]
        if inner.startswith("people:"):
            people = [p.strip() for p in inner[7:].split(",") if p.strip()]
        elif inner.startswith("review:"):
            review_date = date.fromisoformat(inner[7:].strip())
        elif inner.startswith("ref:"):
            ref = inner[4:].strip()
        else:
            tags = [t.strip() for t in inner.split(",") if t.strip()]

    return tags, people, review_date, ref


def parse_header(line: str, line_number: int = 0) -> Entry:
    """Parse an @entry header line into an Entry (body empty)."""
    if not line.startswith("@entry "):
        raise ParseError(f"Line does not start with '@entry '", line_number)

    rest = line[7:].strip()

    # Extract all bracket fields first
    bracket_pattern = re.compile(r"\[[^\]]*\]")
    brackets = bracket_pattern.findall(rest)
    non_bracket = bracket_pattern.sub("", rest).split()

    if len(non_bracket) < 3:
        raise ParseError(
            f"Header must have at least id, timestamp, and type", line_number
        )

    entry_id = non_bracket[0]
    timestamp_str = non_bracket[1]
    entry_type = non_bracket[2]

    try:
        timestamp = datetime.fromisoformat(timestamp_str)
    except ValueError as e:
        raise ParseError(f"Invalid timestamp '{timestamp_str}': {e}", line_number)

    tags, people, review_date, ref = _parse_bracket_fields(brackets)

    return Entry(
        id=entry_id,
        timestamp=timestamp,
        entry_type=entry_type,
        tags=tags,
        people=people,
        review_date=review_date,
        ref=ref,
        body="",
    )


def parse_log(text: str) -> list[Entry]:
    """Parse a full chronicle log text into a list of Entry objects."""
    entries: list[Entry] = []
    current_entry: Entry | None = None
    body_lines: list[str] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.rstrip("\n")

        if stripped.startswith("@entry "):
            if current_entry is not None:
                raise ParseError(
                    f"Missing @end before new @entry", line_number
                )
            current_entry = parse_header(stripped, line_number)
            body_lines = []

        elif stripped == "@end":
            if current_entry is None:
                raise ParseError(f"@end without matching @entry", line_number)
            body = "\n".join(body_lines)
            # Strip leading/trailing blank lines, preserve internal whitespace
            body = body.strip("\n")
            current_entry.body = body
            entries.append(current_entry)
            current_entry = None
            body_lines = []

        elif current_entry is not None:
            body_lines.append(stripped)

    if current_entry is not None:
        raise ParseError("Unclosed @entry at end of file")

    return entries


def parse_file(path: Path) -> list[Entry]:
    """Parse a chronicle log file."""
    text = path.read_text(encoding="utf-8")
    return parse_log(text)


def validate(text: str) -> list[str]:
    """Validate chronicle log text, returning a list of error strings."""
    errors: list[str] = []
    lines = text.splitlines()
    seen_ids: set[str] = set()
    in_entry = False
    entry_start_line = 0

    for line_number, line in enumerate(lines, start=1):
        stripped = line.rstrip("\n")

        if stripped.startswith("@entry "):
            if in_entry:
                errors.append(
                    f"Line {line_number}: @entry without closing @end "
                    f"(opened at line {entry_start_line})"
                )
            in_entry = True
            entry_start_line = line_number

            # Try to parse header
            try:
                entry = parse_header(stripped, line_number)
            except ParseError as e:
                errors.append(f"Line {line_number}: {e}")
                continue

            if entry.id in seen_ids:
                errors.append(f"Line {line_number}: Duplicate ID '{entry.id}'")
            seen_ids.add(entry.id)

            # Validate timestamp
            try:
                datetime.fromisoformat(stripped.split()[2])
            except (ValueError, IndexError):
                errors.append(
                    f"Line {line_number}: Invalid timestamp in header"
                )

            # Validate review date if present
            if entry.review_date is not None:
                try:
                    # Already parsed successfully in parse_header
                    pass
                except Exception:
                    errors.append(
                        f"Line {line_number}: Invalid review date"
                    )

        elif stripped == "@end":
            if not in_entry:
                errors.append(f"Line {line_number}: @end without matching @entry")
            in_entry = False

    if in_entry:
        errors.append(
            f"Line {entry_start_line}: Unclosed @entry at end of file"
        )

    return errors
