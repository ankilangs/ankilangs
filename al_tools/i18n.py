"""Internationalization for AnkiLangs deck content.

Loads translations from SQLite database (populated from CSV files in src/data/i18n/).
Raises KeyError if a requested translation is missing.
"""

from pathlib import Path
from typing import Dict, Optional
import sqlite3

# Cache for loaded translations
_language_names: Optional[Dict[str, Dict[str, str]]] = None
_ui_strings: Optional[Dict[str, Dict[str, str]]] = None
_card_types: Optional[Dict[str, Dict[str, str]]] = None

# Default database path
_DEFAULT_DB_PATH = Path("data.db")


def _get_db_path() -> Path:
    """Get the database path, checking common locations."""
    if _DEFAULT_DB_PATH.exists():
        return _DEFAULT_DB_PATH
    # Try relative to this file (for testing)
    alt_path = Path(__file__).parent.parent / "data.db"
    if alt_path.exists():
        return alt_path
    return _DEFAULT_DB_PATH


def _load_table(db_path: Path, table: str, columns: list[str]) -> list[tuple]:
    """Load rows from a table, raising if the table is missing."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
    )
    if not cursor.fetchone():
        conn.close()
        raise RuntimeError(
            f"Table '{table}' not found in {db_path}. Regenerate with: just csv2sqlite"
        )

    cursor.execute(f"SELECT {', '.join(columns)} FROM {table}")
    rows = cursor.fetchall()
    conn.close()
    return rows


def _load_language_names(db_path: Path) -> Dict[str, Dict[str, str]]:
    """Load language names from database."""
    result: Dict[str, Dict[str, str]] = {}
    for source_locale, target_locale, name in _load_table(
        db_path, "i18n_language_names", ["source_locale", "target_locale", "name"]
    ):
        if source_locale not in result:
            result[source_locale] = {}
        result[source_locale][target_locale] = name
    return result


def _load_ui_strings(db_path: Path) -> Dict[str, Dict[str, str]]:
    """Load UI strings from database."""
    result: Dict[str, Dict[str, str]] = {}
    for locale, key, value in _load_table(
        db_path, "i18n_ui_strings", ["locale", "key", "value"]
    ):
        if locale not in result:
            result[locale] = {}
        result[locale][key] = value
    return result


def _load_card_types(db_path: Path) -> Dict[str, Dict[str, str]]:
    """Load card types from database."""
    result: Dict[str, Dict[str, str]] = {}
    for locale, card_type, name in _load_table(
        db_path, "i18n_card_types", ["locale", "card_type", "name"]
    ):
        if locale not in result:
            result[locale] = {}
        result[locale][card_type] = name
    return result


def _ensure_loaded():
    """Ensure translations are loaded from database."""
    global _language_names, _ui_strings, _card_types

    if _language_names is None:
        db_path = _get_db_path()
        if not db_path.exists():
            raise FileNotFoundError(
                f"Translation database not found at {db_path}. "
                "Generate it with: just csv2sqlite"
            )
        _language_names = _load_language_names(db_path)
        _ui_strings = _load_ui_strings(db_path)
        _card_types = _load_card_types(db_path)


def reload_translations():
    """Force reload translations from database. Useful after csv2sqlite."""
    global _language_names, _ui_strings, _card_types
    _language_names = None
    _ui_strings = None
    _card_types = None
    _ensure_loaded()


def get_supported_locales() -> list[str]:
    """Get list of locales that have language name translations.

    Returns:
        List of locale codes (e.g., ["en_us", "es_es", "de_de", ...])
    """
    _ensure_loaded()
    assert _language_names is not None
    return sorted(_language_names.keys())


def get_card_type_locales() -> list[str]:
    """Get list of locales that have card type translations.

    Returns:
        List of locale codes (e.g., ["en_us", "es_es", "de_de", ...])
    """
    _ensure_loaded()
    assert _card_types is not None
    return sorted(_card_types.keys())


def get_language_name(locale: str, target_locale: str) -> str:
    """Get the name of target language in the source language.

    Args:
        locale: Source language locale (e.g., "en_us")
        target_locale: Target language locale (e.g., "es_es")

    Returns:
        Language name in source language (e.g., "Spanish" for en_us -> es_es)
    """
    _ensure_loaded()
    assert _language_names is not None

    if locale not in _language_names:
        raise KeyError(f"No language names found for locale '{locale}'")

    if target_locale not in _language_names[locale]:
        raise KeyError(f"No language name for '{target_locale}' in locale '{locale}'")

    return _language_names[locale][target_locale]


def get_ui_string(locale: str, key: str, *args) -> str:
    """Get a UI string in the specified locale.

    Args:
        locale: Language locale (e.g., "en_us")
        key: UI string key (e.g., "download_deck")
        *args: Format arguments for strings with placeholders

    Returns:
        Localized UI string
    """
    _ensure_loaded()
    assert _ui_strings is not None

    if locale not in _ui_strings:
        raise KeyError(f"No UI strings found for locale '{locale}'")

    if key not in _ui_strings[locale]:
        raise KeyError(f"Missing UI string '{key}' for locale '{locale}'")

    string = _ui_strings[locale][key]

    if args:
        return string.format(*args)

    return string


def get_card_type_name(locale: str, card_type: str) -> str:
    """Get the name of a card type in the specified locale.

    Args:
        locale: Language locale (e.g., "en_us")
        card_type: Card type key (e.g., "listening", "pronunciation")

    Returns:
        Localized card type name
    """
    _ensure_loaded()
    assert _card_types is not None

    if locale not in _card_types:
        raise KeyError(f"No card types found for locale '{locale}'")

    if card_type not in _card_types[locale]:
        raise KeyError(f"Missing card type '{card_type}' for locale '{locale}'")

    return _card_types[locale][card_type]


def get_apkg_filename(
    source_locale: str,
    target_locale: str,
    deck_type: str,
    version: str,
) -> str:
    """Generate the .apkg filename following the project convention.

    Args:
        source_locale: Source language locale (e.g., "en_us")
        target_locale: Target language locale (e.g., "es_es")
        deck_type: Deck type ("625" or "minimal_pairs")
        version: Version string (e.g., "0.2.0")

    Returns:
        Filename (e.g., "Spanish.EN.to.ES.-.625.Words.-.AnkiLangs.org.-.v0.2.0.apkg")
    """
    # Get target language name in source language
    target_lang_name = get_language_name(source_locale, target_locale)

    # Get localized "to"
    to_word = get_ui_string(source_locale, "to")

    # Convert locales to uppercase for filename
    source_upper = source_locale.split("_")[0].upper()
    target_upper = target_locale.split("_")[0].upper()

    # Get deck type suffix
    if deck_type == "625":
        words = get_ui_string(source_locale, "words")
        type_suffix = f"625.{words}"
    elif deck_type == "minimal_pairs":
        minimal_pairs = get_ui_string(source_locale, "minimal_pairs")
        # Capitalize each word
        minimal_pairs_title = ".".join(
            word.capitalize() for word in minimal_pairs.split()
        )
        type_suffix = minimal_pairs_title
    else:
        type_suffix = deck_type

    filename = f"{target_lang_name}.{source_upper}.{to_word}.{target_upper}.-.{type_suffix}.-.AnkiLangs.org.-.v{version}.apkg"

    return filename
