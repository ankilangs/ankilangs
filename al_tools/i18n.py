"""Internationalization for AnkiLangs deck content."""

from typing import Dict

# Language names in each source language
LANGUAGE_NAMES: Dict[str, Dict[str, str]] = {
    "de_de": {
        "de_de": "Deutsch",
        "en_us": "Englisch",
        "es_es": "Spanisch",
        "fr_fr": "Franzosisch",  # ASCII-safe (no umlaut)
        "it_it": "Italienisch",
        "la_la": "Latein",
        "pt_pt": "Portugiesisch",
        "sq_al": "Albanisch",
        "fa_ir": "Persisch",
    },
    "en_us": {
        "de_de": "German",
        "en_us": "English",
        "es_es": "Spanish",
        "fr_fr": "French",
        "it_it": "Italian",
        "la_la": "Latin",
        "pt_pt": "Portuguese",
        "sq_al": "Albanian",
        "fa_ir": "Farsi",
    },
    "es_es": {
        "de_de": "Aleman",  # ASCII-safe (no accent)
        "en_us": "Ingles",  # ASCII-safe (no accent)
        "es_es": "Espanol",  # ASCII-safe (no tilde)
        "fr_fr": "Frances",  # ASCII-safe (no accent)
        "it_it": "Italiano",
        "la_la": "Latin",  # ASCII-safe (no accent)
        "pt_pt": "Portugues",  # ASCII-safe (no accent)
        "sq_al": "Albanes",  # ASCII-safe (no accent)
        "fa_ir": "Persa",
    },
    "fr_fr": {
        "de_de": "Allemand",
        "en_us": "Anglais",
        "es_es": "Espagnol",
        "fr_fr": "Français",
        "it_it": "Italien",
        "la_la": "Latin",
        "pt_pt": "Portugais",
        "sq_al": "Albanais",
        "fa_ir": "Persan",
    },
    "it_it": {
        "de_de": "Tedesco",
        "en_us": "Inglese",
        "es_es": "Spagnolo",
        "fr_fr": "Francese",
        "it_it": "Italiano",
        "la_la": "Latino",
        "pt_pt": "Portoghese",
        "sq_al": "Albanese",
        "fa_ir": "Persiano",
    },
    "pt_pt": {
        "de_de": "Alemão",
        "en_us": "Inglês",
        "es_es": "Espanhol",
        "fr_fr": "Francês",
        "it_it": "Italiano",
        "la_la": "Latim",
        "pt_pt": "Português",
        "sq_al": "Albanês",
        "fa_ir": "Persa",
    },
}

