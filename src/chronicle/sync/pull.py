"""Pull logic — fetch, decrypt, deduplicate, append new entries."""

from __future__ import annotations

from pathlib import Path

from chronicle.parser import parse_file, parse_log
from chronicle.storage import append_entry
from chronicle.sync.backend import SyncBackend
from chronicle.sync.crypto import decrypt_payload


def pull(
    backend: SyncBackend,
    key: bytes,
    log_path: Path,
) -> int:
    """Pull new entries from the remote backend.

    Fetches all encrypted tokens, decrypts each, parses entries,
    deduplicates against local entries, and appends new ones.

    Returns the number of new entries added.
    """
    remote_content = backend.read().strip()
    if not remote_content:
        return 0

    # Each line is one encrypted token
    tokens = [line for line in remote_content.splitlines() if line.strip()]

    # Decrypt all tokens and collect entries
    remote_entries = []
    for token in tokens:
        token = token.strip()
        if not token or token.startswith("#"):
            continue
        plaintext = decrypt_payload(token, key)
        parsed = parse_log(plaintext)
        remote_entries.extend(parsed)

    if not remote_entries:
        return 0

    # Load local entry IDs for deduplication
    local_ids: set[str] = set()
    if log_path.exists() and log_path.stat().st_size > 0:
        local_entries = parse_file(log_path)
        local_ids = {e.id for e in local_entries}

    # Append only new entries
    added = 0
    for entry in remote_entries:
        if entry.id not in local_ids:
            append_entry(entry, log_path)
            local_ids.add(entry.id)
            added += 1

    return added
