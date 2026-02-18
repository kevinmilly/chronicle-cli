"""Weekly brief generator."""

from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

from chronicle.models import Entry


def _load_categories(entries: list[Entry], processed_path: Path) -> dict[str, list[str]]:
    """Load AI categories for entries. Returns {entry_id: [categories]}."""
    from chronicle.ai.process import load_processed

    processed = load_processed(processed_path)
    return {
        eid: data.get("categories", [])
        for eid, data in processed.items()
    }


def generate_weekly_brief(
    entries: list[Entry],
    start: date,
    end: date,
    processed_path: Path | None = None,
) -> str:
    """Generate a weekly brief from entries in the given date range."""
    lines: list[str] = []
    lines.append(f"# Weekly Brief: {start.isoformat()} to {end.isoformat()}")
    lines.append("")

    # Summary count
    lines.append("## Summary")
    if entries:
        lines.append(f"- {len(entries)} entries this week")
    else:
        lines.append("No entries this week.")
    lines.append("")

    # Load AI categories if available
    categories: dict[str, list[str]] = {}
    if processed_path:
        categories = _load_categories(entries, processed_path)

    # Helper to get entries by AI category
    def _by_category(cat: str) -> list[Entry]:
        return [e for e in entries if cat in categories.get(e.id, [])]

    has_categories = any(categories.get(e.id) for e in entries)

    if has_categories:
        # Use AI categories
        wins = _by_category("win")
        lines.append("## Wins")
        if wins:
            for e in wins:
                first_line = e.body.split("\n")[0] if e.body else "(no body)"
                lines.append(f"- {first_line}")
        else:
            lines.append("None this week.")
        lines.append("")

        blocks = _by_category("block")
        lines.append("## Blocks")
        if blocks:
            for e in blocks:
                first_line = e.body.split("\n")[0] if e.body else "(no body)"
                lines.append(f"- {first_line}")
        else:
            lines.append("None this week.")
        lines.append("")

        decisions = _by_category("decision_needed")
        lines.append("## Decisions Needed")
        if decisions:
            for e in decisions:
                first_line = e.body.split("\n")[0] if e.body else "(no body)"
                lines.append(f"- {first_line}")
        else:
            lines.append("None this week.")
        lines.append("")
    else:
        # No AI processing — show all entries
        lines.append("## Entries")
        if entries:
            for e in entries:
                first_line = e.body.split("\n")[0] if e.body else "(no body)"
                lines.append(f"- **[{e.entry_type}]** {first_line}")
        else:
            lines.append("None this week.")
        lines.append("")

    # Most-mentioned people
    people_counter: Counter[str] = Counter()
    for e in entries:
        for p in e.people:
            people_counter[p] += 1
    lines.append("## People")
    if people_counter:
        for person, count in people_counter.most_common(10):
            lines.append(f"- {person}: {count} mention(s)")
    else:
        lines.append("None this week.")
    lines.append("")

    # Top tags
    tag_counter: Counter[str] = Counter()
    for e in entries:
        for t in e.tags:
            tag_counter[t] += 1
    lines.append("## Tags")
    if tag_counter:
        for tag, count in tag_counter.most_common(10):
            lines.append(f"- {tag}: {count}")
    else:
        lines.append("None this week.")
    lines.append("")

    return "\n".join(lines)
