"""Life story export generator."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from chronicle.models import Entry


def _load_categories(processed_path: Path) -> dict[str, list[str]]:
    """Load AI categories. Returns {entry_id: [categories]}."""
    from chronicle.ai.process import load_processed

    processed = load_processed(processed_path)
    return {
        eid: data.get("categories", [])
        for eid, data in processed.items()
    }


def generate_life_story(
    entries: list[Entry],
    start: date,
    end: date,
    processed_path: Path | None = None,
) -> str:
    """Generate a life story document from entries."""
    lines: list[str] = []
    lines.append("# My Chronicle")
    lines.append("")

    if not entries:
        lines.append("No entries found in the specified range.")
        return "\n".join(lines)

    # Load AI categories if available
    categories: dict[str, list[str]] = {}
    if processed_path:
        categories = _load_categories(processed_path)

    has_categories = any(categories.get(e.id) for e in entries)

    # Helper
    def _by_category(cat: str) -> list[Entry]:
        return [e for e in entries if cat in categories.get(e.id, [])]

    # Timeline by year/month
    lines.append("## Timeline")
    lines.append("")
    by_year_month: dict[tuple[int, int], list[Entry]] = defaultdict(list)
    for e in entries:
        key = (e.timestamp.year, e.timestamp.month)
        by_year_month[key].append(e)

    for (year, month), month_entries in sorted(by_year_month.items()):
        lines.append(f"### {year}-{month:02d}")
        for e in month_entries:
            first_line = e.body.split("\n")[0][:80] if e.body else "(no body)"
            if has_categories and categories.get(e.id):
                cats = ", ".join(categories[e.id])
                lines.append(f"- [{cats}] {first_line}")
            else:
                lines.append(f"- [{e.entry_type}] {first_line}")
        lines.append("")

    # Key people index
    lines.append("## Key People")
    lines.append("")
    people_counter: Counter[str] = Counter()
    for e in entries:
        for p in e.people:
            people_counter[p] += 1
    if people_counter:
        for person, count in people_counter.most_common():
            lines.append(f"- **{person}**: {count} mention(s)")
    else:
        lines.append("No people mentioned.")
    lines.append("")

    # Theme/tag index
    lines.append("## Themes & Tags")
    lines.append("")
    tag_counter: Counter[str] = Counter()
    for e in entries:
        for t in e.tags:
            tag_counter[t] += 1
    if tag_counter:
        for tag, count in tag_counter.most_common():
            lines.append(f"- **{tag}**: {count}")
    else:
        lines.append("No tags found.")
    lines.append("")

    # Highlights section using AI categories or legacy types
    lines.append("## Highlights")
    lines.append("")

    if has_categories:
        wins = _by_category("win")
        if wins:
            lines.append("### Wins")
            for e in wins:
                first_line = e.body.split("\n")[0] if e.body else "(no body)"
                lines.append(f"- {e.timestamp.date()}: {first_line}")
            lines.append("")

        decisions = _by_category("decision_needed")
        if decisions:
            lines.append("### Decisions Needed")
            for e in decisions:
                first_line = e.body.split("\n")[0] if e.body else "(no body)"
                lines.append(f"- {e.timestamp.date()}: {first_line}")
            lines.append("")

        blocks = _by_category("block")
        if blocks:
            lines.append("### Blocks")
            for e in blocks:
                first_line = e.body.split("\n")[0] if e.body else "(no body)"
                lines.append(f"- {e.timestamp.date()}: {first_line}")
            lines.append("")

        lessons = _by_category("lesson_learned")
        if lessons:
            lines.append("### Lessons Learned")
            for e in lessons:
                first_line = e.body.split("\n")[0] if e.body else "(no body)"
                lines.append(f"- {e.timestamp.date()}: {first_line}")
            lines.append("")
    else:
        # Legacy: use entry_type fields
        wins = [e for e in entries if e.entry_type == "win"]
        if wins:
            lines.append("### Wins")
            for e in wins:
                first_line = e.body.split("\n")[0] if e.body else "(no body)"
                lines.append(f"- {e.timestamp.date()}: {first_line}")
            lines.append("")

        decisions = [e for e in entries if e.entry_type == "decision"]
        if decisions:
            lines.append("### Decisions")
            for e in decisions:
                first_line = e.body.split("\n")[0] if e.body else "(no body)"
                lines.append(f"- {e.timestamp.date()}: {first_line}")
            lines.append("")

        blocks = [e for e in entries if e.entry_type == "block"]
        if blocks:
            lines.append("### Recurring Blocks")
            for e in blocks:
                first_line = e.body.split("\n")[0] if e.body else "(no body)"
                lines.append(f"- {e.timestamp.date()}: {first_line}")
            lines.append("")

    # Appendix: entry index table
    lines.append("## Appendix: Entry Index")
    lines.append("")
    lines.append("| ID | Date | Type | Tags |")
    lines.append("|---|---|---|---|")
    for e in entries:
        tags_str = ", ".join(e.tags) if e.tags else ""
        lines.append(
            f"| {e.id} | {e.timestamp.date()} | {e.entry_type} | {tags_str} |"
        )
    lines.append("")

    return "\n".join(lines)
