"""Chronicle CLI — main Typer application."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Annotated, Optional

import typer

from chronicle.config import ChronicleConfig, default_config_toml, load_config
from chronicle.models import Entry, generate_id
from chronicle.parser import parse_file, validate as validate_log
from chronicle.storage import append_entry

app = typer.Typer(
    name="chronicle",
    help="A CLI journaling and self-analysis tool.",
    no_args_is_help=True,
)

export_app = typer.Typer(
    name="export",
    help="Export chronicle entries.",
    no_args_is_help=True,
)
app.add_typer(export_app, name="export")

ai_app = typer.Typer(
    name="ai",
    help="AI-powered journal analysis.",
    invoke_without_command=True,
)
app.add_typer(ai_app, name="ai")

sync_app = typer.Typer(
    name="sync",
    help="Cloud sync (push/pull encrypted entries).",
    no_args_is_help=True,
)
app.add_typer(sync_app, name="sync")

telegram_app = typer.Typer(
    name="telegram",
    help="Telegram bot configuration.",
    no_args_is_help=True,
)
app.add_typer(telegram_app, name="telegram")


ConfigDir = Annotated[
    Optional[Path],
    typer.Option(
        "--config-dir",
        hidden=True,
        help="Override chronicle config directory (for testing).",
    ),
]


def _load_config(config_dir: Path | None) -> ChronicleConfig:
    return load_config(config_dir)


# ── init ────────────────────────────────────────────────────────────────

@app.command()
def init(config_dir: ConfigDir = None) -> None:
    """Initialize chronicle directory and config."""
    cfg = _load_config(config_dir)
    cfg.chronicle_dir.mkdir(parents=True, exist_ok=True)
    cfg.log_file.touch(exist_ok=True)

    toml_path = cfg.chronicle_dir / "config.toml"
    if not toml_path.exists():
        toml_path.write_text(default_config_toml(), encoding="utf-8")

    typer.echo(f"Chronicle initialized at {cfg.chronicle_dir}")


# ── add ─────────────────────────────────────────────────────────────────

@app.command()
def add(
    config_dir: ConfigDir = None,
    editor: Annotated[
        bool, typer.Option("--editor", "-e", help="Open text editor for longer entries.")
    ] = False,
    tags: Annotated[
        Optional[str], typer.Option("--tags", help="Comma-separated tags.")
    ] = None,
    people: Annotated[
        Optional[str], typer.Option("--people", help="Comma-separated people.")
    ] = None,
) -> None:
    """Add a new chronicle entry."""
    cfg = _load_config(config_dir)
    if not cfg.log_file.exists():
        typer.echo("Chronicle not initialized. Run 'chronicle init' first.", err=True)
        raise typer.Exit(code=1)

    now = datetime.now(timezone.utc)
    entry_id = generate_id(now)

    # Get body text
    if editor:
        body = typer.edit("") or ""
        body = body.strip()
    else:
        body = typer.prompt("What's on your mind?")

    # Parse optional fields
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    people_list = (
        [p.strip() for p in people.split(",") if p.strip()] if people else []
    )

    entry = Entry(
        id=entry_id,
        timestamp=now,
        entry_type="entry",
        tags=tag_list,
        people=people_list,
        review_date=None,
        ref=None,
        body=body,
    )

    append_entry(entry, cfg.log_file)
    typer.echo(f"Entry {entry_id} added.")


# ── add-key ─────────────────────────────────────────────────────────────

@app.command(name="add-key")
def add_key(config_dir: ConfigDir = None) -> None:
    """Save your OpenAI API key to the chronicle config."""
    from chronicle.config import save_api_key

    api_key = typer.prompt("Paste your OpenAI API key", hide_input=True)
    api_key = api_key.strip()
    if not api_key:
        typer.echo("No key provided.", err=True)
        raise typer.Exit(code=1)

    toml_path = save_api_key(api_key, config_dir)
    typer.echo(f"API key saved to {toml_path}")

    # Also enable AI if it isn't already
    cfg = _load_config(config_dir)
    if not cfg.ai_enabled:
        typer.echo(
            "Tip: AI features are currently disabled. "
            "Set 'enabled = true' under [ai] in your config.toml to use them."
        )


# ── guide ───────────────────────────────────────────────────────────────

GUIDE_TEXT = """\
Chronicle CLI — Quick Guide
============================

