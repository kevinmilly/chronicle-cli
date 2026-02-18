"""AI-powered insight generation from journal entries."""

from __future__ import annotations

from chronicle.ai import chat_completion, format_entries_as_context
from chronicle.models import Entry


SYSTEM_PROMPT = """\
You are a personal journal analyst. The user will provide their journal entries \
and you will analyze them for patterns, themes, mood trends, and actionable \
observations.

Provide your analysis in clear sections:
- **Patterns & Themes**: Recurring topics or behaviors
- **Mood & Energy Trends**: Emotional trajectory over the period
- **Key Wins**: Notable accomplishments or positive moments
- **Blockers & Challenges**: Ongoing struggles or unresolved issues
- **Actionable Observations**: Concrete suggestions based on what you see

Be empathetic, insightful, and concise. Ground your observations in the actual \
entries — don't invent details."""


def generate_insights(entries: list[Entry], model: str = "gpt-4o-mini") -> str:
    """Analyze journal entries and return AI-generated insights."""
    context = format_entries_as_context(entries)

    return chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Here are my journal entries:\n\n{context}\n\n"
                    "Please analyze these entries and provide your insights."
                ),
            },
        ],
        model=model,
    )
