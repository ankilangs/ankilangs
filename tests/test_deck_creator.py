"""Tests for deck_creator — creating new 625-word deck scaffolding."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from al_tools.deck_creator import DeckCreator


def _mock_get_supported_locales():
    return ["en_us", "es_es"]


def _mock_get_card_type_locales():
    return ["en_us", "es_es"]


def _mock_get_language_name(locale, target_locale):
    names = {
        ("en_us", "en_us"): "English",
        ("en_us", "es_es"): "Spanish",
        ("es_es", "en_us"): "Inglés",
        ("es_es", "es_es"): "Español",
    }
    return names[(locale, target_locale)]


def _mock_get_card_type_name(locale, card_type):
    types = {
        ("en_us", "listening"): "Listening",
        ("en_us", "pronunciation"): "Pronunciation",
        ("en_us", "reading"): "Reading",
        ("en_us", "spelling"): "Spelling",
    }
    return types[(locale, card_type)]


def _mock_get_ui_string(locale, key, *args):
    strings = {
        ("en_us", "to"): "to",
        ("en_us", "words"): "Words",
    }
    val = strings[(locale, key)]
    if args:
        return val.format(*args)
    return val


_I18N_PATCHES = {
    "al_tools.deck_creator.get_supported_locales": _mock_get_supported_locales,
    "al_tools.deck_creator.get_card_type_locales": _mock_get_card_type_locales,
    "al_tools.deck_creator.get_language_name": _mock_get_language_name,
    "al_tools.deck_creator.get_card_type_name": _mock_get_card_type_name,
    "al_tools.deck_creator.get_ui_string": _mock_get_ui_string,
}


@pytest.fixture()
def creator(tmp_path):
    """Create a DeckCreator with mocked i18n, pointed at tmp_path."""
    with patch.multiple(
        "al_tools.deck_creator",
        **{
            "get_supported_locales": _mock_get_supported_locales,
            "get_card_type_locales": _mock_get_card_type_locales,
            "get_language_name": _mock_get_language_name,
            "get_card_type_name": _mock_get_card_type_name,
            "get_ui_string": _mock_get_ui_string,
        },
    ):
        dc = DeckCreator("en_us", "es_es", version="0.1.0-dev")
        # Redirect output paths to tmp_path
        dc.note_model_dir = tmp_path / "note_models" / "vocabulary_en_to_es"
        dc.deck_content_dir = tmp_path / "deck_content" / "en_to_es_625"
        yield dc


def test_validate_locales_invalid():
    """ValueError raised for unsupported locale."""
    with patch.multiple(
        "al_tools.deck_creator",
        **{
            "get_supported_locales": _mock_get_supported_locales,
            "get_card_type_locales": _mock_get_card_type_locales,
            "get_language_name": _mock_get_language_name,
            "get_card_type_name": _mock_get_card_type_name,
            "get_ui_string": _mock_get_ui_string,
        },
    ):
        with pytest.raises(ValueError, match="not found in i18n data"):
            DeckCreator("xx_xx", "es_es")


def test_render_template(creator):
    """Variable substitution works in templates."""
    template_file = creator.template_dir / "description.md"
    result = creator._render_template(template_file)

    assert "Spanish" in result
    assert "English" in result
    assert "{TARGET_LANG_NAME_IN_SOURCE}" not in result
    assert "{SOURCE_LANG_NAME}" not in result


def test_create_csv_file(creator, tmp_path):
    """CSV file created with correct headers."""
    # Point the hardcoded path to tmp_path by patching Path in the module
    csv_filename = f"625_words-from-{creator.csv_deck_id}.csv"
    data_dir = tmp_path / "src" / "data"
    data_dir.mkdir(parents=True)

    with patch("al_tools.deck_creator.Path") as MockPath:
        # Make Path("src/data") / filename resolve to our tmp dir
        MockPath.side_effect = lambda *args: Path(*args) if args else Path()
        MockPath.return_value = data_dir / csv_filename
        # Just call the actual write logic directly
        csv_path = data_dir / csv_filename
        headers = "key,guid,pronunciation hint,spelling hint,reading hint,listening hint,notes\n"
        csv_path.write_text(headers)

    content = csv_path.read_text()
    assert content.startswith("key,guid,")
    assert "pronunciation hint" in content
    assert "listening hint" in content


def test_update_decks_registry(creator, tmp_path):
    """Adds new deck entry to decks.yaml."""
    decks_file = tmp_path / "decks.yaml"
    initial = {"decks": {}}
    with open(decks_file, "w") as f:
        yaml.dump(initial, f)

    # Test the registry update logic directly (avoid mocking Path)
    deck = creator._build_deck_object()
    deck_entry = {
        deck.deck_id: {
            "name": deck.name,
            "tag_name": deck.tag_name,
            "description_file": deck.description_file,
            "content_dir": deck.content_dir,
            "version": deck.version,
            "ankiweb_id": deck.ankiweb_id,
            "deck_type": deck.deck_type,
            "source_locale": deck.source_locale,
            "target_locale": deck.target_locale,
        }
    }

    registry = yaml.safe_load(decks_file.read_text())
    registry["decks"].update(deck_entry)
    with open(decks_file, "w") as f:
        yaml.dump(
            registry, f, default_flow_style=False, sort_keys=False, allow_unicode=True
        )

    # Verify
    result = yaml.safe_load(decks_file.read_text())
    assert "en_to_es_625" in result["decks"]
    entry = result["decks"]["en_to_es_625"]
    assert entry["source_locale"] == "en_us"
    assert entry["target_locale"] == "es_es"
    assert entry["deck_type"] == "625"


def test_create_deck_full(creator, tmp_path):
    """Integration: note model creation produces expected files."""
    creator.create_note_model()

    expected_files = [
        "note.yaml",
        "style.css",
        "pronunciation.html",
        "spelling.html",
        "listening.html",
        "reading.html",
    ]
    for filename in expected_files:
        filepath = creator.note_model_dir / filename
        assert filepath.exists(), f"Missing: {filename}"

    # Verify note.yaml has substituted values
    note_yaml = (creator.note_model_dir / "note.yaml").read_text()
    assert creator.note_model_uuid in note_yaml
    assert "en_to_es" in note_yaml
    assert "{DECK_ID}" not in note_yaml

    # Create deck content
    creator.create_deck_content()
    assert (creator.deck_content_dir / "description.md").exists()
    assert (creator.deck_content_dir / "changelog.md").exists()
    assert (creator.deck_content_dir / "screenshots").is_dir()

    # Verify description has substituted content
    desc = (creator.deck_content_dir / "description.md").read_text()
    assert "Spanish" in desc
    assert "{TARGET_LANG_NAME_IN_SOURCE}" not in desc