GETTING STARTED
  chronicle init              Set up ~/.chronicle/ directory
  chronicle add-key           Save your OpenAI API key

ADDING ENTRIES
  chronicle add               Prompt: "What's on your mind?"
  chronicle add --editor      Open your text editor for longer entries
  chronicle add --tags work,python --people Alice
                              Attach tags and people to an entry

AI FEATURES  (requires API key + enabled = true in config)
  chronicle add-key           Save your OpenAI API key
  chronicle process           Categorize entries & fix spelling/grammar
  chronicle stats             View entries grouped by category
  chronicle stats --category win
                              Filter to a single category
  chronicle ai                Get AI-generated insights
  chronicle ai freestyle "question"
                              Ask a freeform question about your journal

  Categories assigned by AI:
    win, decision_needed, block, failure, lesson_learned

WEEKLY BRIEF
  chronicle week              Brief for the last 7 days
  chronicle week --from 2026-01-01 --to 2026-01-07

EXPORTS
  chronicle export md --all   All entries as Markdown
  chronicle export md --split --all
                              One Markdown file per entry
  chronicle export story      Life story document

UTILITIES
  chronicle validate          Check log file for syntax errors
  chronicle guide             Show this guide

LOG FORMAT
  Entries live in ~/.chronicle/chronicle.log:

    @entry <id> <timestamp> entry [tags] [people:names]
    Your entry text here.
    @end

CONFIGURATION
  Config file: ~/.chronicle/config.toml

    [chronicle]
    # editor = "code --wait"
    # timezone = "America/New_York"

    [ai]
    enabled = true
    api_key = "sk-..."       # set via: chronicle add-key
    # model = "gpt-4o-mini"
