"""Entry serialization and file storage."""

from __future__ import annotations

from pathlib import Path

from chronicle.models import Entry


def format_entry(entry: Entry) -> str:
    """Serialize an Entry to @entry/@end format."""
    parts = [f"@entry {entry.id} {entry.timestamp.isoformat()} {entry.entry_type}"]

    if entry.tags:
        parts.append(f"[{','.join(entry.tags)}]")
    if entry.people:
        parts.append(f"[people:{','.join(entry.people)}]")
    if entry.review_date is not None:
        parts.append(f"[review:{entry.review_date.isoformat()}]")
    if entry.ref is not None:
        parts.append(f"[ref:{entry.ref}]")

    header = " ".join(parts)
    lines = [header]
    if entry.body:
        lines.append(entry.body)
    lines.append("@end")
    return "\n".join(lines)


def append_entry(entry: Entry, log_path: Path) -> None:
    """Append a formatted entry to the log file."""
    formatted = format_entry(entry)
    with open(log_path, "a", encoding="utf-8") as f:
        # Add blank line separator if file is not empty
        if log_path.stat().st_size > 0:
            f.write("\n\n")
        f.write(formatted)
        f.write("\n")


def rewrite_log(entries: list[Entry], log_path: Path) -> None:
    """Rewrite the entire log file with the given entries.

    Creates a .bak backup before overwriting.
    """
    import shutil

    backup_path = log_path.with_suffix(".log.bak")
    shutil.copy2(log_path, backup_path)

    lines: list[str] = []
    for entry in entries:
        lines.append(format_entry(entry))
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(lines))
        if lines:
            f.write("\n")
