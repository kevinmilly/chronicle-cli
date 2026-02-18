"""Integration tests for chronicle CLI commands."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from chronicle.cli import app

runner = CliRunner()


def _init(tmp_path: Path) -> Path:
    config_dir = tmp_path / ".chronicle"
    runner.invoke(app, ["init", "--config-dir", str(config_dir)])
    return config_dir


def _add_entry(config_dir: Path):
    """Add an entry using --editor with mocked editor."""
    with patch("chronicle.cli.typer.edit", return_value="Test body content."):
        return runner.invoke(
            app,
            [
                "add",
                "--config-dir",
                str(config_dir),
                "--editor",
            ],
        )


def _add_entry_prompt(config_dir: Path):
    """Add an entry via the default prompt."""
    return runner.invoke(
        app,
        ["add", "--config-dir", str(config_dir)],
        input="Test body content.\n",
    )


def test_init_creates_structure(tmp_path: Path):
    config_dir = tmp_path / ".chronicle"
    result = runner.invoke(app, ["init", "--config-dir", str(config_dir)])
    assert result.exit_code == 0
    assert config_dir.exists()
    assert (config_dir / "chronicle.log").exists()
    assert (config_dir / "config.toml").exists()


def test_init_idempotent(tmp_path: Path):
    config_dir = _init(tmp_path)
    result = runner.invoke(app, ["init", "--config-dir", str(config_dir)])
    assert result.exit_code == 0


def test_add_editor_appends_entry(tmp_path: Path):
    config_dir = _init(tmp_path)
    result = _add_entry(config_dir)
    assert result.exit_code == 0
    assert "added" in result.output.lower()

    log = (config_dir / "chronicle.log").read_text()
    assert "@entry" in log
    assert "@end" in log
    assert "entry" in log  # entry_type is "entry"


def test_add_prompt_appends_entry(tmp_path: Path):
    config_dir = _init(tmp_path)
    result = _add_entry_prompt(config_dir)
    assert result.exit_code == 0
    assert "added" in result.output.lower()

    log = (config_dir / "chronicle.log").read_text()
    assert "Test body content." in log


def test_add_with_tags_and_people(tmp_path: Path):
    config_dir = _init(tmp_path)
    with patch("chronicle.cli.typer.edit", return_value="Tagged entry."):
        result = runner.invoke(
            app,
            [
                "add",
                "--config-dir",
                str(config_dir),
                "--editor",
                "--tags",
                "work,python",
                "--people",
                "Alice,Bob",
            ],
        )
    assert result.exit_code == 0
    log = (config_dir / "chronicle.log").read_text()
    assert "work,python" in log
    assert "people:Alice,Bob" in log


def test_validate_valid(tmp_path: Path):
    config_dir = _init(tmp_path)
    _add_entry(config_dir)

    result = runner.invoke(app, ["validate", "--config-dir", str(config_dir)])
    assert result.exit_code == 0
    assert "valid" in result.output.lower()


def test_validate_invalid(tmp_path: Path):
    config_dir = _init(tmp_path)
    log_file = config_dir / "chronicle.log"
    log_file.write_text("@entry bad header\n@end\n")

    result = runner.invoke(app, ["validate", "--config-dir", str(config_dir)])
    assert result.exit_code == 1


def test_week_produces_output(tmp_path: Path):
    config_dir = _init(tmp_path)
    _add_entry(config_dir)

    result = runner.invoke(
        app,
        ["week", "--config-dir", str(config_dir)],
    )
    assert result.exit_code == 0
    assert "Weekly Brief" in result.output


def test_stats_no_processed(tmp_path: Path):
    config_dir = _init(tmp_path)
    _add_entry(config_dir)

    result = runner.invoke(
        app,
        ["stats", "--config-dir", str(config_dir)],
    )
    assert result.exit_code == 0
    assert "No processed entries" in result.output


def test_add_key_saves_to_config(tmp_path: Path):
    config_dir = _init(tmp_path)
    result = runner.invoke(
        app,
        ["add-key", "--config-dir", str(config_dir)],
        input="sk-test-key-12345\n",
    )
    assert result.exit_code == 0
    assert "API key saved" in result.output

    # Verify key is in config.toml
    toml_text = (config_dir / "config.toml").read_text()
    assert 'api_key = "sk-test-key-12345"' in toml_text


def test_add_key_replaces_existing(tmp_path: Path):
    config_dir = _init(tmp_path)
    # Add first key
    runner.invoke(
        app,
        ["add-key", "--config-dir", str(config_dir)],
        input="sk-old-key\n",
    )
    # Replace with new key
    result = runner.invoke(
        app,
        ["add-key", "--config-dir", str(config_dir)],
        input="sk-new-key\n",
    )
    assert result.exit_code == 0

    toml_text = (config_dir / "config.toml").read_text()
    assert 'api_key = "sk-new-key"' in toml_text
    assert "sk-old-key" not in toml_text
