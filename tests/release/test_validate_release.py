"""Tests for validate_version_bump and validate_release."""

from unittest import mock

from al_tools.release import validate_version_bump, validate_release
from al_tools.registry import Deck


# --- validate_version_bump (pure logic, no fixtures needed) ---


def test_dev_to_release():
    ok, err = validate_version_bump("1.0.0-dev", "1.0.0")
    assert ok
    assert err is None


def test_release_to_next_patch_dev():
    ok, err = validate_version_bump("1.0.0", "1.0.1-dev")
    assert ok


def test_release_to_next_minor_dev():
    ok, err = validate_version_bump("1.0.0", "1.1.0-dev")
    assert ok


def test_release_to_next_major_dev():
    ok, err = validate_version_bump("1.0.0", "2.0.0-dev")
    assert ok


def test_release_to_release_rejected():
    ok, err = validate_version_bump("1.0.0", "1.0.1")
    assert not ok
    assert "dev version" in err


def test_dev_to_major_bump_release_allowed():
    """From 1.0.0-dev, jumping to 2.0.0 is allowed."""
    ok, err = validate_version_bump("1.0.0-dev", "2.0.0")
    assert ok


def test_invalid_version_format():
    ok, err = validate_version_bump("bad", "1.0.0")
    assert not ok
    assert "Invalid version" in err


def test_dev_to_minor_bump_release():
    """From dev, can bump to next minor release directly."""
    ok, err = validate_version_bump("1.0.0-dev", "1.1.0")
    assert ok


def test_dev_to_far_future_rejected():
    """From 1.0.0-dev, jumping to 3.0.0 is not allowed."""
    ok, err = validate_version_bump("1.0.0-dev", "3.0.0")
    assert not ok


# --- validate_release (uses testdata_dir for content files) ---


def _make_deck(content_dir, **overrides) -> Deck:
    defaults = {
        "deck_id": "en_to_es_625",
        "name": "Spanish (EN to ES) | 625 Words | AnkiLangs.org",
        "tag_name": "EN_to_ES_625_Words",
        "description_file": str(content_dir / "description.html"),
        "content_dir": str(content_dir),
        "version": "0.3.0-dev",
        "ankiweb_id": "123",
        "deck_type": "625",
        "source_locale": "en_us",
        "target_locale": "es_es",
    }
    defaults.update(overrides)
    return Deck(**defaults)


def test_valid_release_passes(testdata_dir):
    deck = _make_deck(testdata_dir)

    def mock_run_side_effect(*args, **kwargs):
        cmd = args[0]
        if cmd[0] == "jj":
            return mock.Mock(stdout="The working copy has no changes", returncode=0)
        if cmd[0] == "git" and "tag" in cmd:
            return mock.Mock(stdout="", returncode=0)
        return mock.Mock(stdout="", returncode=0)

    with mock.patch("subprocess.run", side_effect=mock_run_side_effect):
        result = validate_release(deck, "0.3.0")

    assert result.is_valid


def test_detects_missing_changelog_entry(testdata_dir):
    deck = _make_deck(testdata_dir)

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(
            stdout="The working copy has no changes", returncode=0
        )
        result = validate_release(deck, "0.3.0")

    assert not result.is_valid
    assert any("changelog" in e.lower() for e in result.errors)


def test_detects_missing_description_file(testdata_dir):
    deck = _make_deck(
        testdata_dir,
        description_file=str(testdata_dir / "nonexistent.html"),
    )

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(
            stdout="The working copy has no changes", returncode=0
        )
        result = validate_release(deck, "0.3.0")

    assert not result.is_valid
    assert any("description" in e.lower() for e in result.errors)


def test_missing_screenshots_is_warning(testdata_dir):
    deck = _make_deck(testdata_dir)

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(
            stdout="The working copy has no changes", returncode=0
        )
        result = validate_release(deck, "0.3.0")

    assert any("screenshot" in w.lower() for w in result.warnings)


def test_detects_existing_tag(testdata_dir):
    deck = _make_deck(testdata_dir)

    def mock_run_side_effect(*args, **kwargs):
        cmd = args[0]
        if cmd[0] == "jj":
            return mock.Mock(stdout="The working copy has no changes", returncode=0)
        if cmd[0] == "git" and "tag" in cmd:
            return mock.Mock(stdout="EN_to_ES_625_Words/0.3.0\n", returncode=0)
        return mock.Mock(stdout="", returncode=0)

    with mock.patch("subprocess.run", side_effect=mock_run_side_effect):
        result = validate_release(deck, "0.3.0")

    assert not result.is_valid
    assert any("tag" in e.lower() for e in result.errors)
