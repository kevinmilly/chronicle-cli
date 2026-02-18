"""Shared test fixtures."""

from __future__ import annotations

import pytest
from datetime import datetime, date, timezone
from pathlib import Path

from chronicle.models import Entry


@pytest.fixture
def tmp_chronicle(tmp_path: Path) -> Path:
    """Create a temporary chronicle directory."""
    chronicle_dir = tmp_path / ".chronicle"
    chronicle_dir.mkdir()
    log_file = chronicle_dir / "chronicle.log"
    log_file.touch()
    return chronicle_dir


@pytest.fixture
def sample_entry() -> Entry:
    return Entry(
        id="20260101-1200-ab12",
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        entry_type="win",
        tags=["coding", "python"],
        people=["Alice"],
        review_date=None,
        ref=None,
        body="Finished the first module of the project.",
    )


@pytest.fixture
def sample_decision() -> Entry:
    return Entry(
        id="20260115-0900-cd34",
        timestamp=datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc),
        entry_type="decision",
        tags=["career"],
        people=["Bob"],
        review_date=date(2026, 4, 15),
        ref=None,
        body="Decided to switch to the new framework.",
    )


SAMPLE_LOG = """\
@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 win [coding,python] [people:Alice]
Finished the first module of the project.
@end

@entry 20260115-0900-cd34 2026-01-15T09:00:00+00:00 decision [career] [people:Bob] [review:2026-04-15]
Decided to switch to the new framework.
@end
"""
