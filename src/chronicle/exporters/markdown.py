"""Markdown export with YAML front matter."""

from __future__ import annotations

from pathlib import Path

from chronicle.models import Entry


def entry_to_markdown(entry: Entry) -> str:
    """Convert an Entry to Markdown with YAML front matter."""
    lines = ["---"]
    lines.append(f"id: {entry.id}")
    lines.append(f"date: {entry.timestamp.isoformat()}")
    lines.append(f"type: {entry.entry_type}")

    if entry.tags:
        lines.append(f"tags: [{', '.join(entry.tags)}]")
    if entry.people:
        lines.append(f"people: [{', '.join(entry.people)}]")
    if entry.review_date is not None:
        lines.append(f"review_date: {entry.review_date.isoformat()}")
    if entry.ref is not None:
        lines.append(f"ref: {entry.ref}")

    lines.append("---")
    lines.append("")
    if entry.body:
        lines.append(entry.body)
        lines.append("")

    return "\n".join(lines)


def export_all(entries: list[Entry]) -> str:
    """Export all entries as a single concatenated Markdown document."""
    parts = [entry_to_markdown(e) for e in entries]
    return "\n".join(parts)


def export_split(entries: list[Entry], output_dir: Path) -> list[Path]:
    """Export each entry as a separate Markdown file."""
    paths: list[Path] = []
    for entry in entries:
        path = output_dir / f"{entry.id}.md"
        path.write_text(entry_to_markdown(entry), encoding="utf-8")
        paths.append(path)
    return paths
