"""AI processing — categorize entries and fix spelling/grammar."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from chronicle.ai import chat_completion
from chronicle.models import Entry

CATEGORIES = [
    "win",
    "decision_needed",
    "block",
    "failure",
    "lesson_learned",
]

BATCH_SIZE = 20

SYSTEM_PROMPT = """\
You are a journal entry processor. For each entry provided, you must:
1. Categorize it into zero or more of these categories: win, decision_needed, block, failure, lesson_learned
2. Write a short one-line summary (max 80 chars)
3. Fix any spelling and grammar mistakes in the body text. Keep the meaning and tone identical.

Respond with a JSON array (no markdown fences). Each element must have:
- "id": the entry ID (string)
- "categories": list of category strings (may be empty)
- "summary": one-line summary string
- "corrected_body": the body text with spelling/grammar fixed

Example response:
[{"id": "20260101-1200-ab12", "categories": ["win"], "summary": "Completed project milestone", "corrected_body": "Finished the first module of the project."}]
"""


@dataclass
class ProcessedResult:
    id: str
    categories: list[str] = field(default_factory=list)
    summary: str = ""
    corrected_body: str = ""


def load_processed(path: Path) -> dict:
    """Load ai_processed.json, returning empty dict if not found."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_processed(data: dict, path: Path) -> None:
    """Save ai_processed.json."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _build_batch_prompt(entries: list[Entry]) -> str:
    """Build the user prompt for a batch of entries."""
    parts: list[str] = []
    for e in entries:
        parts.append(f"--- Entry ID: {e.id} ---\n{e.body}")
    return "\n\n".join(parts)


def process_entries(
    entries: list[Entry], model: str = "gpt-4o-mini"
) -> list[ProcessedResult]:
    """Send entries to the LLM in batches, get back categories + corrected body."""
    results: list[ProcessedResult] = []

    for i in range(0, len(entries), BATCH_SIZE):
        batch = entries[i : i + BATCH_SIZE]
        user_prompt = _build_batch_prompt(batch)

        response = chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
        )

        # Strip markdown fences if present
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        parsed = json.loads(text)
        for item in parsed:
            results.append(
                ProcessedResult(
                    id=item["id"],
                    categories=item.get("categories", []),
                    summary=item.get("summary", ""),
                    corrected_body=item.get("corrected_body", ""),
                )
            )

    return results
