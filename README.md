# Chronicle CLI

A command-line journaling and self-analysis tool. Write freestyle entries, then let AI categorize them and fix spelling/grammar. Everything is stored in a single append-only text file.

## Installation

```bash
pip install -e ".[dev]"
```

Requires Python 3.11+.

## Quick Start

```bash
# 1. Initialize chronicle (~/.chronicle/)
chronicle init

# 2. Add your API key for AI features
chronicle add-key

# 3. Start journaling
chronicle add
```

## Commands

### Journaling

```bash
# Add an entry (prompts "What's on your mind?")
chronicle add

# Open your text editor for longer entries
chronicle add --editor

# Tag entries and mention people
chronicle add --tags "work,python" --people "Alice,Bob"
```

### AI Features

AI features require an OpenAI API key and `enabled = true` in your config.

```bash
# Save your OpenAI API key
chronicle add-key

# Process entries — AI categorizes and fixes spelling/grammar
chronicle process

# View categorized stats
chronicle stats
chronicle stats --category win
chronicle stats --from 2026-01-01 --to 2026-01-31

# Get AI insights about your journal
chronicle ai
chronicle ai --from 2026-01-01

# Ask a freeform question
chronicle ai freestyle "what are my biggest wins this month?"
```

**How `chronicle process` works:**

1. Scans for entries that haven't been processed yet
2. Sends them to the AI in batches
3. Each entry gets categorized into: `win`, `decision_needed`, `block`, `failure`, `lesson_learned` (or none)
4. Spelling and grammar are corrected in-place (a `.bak` backup is created)
5. Results are stored in `~/.chronicle/ai_processed.json`

Run it again any time — it only processes new entries.

### Weekly Brief

```bash
chronicle week
chronicle week --from 2026-01-01 --to 2026-01-07
```

Generates a weekly summary. If entries have been AI-processed, the brief groups them by category (Wins, Blocks, Decisions Needed). Otherwise it lists all entries.

### Exports

```bash
# Markdown with YAML front matter
chronicle export md --all
chronicle export md --split --all    # One file per entry
chronicle export md --from 2026-01-01 --to 2026-06-30

# Life story document
chronicle export story
chronicle export story --from 2026-01-01 --to 2026-12-31
```

### Cloud Sync

Sync entries between devices using encrypted GitHub Gist storage. You can also capture entries from your phone via a Telegram bot.

**First-time setup:**

```bash
chronicle sync setup
```

This will prompt you for:
1. A **GitHub Personal Access Token** — create one at [github.com/settings/tokens](https://github.com/settings/tokens) with the `gist` scope
2. A **sync passphrase** — used to encrypt/decrypt your entries (never stored on disk)

The wizard creates a private Gist and saves the config to `~/.chronicle/config.toml`.

**Daily use:**

```bash
# Push all local entries to the cloud (full encrypted backup)
chronicle push

# Pull new entries from the cloud (e.g. entries added from Telegram)
chronicle pull

# Check sync status
chronicle sync status
```

`push` overwrites the remote with all local entries (Gist revision history preserves old versions). `pull` fetches remote entries, decrypts them, and appends only entries that don't already exist locally.

The passphrase is prompted each time, or you can set `CHRONICLE_SYNC_PASSPHRASE` as an environment variable.

**Telegram bot (optional):**

Want to journal from your phone? See [`telegram_bot/README.md`](telegram_bot/README.md) for setup instructions. The bot encrypts messages with the same passphrase and appends them to your Gist — then `chronicle pull` brings them into your local log.

### Utilities

```bash
# Validate your log file for syntax errors
chronicle validate

# Show the usage guide in your terminal
chronicle guide
```

## Log Format

Entries are stored in `~/.chronicle/chronicle.log`:

```
@entry 20260101-1200-ab12 2026-01-01T12:00:00+00:00 entry [coding,python] [people:Alice]
Finished the first module of the project.
@end

@entry 20260115-0900-cd34 2026-01-15T09:00:00+00:00 entry [career] [people:Bob]
Decided to switch to the new framework.
Considered staying with the old one, but the new one has better support.
@end
```

Header fields (in brackets, any order):
- `[tags]` — comma-separated tags
- `[people:names]` — comma-separated people
- `[review:YYYY-MM-DD]` — review date
- `[ref:entry-id]` — reference to another entry

Old entries with legacy types (`win`, `block`, `decision`, etc.) still parse fine. New entries all use type `entry` — AI handles categorization after the fact.

## Configuration

Config lives at `~/.chronicle/config.toml`:

```toml
[chronicle]
# editor = "code --wait"
# timezone = "America/New_York"

[ai]
enabled = true
api_key = "sk-..."       # set via: chronicle add-key
# provider = "openai"
# model = "gpt-4o-mini"

[sync]
enabled = true            # set by: chronicle sync setup
backend = "gist"
gist_id = "abc123..."
github_token = "ghp_..."
encryption_salt = "0a1b..."  # hex-encoded, generated during setup
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
