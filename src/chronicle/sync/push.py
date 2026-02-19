"""Push logic — encrypt all local entries and overwrite remote."""

from __future__ import annotations

from pathlib import Path

from chronicle.parser import parse_file
from chronicle.storage import format_entry
from chronicle.sync.backend import SyncBackend
from chronicle.sync.crypto import encrypt_payload


def push(
    backend: SyncBackend,
    key: bytes,
    log_path: Path,
) -> int:
    """Push all local entries to the remote backend (full backup).

    Reads all local entries, encrypts each one, and overwrites the
    remote content. Gist revision history preserves previous versions.

    Returns the number of entries pushed.
    """
    if not log_path.exists() or log_path.stat().st_size == 0:
        return 0

    entries = parse_file(log_path)
    if not entries:
        return 0

    # Encrypt each entry as one token per line
    tokens = []
    for entry in entries:
        plaintext = format_entry(entry)
        token = encrypt_payload(plaintext, key)
        tokens.append(token)

    content = "\n".join(tokens) + "\n"
    backend.write(content)
    return len(entries)
