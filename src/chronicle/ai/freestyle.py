"""AI-powered freestyle Q&A using journal entries as context."""

from __future__ import annotations

from chronicle.ai import chat_completion, format_entries_as_context
from chronicle.models import Entry


SYSTEM_PROMPT = """\
You are a helpful assistant with access to the user's personal journal entries. \
Use the journal entries provided as context to answer the user's question. \
Reference specific entries when relevant. If the journal entries don't contain \
enough information to fully answer, say so honestly.

Be empathetic, thoughtful, and concise."""


def freestyle_query(
    entries: list[Entry], question: str, model: str = "gpt-4o-mini"
) -> str:
    """Answer a freeform question using journal entries as context."""
    context = format_entries_as_context(entries)

    return chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Here are my journal entries:\n\n{context}\n\n"
                    f"My question: {question}"
                ),
            },
        ],
        model=model,
    )
