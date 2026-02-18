"""Configuration loading and defaults."""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


def _default_editor() -> str:
    env = os.environ.get("EDITOR", "")
    if env:
        return env
    if sys.platform == "win32":
        return "notepad"
    return "vi"


@dataclass
class ChronicleConfig:
    chronicle_dir: Path
    log_file: Path
    editor: str
    timezone: str
    ai_enabled: bool
    ai_provider: str
    ai_model: str
    ai_api_key: str = ""

    @property
    def processed_file(self) -> Path:
        return self.chronicle_dir / "ai_processed.json"

    @classmethod
    def defaults(cls, chronicle_dir: Path | None = None) -> ChronicleConfig:
        d = chronicle_dir or Path.home() / ".chronicle"
        return cls(
            chronicle_dir=d,
            log_file=d / "chronicle.log",
            editor=_default_editor(),
            timezone="UTC",
            ai_enabled=False,
            ai_provider="openai",
            ai_model="gpt-4o-mini",
            ai_api_key="",
        )


def default_config_toml() -> str:
    """Return a default config.toml template string."""
    return """\
[chronicle]
# editor = "code --wait"
# timezone = "America/New_York"

[ai]
enabled = false
# provider = "openai"
# model = "gpt-4o-mini"
# Set the OPENAI_API_KEY environment variable to use AI features.
"""


def load_config(config_dir: Path | None = None) -> ChronicleConfig:
    """Load config from TOML file, falling back to defaults."""
    cfg = ChronicleConfig.defaults(config_dir)
    toml_path = cfg.chronicle_dir / "config.toml"

    if toml_path.exists():
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)

        chronicle = data.get("chronicle", {})
        if "editor" in chronicle:
            cfg.editor = chronicle["editor"]
        if "timezone" in chronicle:
            cfg.timezone = chronicle["timezone"]

        ai = data.get("ai", {})
        if "enabled" in ai:
            cfg.ai_enabled = ai["enabled"]
        if "provider" in ai:
            cfg.ai_provider = ai["provider"]
        if "model" in ai:
            cfg.ai_model = ai["model"]
        if "api_key" in ai:
            cfg.ai_api_key = ai["api_key"]

    return cfg


def save_api_key(api_key: str, config_dir: Path | None = None) -> Path:
    """Save an API key into the config.toml [ai] section.

    If the file already has an api_key line, it is replaced.
    If [ai] section exists but no api_key, the key is inserted after the section header.
    If no [ai] section, one is appended.
    Returns the path to the config file.
    """
    import re

    cfg = ChronicleConfig.defaults(config_dir)
    toml_path = cfg.chronicle_dir / "config.toml"

    cfg.chronicle_dir.mkdir(parents=True, exist_ok=True)
    if not toml_path.exists():
        toml_path.write_text(default_config_toml(), encoding="utf-8")

    text = toml_path.read_text(encoding="utf-8")
    key_line = f'api_key = "{api_key}"'

    # Case 1: api_key line already exists — replace it
    if re.search(r'^#?\s*api_key\s*=', text, re.MULTILINE):
        text = re.sub(
            r'^#?\s*api_key\s*=.*$',
            key_line,
            text,
            count=1,
            flags=re.MULTILINE,
        )
    # Case 2: [ai] section exists — insert after it
    elif re.search(r'^\[ai\]', text, re.MULTILINE):
        text = re.sub(
            r'^(\[ai\]\s*\n)',
            rf'\g<1>{key_line}\n',
            text,
            count=1,
            flags=re.MULTILINE,
        )
    # Case 3: no [ai] section — append one
    else:
        text = text.rstrip() + f"\n\n[ai]\n{key_line}\n"

    toml_path.write_text(text, encoding="utf-8")
    return toml_path
