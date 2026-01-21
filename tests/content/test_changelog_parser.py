"""Tests for changelog parsing."""

from datetime import datetime
from pathlib import Path

import pytest

from al_tools.content import ChangelogParser


def test_parse_single_entry(tmp_path: Path):
    """Test parsing a changelog with a single entry."""
    changelog = tmp_path / "changelog.md"
    changelog.write_text("""## 0.2.0 - 2025-01-22

- Initial public release
- Added 625 words
""")

    entries = ChangelogParser.parse(changelog)

    assert len(entries) == 1
    assert entries[0].version == "0.2.0"
    assert entries[0].date == datetime(2025, 1, 22)
    assert len(entries[0].changes) == 2
    assert entries[0].changes[0] == "Initial public release"
    assert entries[0].changes[1] == "Added 625 words"


def test_parse_multiple_entries(tmp_path: Path):
    """Test parsing a changelog with multiple entries."""
    changelog = tmp_path / "changelog.md"
    changelog.write_text("""## 0.3.0 - 2026-01-15

- Fixed typo in 'izquierda'
- Added disambiguation hints for 12 ambiguous words

## 0.2.0 - 2025-01-22

- Initial public release
""")

    entries = ChangelogParser.parse(changelog)

    assert len(entries) == 2
    assert entries[0].version == "0.3.0"
    assert entries[0].date == datetime(2026, 1, 15)
    assert len(entries[0].changes) == 2

    assert entries[1].version == "0.2.0"
    assert entries[1].date == datetime(2025, 1, 22)
    assert len(entries[1].changes) == 1


def test_parse_entry_without_date(tmp_path: Path):
    """Test parsing an entry without a date."""
    changelog = tmp_path / "changelog.md"
    changelog.write_text("""## 0.2.0

- Initial public release
""")

    entries = ChangelogParser.parse(changelog)

    assert len(entries) == 1
    assert entries[0].version == "0.2.0"
    assert entries[0].date is None
    assert len(entries[0].changes) == 1


def test_parse_with_mixed_bullet_styles(tmp_path: Path):
    """Test parsing with both - and * bullet styles."""
    changelog = tmp_path / "changelog.md"
    changelog.write_text("""## 0.2.0 - 2025-01-22

- First change
* Second change
- Third change
""")

    entries = ChangelogParser.parse(changelog)

    assert len(entries) == 1
    assert len(entries[0].changes) == 3
    assert entries[0].changes[0] == "First change"
    assert entries[0].changes[1] == "Second change"
    assert entries[0].changes[2] == "Third change"


def test_get_version_entry(tmp_path: Path):
    """Test getting a specific version entry."""
    changelog = tmp_path / "changelog.md"
    changelog.write_text("""## 0.3.0 - 2026-01-15

- New feature

## 0.2.0 - 2025-01-22

- Initial release
""")

    entry = ChangelogParser.get_version_entry(changelog, "0.2.0")

    assert entry is not None
    assert entry.version == "0.2.0"
    assert len(entry.changes) == 1
    assert entry.changes[0] == "Initial release"


def test_get_version_entry_not_found(tmp_path: Path):
    """Test getting a version that doesn't exist."""
    changelog = tmp_path / "changelog.md"
    changelog.write_text("""## 0.2.0 - 2025-01-22

- Initial release
""")

    entry = ChangelogParser.get_version_entry(changelog, "0.3.0")

    assert entry is None


def test_get_latest_entry(tmp_path: Path):
    """Test getting the latest entry."""
    changelog = tmp_path / "changelog.md"
    changelog.write_text("""## 0.3.0 - 2026-01-15

- New feature

## 0.2.0 - 2025-01-22

- Initial release
""")

    entry = ChangelogParser.get_latest_entry(changelog)

    assert entry is not None
    assert entry.version == "0.3.0"


def test_parse_empty_file(tmp_path: Path):
    """Test parsing an empty changelog."""
    changelog = tmp_path / "changelog.md"
    changelog.write_text("")

    entries = ChangelogParser.parse(changelog)

    assert len(entries) == 0


def test_parse_nonexistent_file(tmp_path: Path):
    """Test parsing a file that doesn't exist."""
    changelog = tmp_path / "nonexistent.md"

    with pytest.raises(FileNotFoundError):
        ChangelogParser.parse(changelog)
