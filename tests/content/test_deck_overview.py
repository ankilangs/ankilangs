"""Tests for generate_deck_overview_page — main deck listing page."""

from pathlib import Path
from unittest.mock import patch, MagicMock

from al_tools.content import generate_deck_overview_page
from al_tools.registry import Deck, DeckRegistry
from tests.utils import compare_or_update_golden


def _make_test_deck(
    tmp_path, deck_id, name, source_locale, target_locale, version="0.3.0", **kw
):
    content_dir = tmp_path / deck_id
    defaults = {
        "deck_id": deck_id,
        "name": name,
        "tag_name": deck_id.replace("_", "_").upper() + "_Words",
        "description_file": f"src/headers/description_{deck_id}.html",
        "content_dir": str(content_dir),
        "version": version,
        "ankiweb_id": None,
        "deck_type": "625",
        "source_locale": source_locale,
        "target_locale": target_locale,
    }
    defaults.update(kw)
    return Deck(**defaults)


def _mock_get_language_name(locale, target_locale):
    names = {
        ("en_us", "en_us"): "English",
        ("en_us", "es_es"): "Spanish",
        ("en_us", "de_de"): "German",
        ("es_es", "en_us"): "Inglés",
        ("es_es", "es_es"): "Español",
    }
    return names.get((locale, target_locale), f"Unknown({target_locale})")


def _mock_get_ui_string(locale, key, *args):
    strings = {
        ("en_us", "source_language_decks_header"): "English Decks",
        (
            "en_us",
            "learn_other_languages_intro",
        ): "Learn other languages if you speak English",
        ("es_es", "source_language_decks_header"): "Mazos españoles",
        (
            "es_es",
            "learn_other_languages_intro",
        ): "Aprende otros idiomas si hablas español",
    }
    val = strings.get((locale, key), f"missing:{key}")
    if args:
        return val.format(*args)
    return val


def test_generate_deck_overview_page(golden_dir, pytestconfig, tmp_path):
    """Golden file test for the full deck overview page."""
    # Create test decks: 2 English-source, 1 Spanish-source (but Spanish is minimal_pairs so filtered)
    decks = [
        _make_test_deck(
            tmp_path,
            "en_to_es_625",
            "Spanish (EN to ES) | 625 Words | AnkiLangs.org",
            "en_us",
            "es_es",
            version="0.3.0",
        ),
        _make_test_deck(
            tmp_path,
            "en_to_de_625",
            "German (EN to DE) | 625 Words | AnkiLangs.org",
            "en_us",
            "de_de",
            version="0.2.0",
        ),
        _make_test_deck(
            tmp_path,
            "es_to_en_625",
            "Inglés (ES a EN) | 625 Words | AnkiLangs.org",
            "es_es",
            "en_us",
            version="0.1.0-dev",
        ),
    ]

    # Create a mock registry
    registry = MagicMock(spec=DeckRegistry)
    registry.all.return_value = decks
    registry.get_latest_release_version.return_value = None  # no git tags in test

    # Create minimal changelog files for version lookup
    for deck in decks:
        content_dir = Path(deck.content_dir)
        content_dir.mkdir(parents=True, exist_ok=True)
        changelog = content_dir / "changelog.md"
        if not deck.is_dev_version:
            changelog.write_text(f"## {deck.version} - 2025-01-15\n- Initial release\n")
        else:
            changelog.write_text("## 0.1.0-dev\n- Work in progress\n")

    with (
        patch(
            "al_tools.content.get_language_name", side_effect=_mock_get_language_name
        ),
        patch("al_tools.content.get_ui_string", side_effect=_mock_get_ui_string),
    ):
        result = generate_deck_overview_page(registry)

    compare_or_update_golden(pytestconfig, golden_dir / "output.md", result)