"""


@app.command()
def guide() -> None:
    """Show a usage guide for Chronicle CLI."""
    typer.echo(GUIDE_TEXT)


# ── validate ────────────────────────────────────────────────────────────

@app.command(name="validate")
def validate_cmd(config_dir: ConfigDir = None) -> None:
    """Validate the chronicle log file."""
    cfg = _load_config(config_dir)
    if not cfg.log_file.exists():
        typer.echo("No chronicle log found.", err=True)
        raise typer.Exit(code=1)

    text = cfg.log_file.read_text(encoding="utf-8")
    errors = validate_log(text)

    if errors:
        typer.echo(f"Found {len(errors)} error(s):")
        for e in errors:
            typer.echo(f"  - {e}")
        raise typer.Exit(code=1)
    else:
        typer.echo("Chronicle log is valid.")


# ── week ────────────────────────────────────────────────────────────────

@app.command()
def week(
    config_dir: ConfigDir = None,
    start: Annotated[
        Optional[str],
        typer.Option("--from", help="Start date (YYYY-MM-DD). Default: 7 days ago."),
    ] = None,
    end: Annotated[
        Optional[str],
        typer.Option("--to", help="End date (YYYY-MM-DD). Default: today."),
    ] = None,
) -> None:
    """Generate a weekly brief."""
    from chronicle.exporters.weekly import generate_weekly_brief

    cfg = _load_config(config_dir)
    if not cfg.log_file.exists():
        typer.echo("No chronicle log found.", err=True)
        raise typer.Exit(code=1)

    today = date.today()
    end_date = date.fromisoformat(end) if end else today
    start_date = (
        date.fromisoformat(start)
        if start
        else date.fromordinal(end_date.toordinal() - 6)
    )

    entries = parse_file(cfg.log_file)
    filtered = [
        e
        for e in entries
        if start_date <= e.timestamp.astimezone().date() <= end_date
    ]

    brief = generate_weekly_brief(filtered, start_date, end_date, cfg.processed_file)

    # Write to exports dir
    exports_dir = cfg.chronicle_dir / "exports" / "weekly"
    exports_dir.mkdir(parents=True, exist_ok=True)
    iso_year, iso_week, _ = end_date.isocalendar()
    out_path = exports_dir / f"weekly-{iso_year}-{iso_week:02d}.md"
    out_path.write_text(brief, encoding="utf-8")
    typer.echo(brief)
    typer.echo(f"\nSaved to {out_path}")


# ── process ─────────────────────────────────────────────────────────────

@app.command()
def process(config_dir: ConfigDir = None) -> None:
    """Run AI processing on unprocessed entries (categorize + fix spelling)."""
    from chronicle.ai.process import (
        load_processed,
        save_processed,
        process_entries,
    )
    from chronicle.storage import rewrite_log

    cfg = _load_config(config_dir)
    if not cfg.log_file.exists():
        typer.echo("No chronicle log found.", err=True)
        raise typer.Exit(code=1)

    if not cfg.ai_enabled:
        typer.echo(
            "AI features are disabled. Enable them in your config.toml:\n"
            "  [ai]\n  enabled = true",
            err=True,
        )
        raise typer.Exit(code=1)

    entries = parse_file(cfg.log_file)
    processed = load_processed(cfg.processed_file)

    # Find unprocessed entries
    unprocessed = [e for e in entries if e.id not in processed]

    if not unprocessed:
        typer.echo("No new entries to process.")
        return

    typer.echo(f"Processing {len(unprocessed)} new entries...")

    results = process_entries(unprocessed, model=cfg.ai_model)

    # Build lookup for corrections
    corrections = {r.id: r for r in results}

    # Update processed data and apply corrections
    category_counts: Counter[str] = Counter()
    corrected_count = 0

    for result in results:
        processed[result.id] = {
            "categories": result.categories,
            "summary": result.summary,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        for cat in result.categories:
            category_counts[cat] += 1

    # Apply spelling corrections to entries
    changed = False
    for entry in entries:
        if entry.id in corrections:
            new_body = corrections[entry.id].corrected_body
            if new_body and new_body != entry.body:
                entry.body = new_body
                corrected_count += 1
                changed = True

    if changed:
        rewrite_log(entries, cfg.log_file)

    save_processed(processed, cfg.processed_file)

    # Summary
    parts: list[str] = []
    if category_counts:
        cat_parts = [f"{count} {cat}" for cat, count in category_counts.most_common()]
        parts.append(f"Categorized: {', '.join(cat_parts)}.")
    if corrected_count:
        parts.append(f"Corrected {corrected_count} entries.")
    typer.echo(" ".join(parts) if parts else "Processing complete.")


# ── stats ───────────────────────────────────────────────────────────────

@app.command()
def stats(
    config_dir: ConfigDir = None,
    category: Annotated[
        Optional[str],
        typer.Option("--category", help="Filter by category (win, block, etc.)"),
    ] = None,
    from_date: Annotated[
        Optional[str],
        typer.Option("--from", help="Start date (YYYY-MM-DD)."),
    ] = None,
    to_date: Annotated[
        Optional[str],
        typer.Option("--to", help="End date (YYYY-MM-DD)."),
    ] = None,
) -> None:
    """Show stats from AI-categorized entries."""
    from chronicle.stats import generate_stats

    cfg = _load_config(config_dir)
    if not cfg.log_file.exists():
        typer.echo("No chronicle log found.", err=True)
        raise typer.Exit(code=1)

    entries = parse_file(cfg.log_file)

    start = date.fromisoformat(from_date) if from_date else None
    end = date.fromisoformat(to_date) if to_date else None

    output = generate_stats(
        entries, cfg.processed_file, category=category, from_date=start, to_date=end
    )
    typer.echo(output)


# ── export md ───────────────────────────────────────────────────────────

@export_app.command(name="md")
def export_md(
    config_dir: ConfigDir = None,
    all_entries: Annotated[
        bool, typer.Option("--all", help="Export all entries.")
    ] = False,
    split: Annotated[
        bool, typer.Option("--split", help="One file per entry.")
    ] = False,
    from_date: Annotated[
        Optional[str], typer.Option("--from", help="Start date (YYYY-MM-DD).")
    ] = None,
    to_date: Annotated[
        Optional[str], typer.Option("--to", help="End date (YYYY-MM-DD).")
    ] = None,
) -> None:
    """Export entries as Markdown with YAML front matter."""
    from chronicle.exporters.markdown import entry_to_markdown, export_all, export_split

    cfg = _load_config(config_dir)
    if not cfg.log_file.exists():
        typer.echo("No chronicle log found.", err=True)
        raise typer.Exit(code=1)

    entries = parse_file(cfg.log_file)

    if not all_entries:
        start = date.fromisoformat(from_date) if from_date else date.min
        end = date.fromisoformat(to_date) if to_date else date.max
        entries = [e for e in entries if start <= e.timestamp.date() <= end]

    if not entries:
        typer.echo("No entries to export.")
        return

    if split:
        out_dir = cfg.chronicle_dir / "exports" / "md"
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = export_split(entries, out_dir)
        typer.echo(f"Exported {len(paths)} files to {out_dir}")
    else:
        result = export_all(entries)
        typer.echo(result)


# ── export story ────────────────────────────────────────────────────────

@export_app.command(name="story")
def export_story(
    config_dir: ConfigDir = None,
    from_date: Annotated[
        Optional[str], typer.Option("--from", help="Start date (YYYY-MM-DD).")
    ] = None,
    to_date: Annotated[
        Optional[str], typer.Option("--to", help="End date (YYYY-MM-DD).")
    ] = None,
) -> None:
    """Generate a life story export."""
    from chronicle.exporters.story import generate_life_story

    cfg = _load_config(config_dir)
    if not cfg.log_file.exists():
        typer.echo("No chronicle log found.", err=True)
        raise typer.Exit(code=1)

    entries = parse_file(cfg.log_file)

    start = date.fromisoformat(from_date) if from_date else date.min
    end = date.fromisoformat(to_date) if to_date else date.max
    entries = [e for e in entries if start <= e.timestamp.date() <= end]

    story = generate_life_story(entries, start, end, cfg.processed_file)
    typer.echo(story)


# ── ai ─────────────────────────────────────────────────────────────────

def _load_entries_for_ai(
    cfg: ChronicleConfig,
    start: str | None,
    end: str | None,
) -> list[Entry]:
    """Load and optionally filter entries for AI commands."""
    if not cfg.log_file.exists():
        typer.echo("No chronicle log found.", err=True)
        raise typer.Exit(code=1)

    if not cfg.ai_enabled:
        typer.echo(
            "AI features are disabled. Enable them in your config.toml:\n"
            "  [ai]\n  enabled = true",
            err=True,
        )
        raise typer.Exit(code=1)

    entries = parse_file(cfg.log_file)

    start_date = date.fromisoformat(start) if start else date.min
    end_date = date.fromisoformat(end) if end else date.max
    entries = [
        e
        for e in entries
        if start_date <= e.timestamp.astimezone().date() <= end_date
    ]

    if not entries:
        typer.echo("No entries found for the given date range.")
        raise typer.Exit(code=1)

    return entries


@ai_app.callback(invoke_without_command=True)
def ai_default(
    ctx: typer.Context,
    config_dir: ConfigDir = None,
    start: Annotated[
        Optional[str],
        typer.Option("--from", help="Start date (YYYY-MM-DD)."),
    ] = None,
    end: Annotated[
        Optional[str],
        typer.Option("--to", help="End date (YYYY-MM-DD)."),
    ] = None,
) -> None:
    """Generate AI insights from your journal entries (default)."""
    if ctx.invoked_subcommand is not None:
        return

    from chronicle.ai.insights import generate_insights

    cfg = _load_config(config_dir)
    entries = _load_entries_for_ai(cfg, start, end)

    typer.echo("Analyzing your journal entries...\n")
    result = generate_insights(entries, model=cfg.ai_model)
    typer.echo(result)


@ai_app.command(name="freestyle")
def ai_freestyle(
    question: Annotated[str, typer.Argument(help="Your question about your journal.")],
    config_dir: ConfigDir = None,
    start: Annotated[
        Optional[str],
        typer.Option("--from", help="Start date (YYYY-MM-DD)."),
    ] = None,
    end: Annotated[
        Optional[str],
        typer.Option("--to", help="End date (YYYY-MM-DD)."),
    ] = None,
) -> None:
    """Ask a freeform question about your journal entries."""
    from chronicle.ai.freestyle import freestyle_query

    cfg = _load_config(config_dir)
    entries = _load_entries_for_ai(cfg, start, end)

    typer.echo("Thinking...\n")
    result = freestyle_query(entries, question, model=cfg.ai_model)
    typer.echo(result)


# ── sync ───────────────────────────────────────────────────────────────

def _get_sync_backend(cfg: ChronicleConfig) -> "SyncBackend":
    """Build the sync backend from config."""
    from chronicle.sync.gist_backend import GistBackend

    if not cfg.sync_enabled:
        typer.echo(
            "Sync is not configured. Run 'chronicle sync setup' first.",
            err=True,
        )
        raise typer.Exit(code=1)

    if cfg.sync_backend == "gist":
        if not cfg.sync_gist_id or not cfg.sync_github_token:
            typer.echo(
                "Gist sync not fully configured. Run 'chronicle sync setup'.",
                err=True,
            )
            raise typer.Exit(code=1)
        return GistBackend(cfg.sync_gist_id, cfg.sync_github_token)

    typer.echo(f"Unknown sync backend: {cfg.sync_backend}", err=True)
    raise typer.Exit(code=1)


def _get_sync_key(cfg: ChronicleConfig) -> bytes:
    """Get the encryption key from config."""
    if not cfg.sync_encryption_key:
        typer.echo("No encryption key configured. Run 'chronicle sync setup'.", err=True)
        raise typer.Exit(code=1)
    return cfg.sync_encryption_key.encode("ascii")


@sync_app.command(name="setup")
def sync_setup(config_dir: ConfigDir = None) -> None:
    """Interactive setup wizard for cloud sync."""
    from chronicle.config import save_sync_config
    from chronicle.sync.crypto import generate_key
    from chronicle.sync.gist_backend import GistBackend

    cfg = _load_config(config_dir)
    if not cfg.log_file.exists():
        typer.echo("Chronicle not initialized. Run 'chronicle init' first.", err=True)
        raise typer.Exit(code=1)

    typer.echo("Chronicle Sync Setup")
    typer.echo("=" * 40)

    # Get GitHub PAT
    github_token = typer.prompt(
        "GitHub Personal Access Token (needs 'gist' scope)",
        hide_input=True,
    )
    if not github_token.strip():
        typer.echo("No token provided.", err=True)
        raise typer.Exit(code=1)
    github_token = github_token.strip()

    # Generate encryption key
    encryption_key = generate_key().decode("ascii")

    # Create Gist
    typer.echo("Creating sync Gist...")
    gist_id = GistBackend.create_gist(github_token)
    typer.echo(f"Gist created: {gist_id}")

    # Save config
    save_sync_config(
        gist_id=gist_id,
        github_token=github_token,
        encryption_key=encryption_key,
        config_dir=config_dir,
    )

    typer.echo("\nSync configured successfully!")
    typer.echo(f"  Backend: gist")
    typer.echo(f"  Gist ID: {gist_id}")
    typer.echo("  Encryption: enabled (Fernet)")
    typer.echo("\nUse 'chronicle push' to backup and 'chronicle pull' to sync.")


@sync_app.command(name="pull")
def sync_pull(config_dir: ConfigDir = None) -> None:
    """Pull new entries from the cloud."""
    from chronicle.sync.pull import pull

    cfg = _load_config(config_dir)
    backend = _get_sync_backend(cfg)
    key = _get_sync_key(cfg)

    typer.echo("Pulling from remote...")
    added = pull(backend, key, cfg.log_file)

    if added:
        typer.echo(f"Pulled {added} new entry(ies).")
    else:
        typer.echo("Already up to date (0 new entries).")


@sync_app.command(name="push")
def sync_push(config_dir: ConfigDir = None) -> None:
    """Push all local entries to the cloud (full backup)."""
    from chronicle.sync.push import push

    cfg = _load_config(config_dir)
    backend = _get_sync_backend(cfg)
    key = _get_sync_key(cfg)

    typer.echo("Pushing to remote...")
    count = push(backend, key, cfg.log_file)

    if count:
        typer.echo(f"Pushed {count} entry(ies) to remote.")
    else:
        typer.echo("No entries to push.")


@sync_app.command(name="status")
def sync_status(config_dir: ConfigDir = None) -> None:
    """Show sync configuration status."""
    cfg = _load_config(config_dir)

    typer.echo("Chronicle Sync Status")
    typer.echo("=" * 40)
    typer.echo(f"  Enabled:  {cfg.sync_enabled}")
    typer.echo(f"  Backend:  {cfg.sync_backend}")

    if cfg.sync_enabled and cfg.sync_backend == "gist":
        typer.echo(f"  Gist ID:  {cfg.sync_gist_id}")
        typer.echo(f"  Token:    {'configured' if cfg.sync_github_token else 'not set'}")
        typer.echo(f"  Key:      {'configured' if cfg.sync_encryption_key else 'not set'}")

    if cfg.log_file.exists() and cfg.log_file.stat().st_size > 0:
        entries = parse_file(cfg.log_file)
        typer.echo(f"  Local entries: {len(entries)}")
    else:
        typer.echo(f"  Local entries: 0")


# ── top-level pull/push shortcuts ──────────────────────────────────────

@app.command(name="pull")
def pull_shortcut(config_dir: ConfigDir = None) -> None:
    """Pull new entries from the cloud (shortcut for 'sync pull')."""
    sync_pull(config_dir=config_dir)


@app.command(name="push")
def push_shortcut(config_dir: ConfigDir = None) -> None:
    """Push all local entries to the cloud (shortcut for 'sync push')."""
    sync_push(config_dir=config_dir)


# ── telegram ───────────────────────────────────────────────────────────

@telegram_app.command(name="setup")
def telegram_setup(
    config_dir: ConfigDir = None,
    bot_token: Annotated[
        Optional[str],
        typer.Option("--token", help="Telegram bot token from @BotFather."),
    ] = None,
    user_id: Annotated[
        Optional[str],
        typer.Option("--user-id", help="Your Telegram numeric user ID."),
    ] = None,
) -> None:
    """Save Telegram bot token and user ID to the chronicle config."""
    from chronicle.config import save_telegram_config

    cfg = _load_config(config_dir)
    if not cfg.log_file.exists():
        typer.echo("Chronicle not initialized. Run 'chronicle init' first.", err=True)
        raise typer.Exit(code=1)

    if not bot_token:
        bot_token = typer.prompt("Telegram bot token (from @BotFather)")
    bot_token = bot_token.strip()
    if not bot_token:
        typer.echo("No bot token provided.", err=True)
        raise typer.Exit(code=1)

    if not user_id:
        user_id = typer.prompt("Your Telegram user ID (numeric)")
    user_id = user_id.strip()
    if not user_id:
        typer.echo("No user ID provided.", err=True)
        raise typer.Exit(code=1)

    toml_path = save_telegram_config(
        bot_token=bot_token,
        user_id=user_id,
        config_dir=config_dir,
    )

    typer.echo(f"Telegram config saved to {toml_path}")
    typer.echo(f"  Bot token: {bot_token[:8]}...{bot_token[-4:]}")
    typer.echo(f"  User ID:   {user_id}")

    if cfg.sync_enabled:
        typer.echo(
            "\nTip: The Telegram bot reads sync config from the same config.toml."
        )


@telegram_app.command(name="status")
def telegram_status(config_dir: ConfigDir = None) -> None:
    """Show Telegram bot configuration status."""
    cfg = _load_config(config_dir)

    typer.echo("Chronicle Telegram Status")
    typer.echo("=" * 40)
    typer.echo(f"  Bot token: {'configured' if cfg.telegram_bot_token else 'not set'}")
    typer.echo(f"  User ID:   {cfg.telegram_user_id or 'not set'}")


def app_main() -> None:
    app()
