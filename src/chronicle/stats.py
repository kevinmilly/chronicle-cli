"""Stats display — show AI-categorized entries."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from chronicle.ai.process import load_processed
from chronicle.models import Entry


CATEGORY_LABELS = {
    "win": "Wins",
    "decision_needed": "Decisions Needed",
    "block": "Blocks",
    "failure": "Failures/Mistakes",
    "lesson_learned": "Lessons Learned",
}


def generate_stats(
    entries: list[Entry],
    processed_path: Path,
    *,
    category: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> str:
    """Generate categorized stats display from AI-processed data."""
    processed = load_processed(processed_path)

    if not processed:
        return "No processed entries found. Run 'chronicle process' first."

    # Build lookup: entry id -> entry
    entry_map = {e.id: e for e in entries}

    # Filter by date range if specified
    filtered_ids = set()
    for eid, data in processed.items():
        if eid not in entry_map:
            continue
        entry = entry_map[eid]
        entry_date = entry.timestamp.astimezone().date()
        if from_date and entry_date < from_date:
            continue
        if to_date and entry_date > to_date:
            continue
        filtered_ids.add(eid)

    # Group by category
    by_category: dict[str, list[tuple[date, str]]] = {
        cat: [] for cat in CATEGORY_LABELS
    }
    for eid in filtered_ids:
        data = processed[eid]
        entry = entry_map[eid]
        entry_date = entry.timestamp.astimezone().date()
        summary = data.get("summary", entry.body.split("\n")[0][:60])
        for cat in data.get("categories", []):
            if cat in by_category:
                by_category[cat].append((entry_date, summary))

    # Sort each category by date
    for cat in by_category:
        by_category[cat].sort()

    # Build output
    lines: list[str] = ["=== Chronicle Stats ===", ""]

    categories_to_show = (
        [category] if category and category in CATEGORY_LABELS else CATEGORY_LABELS
    )

    for cat in categories_to_show:
        label = CATEGORY_LABELS[cat]
        items = by_category[cat]
        lines.append(f"{label} ({len(items)}):")
        if items:
            for d, summary in items:
                lines.append(f"  {d}  {summary}")
        else:
            lines.append("  (none)")
        lines.append("")

    return "\n".join(lines)