# UI strings for each locale
UI_STRINGS: Dict[str, Dict[str, str]] = {
    "de_de": {
        "to": "zu",
        "words": "Worter",  # ASCII-safe version (no umlaut) for filenames
        "minimal_pairs": "Minimalpaar",
        "download_deck": "Deck herunterladen",
        "installation_instructions": "Installationsanleitung",
        "learning_tips": "Lerntipps",
        "screenshots": "Screenshots",
        "changelog": "Änderungsprotokoll",
        "notes": "Hinweise",
        "see_x_and_y": "Siehe {} und {}.",
        "version": "Version",
        "whats_new_in": "Was ist neu in {}",
        "unreleased_note": "Dieses Deck ist noch nicht veröffentlicht und befindet sich in der Entwicklung.",
    },
    "en_us": {
        "to": "to",
        "words": "Words",
        "minimal_pairs": "Minimal Pairs",
        "download_deck": "Download deck",
        "installation_instructions": "Installation Instructions",
        "learning_tips": "Learning Tips",
        "screenshots": "Screenshots",
        "changelog": "Changelog",
        "notes": "Notes",
        "see_x_and_y": "See {} and {}.",
        "version": "Version",
        "whats_new_in": "What's New in {}",
        "unreleased_note": "This deck is not yet released and is under development.",
    },
    "es_es": {
        "to": "a",
        "words": "palabras",
        "minimal_pairs": "pares mínimos",
        "download_deck": "Descargar mazo",
        "installation_instructions": "Instrucciones de instalación",
        "learning_tips": "Consejos de aprendizaje",
        "screenshots": "Capturas de pantalla",
        "changelog": "Registro de cambios",
        "notes": "Notas",
        "see_x_and_y": "Ver {} y {}.",
        "version": "Versión",
        "whats_new_in": "Novedades en {}",
        "unreleased_note": "Este mazo aún no está publicado y está en desarrollo.",
    },
    "fr_fr": {
        "to": "à",
        "words": "mots",
        "minimal_pairs": "paires minimales",
        "download_deck": "Télécharger le paquet",
        "installation_instructions": "Instructions d'installation",
        "learning_tips": "Conseils d'apprentissage",
        "screenshots": "Captures d'écran",
        "changelog": "Journal des modifications",
        "notes": "Notes",
        "see_x_and_y": "Voir {} et {}.",
        "version": "Version",
        "whats_new_in": "Nouveautés de {}",
        "unreleased_note": "Ce paquet n'est pas encore publié et est en cours de développement.",
    },
    "it_it": {
        "to": "a",
        "words": "parole",
        "minimal_pairs": "coppie minime",
        "download_deck": "Scarica mazzo",
        "installation_instructions": "Istruzioni di installazione",
        "learning_tips": "Suggerimenti per l'apprendimento",
        "screenshots": "Screenshot",
        "changelog": "Registro delle modifiche",
        "notes": "Note",
        "see_x_and_y": "Vedi {} e {}.",
        "version": "Versione",
        "whats_new_in": "Novità in {}",
        "unreleased_note": "Questo mazzo non è ancora stato rilasciato ed è in fase di sviluppo.",
    },
    "pt_pt": {
        "to": "para",
        "words": "palavras",
        "minimal_pairs": "pares mínimos",
        "download_deck": "Baixar baralho",
        "installation_instructions": "Instruções de instalação",
        "learning_tips": "Dicas de aprendizagem",
        "screenshots": "Capturas de tela",
        "changelog": "Registro de alterações",
        "notes": "Notas",
        "see_x_and_y": "Ver {} e {}.",
        "version": "Versão",
        "whats_new_in": "Novidades em {}",
        "unreleased_note": "Este baralho ainda não foi lançado e está em desenvolvimento.",
    },
}

# Card type names for each locale
CARD_TYPES: Dict[str, Dict[str, str]] = {
    "de_de": {
        "listening": "Hörverständnis",
        "pronunciation": "Aussprache",
        "reading": "Leseverständnis",
        "spelling": "Rechtschreibung",
    },
    "en_us": {
        "listening": "Listening",
        "pronunciation": "Pronunciation",
        "reading": "Reading",
        "spelling": "Spelling",
    },
    "es_es": {
        "listening": "Comprensión oral",
        "pronunciation": "Pronunciación",
        "reading": "Comprensión escrita",
        "spelling": "Ortografía",
    },
    "fr_fr": {
        "listening": "Compréhension orale",
        "pronunciation": "Prononciation",
        "reading": "Compréhension écrite",
        "spelling": "Orthographe",
    },
    "it_it": {
        "listening": "Ascolto",
        "pronunciation": "Pronuncia",
        "reading": "Lettura",
        "spelling": "Ortografia",
    },
    "pt_pt": {
        "listening": "Compreensão oral",
        "pronunciation": "Pronúncia",
        "reading": "Compreensão escrita",
        "spelling": "Ortografia",
    },
}


def get_language_name(locale: str, target_locale: str) -> str:
    """Get the name of target language in the source language.

    Args:
        locale: Source language locale (e.g., "en_us")
        target_locale: Target language locale (e.g., "es_es")

    Returns:
        Language name in source language (e.g., "Spanish" for en_us -> es_es)
    """
    if locale not in LANGUAGE_NAMES:
        # Fallback to English
        locale = "en_us"

    return LANGUAGE_NAMES[locale].get(target_locale, target_locale)


def get_ui_string(locale: str, key: str, *args) -> str:
    """Get a UI string in the specified locale.

    Args:
        locale: Language locale (e.g., "en_us")
        key: UI string key (e.g., "download_deck")
        *args: Format arguments for strings with placeholders

    Returns:
        Localized UI string
    """
    if locale not in UI_STRINGS:
        # Fallback to English
        locale = "en_us"

    string = UI_STRINGS[locale].get(key, key)

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
    if locale not in CARD_TYPES:
        # Fallback to English
        locale = "en_us"

    return CARD_TYPES[locale].get(card_type, card_type.capitalize())


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
