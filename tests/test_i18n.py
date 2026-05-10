"""Tests for the i18n module."""

from pathlib import Path

import pytest

from al_tools.core import csv2sqlite
import al_tools.i18n as i18n_module

# Path to test CSV data (shared across all tests in this file)
_TESTDATA_DIR = Path(__file__).parent / "testdata" / "test_i18n"


@pytest.fixture(autouse=True)
def _i18n_test_db(tmp_path, monkeypatch):
    """Create a small SQLite DB from test CSVs and point i18n at it."""
    db_path = tmp_path / "test_i18n.db"
    csv2sqlite(_TESTDATA_DIR, db_path, force=True)

    # Reset the module-level cache and point at our test DB
    i18n_module._language_names = None
    i18n_module._ui_strings = None
    i18n_module._card_types = None
    monkeypatch.setattr(i18n_module, "_DEFAULT_DB_PATH", db_path)

    yield

    # Reset cache after test
    i18n_module._language_names = None
    i18n_module._ui_strings = None
    i18n_module._card_types = None


# --- get_language_name ---


def test_get_language_name():
    assert i18n_module.get_language_name("en_us", "es_es") == "Spanish"


def test_get_language_name_missing_locale():
    with pytest.raises(KeyError, match="No language names found for locale 'xx_xx'"):
        i18n_module.get_language_name("xx_xx", "en_us")


def test_get_language_name_missing_target():
    with pytest.raises(KeyError, match="No language name for 'xx_xx'"):
        i18n_module.get_language_name("en_us", "xx_xx")


# --- get_ui_string ---


def test_get_ui_string():
    assert i18n_module.get_ui_string("en_us", "download_deck") == "Download deck"


def test_get_ui_string_with_format_args():
    assert i18n_module.get_ui_string("es_es", "greeting", "Mundo") == "¡Hola Mundo!"


def test_get_ui_string_missing_locale():
    with pytest.raises(KeyError, match="No UI strings found for locale 'xx_xx'"):
        i18n_module.get_ui_string("xx_xx", "to")


def test_get_ui_string_missing_key():
    with pytest.raises(KeyError, match="Missing UI string 'nonexistent'"):
        i18n_module.get_ui_string("en_us", "nonexistent")


# --- get_card_type_name ---


def test_get_card_type_name():
    assert i18n_module.get_card_type_name("es_es", "pronunciation") == "Pronunciación"


def test_get_card_type_name_missing():
    with pytest.raises(KeyError, match="No card types found for locale 'xx_xx'"):
        i18n_module.get_card_type_name("xx_xx", "listening")


# --- locale lists ---


def test_get_supported_locales():
    locales = i18n_module.get_supported_locales()
    assert locales == ["en_us", "es_es"]


def test_get_card_type_locales():
    locales = i18n_module.get_card_type_locales()
    assert locales == ["en_us", "es_es"]


# --- get_apkg_filename ---


def test_get_apkg_filename_625():
    filename = i18n_module.get_apkg_filename("en_us", "es_es", "625", "0.2.0")
    assert filename == "Spanish.EN.to.ES.-.625.Words.-.AnkiLangs.org.-.v0.2.0.apkg"


def test_get_apkg_filename_minimal_pairs():
    filename = i18n_module.get_apkg_filename("en_us", "es_es", "minimal_pairs", "1.0.0")
    assert filename == "Spanish.EN.to.ES.-.Minimal.Pairs.-.AnkiLangs.org.-.v1.0.0.apkg"


# --- reload_translations ---


def test_reload_translations():
    # Load once
    assert i18n_module.get_language_name("en_us", "es_es") == "Spanish"
    # Reload should not error and data should still be accessible
    i18n_module.reload_translations()
    assert i18n_module.get_language_name("en_us", "es_es") == "Spanish"
