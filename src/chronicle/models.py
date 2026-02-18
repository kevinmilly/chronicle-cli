"""Data model for chronicle entries."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import date, datetime, timezone


@dataclass
class Entry:
    id: str
    timestamp: datetime
    entry_type: str
    tags: list[str] = field(default_factory=list)
    people: list[str] = field(default_factory=list)
    review_date: date | None = None
    ref: str | None = None
    body: str = ""


def generate_id(ts: datetime | None = None) -> str:
    """Generate an entry ID in the format YYYYMMDD-HHMM-<4hex>."""
    if ts is None:
        ts = datetime.now(timezone.utc)
    hex_suffix = secrets.token_hex(2)
    return f"{ts.strftime('%Y%m%d-%H%M')}-{hex_suffix}"
