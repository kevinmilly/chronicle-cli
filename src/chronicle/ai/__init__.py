"""AI integration for Chronicle — OpenAI API helpers."""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error

from chronicle.models import Entry


def get_api_key() -> str:
    """Return the OpenAI API key from config or environment.

    Checks config.toml first, then falls back to OPENAI_API_KEY env var.
    Raises RuntimeError if neither is set.
    """
    from chronicle.config import load_config

    cfg = load_config()
    if cfg.ai_api_key:
        return cfg.ai_api_key

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key found. Set one with 'chronicle add-key' "
            "or set the OPENAI_API_KEY environment variable."
        )
    return api_key


def chat_completion(
    messages: list[dict[str, str]], model: str = "gpt-4o-mini"
) -> str:
    """Call the OpenAI Chat Completions API and return the response text."""
    api_key = get_api_key()

    payload = json.dumps({"model": model, "messages": messages}).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"OpenAI API error ({e.code}): {body}") from e

    return data["choices"][0]["message"]["content"] or ""


def format_entries_as_context(entries: list[Entry]) -> str:
    """Format a list of entries into a text block for LLM context."""
    parts: list[str] = []
    for e in entries:
        header = f"[{e.timestamp.strftime('%Y-%m-%d %H:%M')}] ({e.entry_type})"
        if e.tags:
            header += f" tags: {', '.join(e.tags)}"
        if e.people:
            header += f" people: {', '.join(e.people)}"
        parts.append(f"{header}\n{e.body}")
    return "\n\n---\n\n".join(parts)
