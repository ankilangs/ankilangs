"""Tests for ContentGenerator — website pages, AnkiWeb descriptions, GitHub release notes."""

from pathlib import Path

import pytest

from al_tools.content import ContentGenerator
from al_tools.registry import Deck
from tests.utils import compare_or_update_golden

# content_dir must be relative to project root (used in GitHub raw URLs)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _make_deck(content_dir, **overrides) -> Deck:
    """Create a test Deck with reasonable defaults."""
    defaults = {
        "deck_id": "en_to_es_625",
        "name": "Spanish (EN to ES) | 625 Words | AnkiLangs.org",
        "tag_name": "EN_to_ES_625_Words",
        "description_file": "src/headers/description_en_to_es-625_words.html",
        "content_dir": str(content_dir.relative_to(_PROJECT_ROOT)),
        "version": "0.3.0",
        "ankiweb_id": "1234567890",
        "deck_type": "625",
        "source_locale": "en_us",
        "target_locale": "es_es",
    }
    defaults.update(overrides)
    return Deck(**defaults)


def test_description_file_content(testdata_dir, golden_dir, pytestconfig):
    """Full output of generate_description_file_content matches golden file."""
    deck = _make_deck(testdata_dir)
    gen = ContentGenerator(deck)
    result = gen.generate_description_file_content("0.3.0")

    compare_or_update_golden(pytestconfig, golden_dir / "output.html", result)


def test_ankiweb_description(testdata_dir, golden_dir, pytestconfig):
    """Full output of generate_ankiweb_description matches golden file."""
    deck = _make_deck(testdata_dir)
    gen = ContentGenerator(deck)
    result = gen.generate_ankiweb_description()

    compare_or_update_golden(pytestconfig, golden_dir / "output.md", result)


def test_ankiweb_description_no_screenshots(testdata_dir, golden_dir, pytestconfig):
    """AnkiWeb description without screenshots omits image section."""
    deck = _make_deck(testdata_dir)
    gen = ContentGenerator(deck)
    result = gen.generate_ankiweb_description()

    compare_or_update_golden(pytestconfig, golden_dir / "output.md", result)


def test_github_release_notes(testdata_dir, golden_dir, pytestconfig):
    """Full output of generate_github_release_notes matches golden file."""
    deck = _make_deck(testdata_dir)
    gen = ContentGenerator(deck)
    result = gen.generate_github_release_notes("0.3.0")

    compare_or_update_golden(pytestconfig, golden_dir / "output.md", result)


def test_github_release_notes_no_ankiweb(testdata_dir, golden_dir, pytestconfig):
    """Release notes without ankiweb_id omit AnkiWeb link."""
    deck = _make_deck(testdata_dir, ankiweb_id=None)
    gen = ContentGenerator(deck)
    result = gen.generate_github_release_notes("0.3.0")

    compare_or_update_golden(pytestconfig, golden_dir / "output.md", result)


def test_github_release_notes_missing_version_raises(testdata_dir):
    """Requesting release notes for a nonexistent version raises ValueError."""
    deck = _make_deck(testdata_dir)
    gen = ContentGenerator(deck)

    with pytest.raises(ValueError, match="No changelog entry"):
        gen.generate_github_release_notes("9.9.9")
