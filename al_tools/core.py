from enum import Enum
from pathlib import Path
import random
import time
from typing import List, Tuple, Dict, Set
import unicodedata
import csv
import sqlite3
from datetime import datetime
import sys

import pandas as pd
import os
import re

from google.cloud import texttospeech as tts
import xlsxwriter


def _ensure_db_exists(db_path: Path, data_dir: Path = Path("src/data")):
    """Check if database exists, create automatically from CSV if not."""
    if not db_path.exists():
        print(f"Database '{db_path}' not found.")
        print(f"Creating database from CSV files in '{data_dir}'...")
        csv2sqlite(data_dir, db_path, force=True)
        print(f"Database created successfully at '{db_path}'.")


def _check_db_freshness(db_path: Path, data_dir: Path, force: bool = False):
    """Check if database is up to date with CSV files."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM _meta WHERE key = 'import_timestamp'")
    result = cursor.fetchone()
    conn.close()

    if not result:
        print("Warning: Database has no import timestamp.")
        return

    import_time = datetime.fromisoformat(result[0])

    # Check all CSV files
    csv_files = list(data_dir.glob("*.csv"))
    for csv_file in csv_files:
        mtime = datetime.fromtimestamp(csv_file.stat().st_mtime)
        if mtime > import_time:
            if force:
                return

            print("━" * 70)
            print("⚠️  DATABASE OUT OF DATE")
            print("━" * 70)
            print(f"CSV files in '{data_dir}' have been modified since the database")
            print(f"'{db_path}' was last updated.")
            print()
            print("What would you like to do?")
            print()
            print("  [o] Overwrite - Regenerate database from CSV files")
            print(
                "  [i] Ignore    - Continue with the current database (may be inconsistent)"
            )
            print("  [c] Cancel    - Exit to fix manually (default)")
            print()

            response = input("Enter your choice [o/i/c] (default: c): ").strip().lower()

            if response == "o" or response == "overwrite":
                print(f"Regenerating database from '{data_dir}'...")
                csv2sqlite(data_dir, db_path, force=True)
                print(f"Database successfully updated at '{db_path}'.")
                return
            elif response == "i" or response == "ignore":
                print("⚠️  Proceeding with potentially out-of-date database.")
                return
            else:
                print("Operation cancelled. Update manually with:")
                print(f"  uv run al-tools csv2sqlite -i {data_dir} -d {db_path}")
                sys.exit(1)


class AudioExistsAction(Enum):
    SKIP = "skip"
    OVERWRITE = "overwrite"
    RAISE = "raise"


def _remove_diacritics(s: str) -> str:
    # Convert fancy characters to their most basic form and then split up all
    # combining parts.
    decomposed = unicodedata.normalize("NFKD", s)

    # Keep only the base characters, except if the combining ones are their own
    # letters (Mc) (which do not occur in European languages).
    return "".join(x for x in decomposed if unicodedata.category(x) not in ["Mn", "Me"])


def create_mp3_filename(text: str, prefix: str = "") -> str:
    """
    Create a valid filename for the given text.
    """
    clean_name = text

    clean_name = _remove_diacritics(clean_name)
    clean_name = clean_name.lower()
    clean_name = re.sub(r"[^a-z0-9]+", "_", clean_name)
    clean_name = clean_name.strip("_")

    if not clean_name:
        raise ValueError(f"Invalid text '{text}'")
    return f"{prefix}{clean_name}.mp3"


def _get_text_col(df: pd.DataFrame) -> str:
    """
    Get the text column from the DataFrame.
    """
    text_columns = []
    for column in df.columns:
        if column == "text":
            text_columns.append(column)
        elif column.startswith("text:"):
            text_columns.append(column)

    if len(text_columns) != 1:
        raise ValueError(f"Expected one text column, found {text_columns}")

    return text_columns[0]


def _get_audio_col(df: pd.DataFrame) -> str:
    """
    Get the audio column from the DataFrame.
    """
    audio_columns = []
    for column in df.columns:
        if column == "audio":
            audio_columns.append(column)
        elif column.startswith("audio:"):
            audio_columns.append(column)

    if len(audio_columns) != 1:
        raise ValueError(f"Expected one audio column, found {audio_columns}")

    return audio_columns[0]


def _get_audio_source_col(df: pd.DataFrame) -> str:
    """
    Get the audio source column from the DataFrame.
    """
    audio_source_columns = []
    for column in df.columns:
        if column == "audio source":
            audio_source_columns.append(column)
        elif column.startswith("audio source:"):
            audio_source_columns.append(column)

    if len(audio_source_columns) != 1:
        raise ValueError(
            f"Expected one audio source column, found {audio_source_columns}"
        )

    return audio_source_columns[0]


# See: https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types
_VOICE_MAP = {
    "ar_xa": [
        "ar-XA-Standard-C",
        "ar-XA-Standard-D",
    ],
    "en_gb": [
        "en-GB-Studio-B",
        "en-GB-Studio-C",
    ],
    "en_us": [
        "en-US-Studio-O",
        "en-US-Studio-Q",
    ],
    "es_es": [
        "es-ES-Studio-C",
        "es-ES-Studio-F",
    ],
    "fa_ir": [
        "Aoede",
        "Achernar",
        "Achird",
    ],
    "fr_fr": [
        "fr-FR-Studio-A",
        "fr-FR-Studio-D",
    ],
    # No Italian studio voices exist as of Jan 2025
    "it_it": [
        "it-IT-Journey-D",
        "it-IT-Journey-F",
        "it-IT-Journey-O",
    ],
    "de_de": [
        "de-DE-Studio-B",
        "de-DE-Studio-C",
    ],
    # No Portuguese studio voices exist as of Jan 2025
    "pt_pt": [
        "pt-PT-Standard-D",
        "pt-PT-Standard-F",
    ],
    "sq_al": [
        "Achernar",
        "Achird",
    ],
}


def generate_audio(
    db_path: Path,
    locale: str,
    audio_folder_path: Path,
    audio_exists_action: AudioExistsAction,
    data_dir: Path = Path("src/data"),
    seed: int = 42,
    limit: int = None,
):
    """
    Generate audio via the Google Cloud TTS API.
    Reads from SQLite database and updates it with generated audio.
    If the directory does not exist it will be created.

    Args:
        limit: Maximum number of audio files to generate. None means no limit.
    """
    _ensure_db_exists(db_path, data_dir)
    _check_db_freshness(db_path, data_dir)

    random.seed(seed)
    lang_short = locale.split("_")[0]

    # Read from SQLite
    conn = sqlite3.connect(db_path)
    query = """
        SELECT
            bl.key,
            bl.text,
            bl.audio,
            bl.audio_source,
            COALESCE(tts.tts_text, bl.text) as tts_text,
            COALESCE(tts.is_ssml, 0) as is_ssml
        FROM base_language bl
        LEFT JOIN tts_overrides tts ON bl.key = tts.key AND bl.locale = tts.locale
        WHERE bl.locale = ?
        ORDER BY bl.key COLLATE NOCASE
    """
    df = pd.read_sql_query(query, conn, params=(locale,))

    # Rename columns to match expected format
    df = df.rename(
        columns={
            "text": f"text:{lang_short}",
            "audio": f"audio:{lang_short}",
            "audio_source": f"audio source:{lang_short}",
        }
    )

    os.makedirs(audio_folder_path, exist_ok=True)

    text_col = _get_text_col(df)
    audio_col = _get_audio_col(df)
    audio_source_col = _get_audio_source_col(df)

    client = tts.TextToSpeechClient()
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3)

    cursor = conn.cursor()
    generated_count = 0
    try:
        for rowindex, row in df.iterrows():
            # Check if we've reached the limit
            if limit is not None and generated_count >= limit:
                print(f"\nReached limit of {limit} audio files. Stopping.")
                break

            # Skip rows with empty text
            if pd.isna(row[text_col]) or not row[text_col]:
                print(f"Skipping row with key '{row['key']}' - empty text")
                continue

            if pd.notna(row[audio_col]) and row[audio_col]:
                audio_file = audio_folder_path / re.search(
                    r"\[sound:(.+)\]", row[audio_col]
                ).group(1)
            else:
                audio_file = audio_folder_path / create_mp3_filename(
                    row["key"], prefix=f"al_{locale}_"
                )
            if audio_file.exists():
                if audio_exists_action == AudioExistsAction.SKIP:
                    print(f"Skipping existing audio file '{audio_file}'")
                    if pd.isna(row[audio_col]):
                        df.at[rowindex, audio_col] = f"[sound:{audio_file.name}]"
                        # find the source of that audio
                        audio_source = df[
                            df[audio_col] == f"[sound:{audio_file.name}]"
                        ][audio_source_col].values[0]
                        df.at[rowindex, audio_source_col] = audio_source
                        print(
                            f"  ** Setting audio of '{row[text_col]}' to '{audio_file.name}'"
                        )
                    continue
                elif audio_exists_action == AudioExistsAction.OVERWRITE:
                    print(f"Overwriting existing audio file '{audio_file}'")
                    os.remove(audio_file)
                else:
                    raise FileExistsError(f"Audio file {audio_file} already exists")

            voice_name = random.choice(_VOICE_MAP[locale])
            if locale in ("sq_al", "fa_ir"):
                voice = tts.VoiceSelectionParams(
                    language_code=f"{locale.split('_')[0]}-{locale.split('_')[1].upper()}",
                    name=voice_name,
                    model_name="gemini-2.5-pro-tts",
                )
            else:
                voice = tts.VoiceSelectionParams(
                    language_code=f"{locale.split('_')[0]}-{locale.split('_')[1].upper()}",
                    name=voice_name,
                )

            # Use TTS override if available, otherwise use regular text
            tts_text = row["tts_text"]
            is_ssml = row["is_ssml"]

            if is_ssml:
                synthesis_input = tts.SynthesisInput(ssml=tts_text)
            else:
                synthesis_input = tts.SynthesisInput(text=tts_text)

            # Avoid rate limit
            time.sleep(1)

            try:
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config,
                )
            except Exception as e:
                raise Exception(
                    f"Error for '{row[text_col]}' (TTS text: '{tts_text}'): {e}"
                ) from e
            audio_file.write_bytes(response.audio_content)
            df.at[rowindex, audio_col] = f"[sound:{audio_file.name}]"
            df.at[rowindex, audio_source_col] = (
                f"Google Cloud TTS<br>Voice: {voice_name}"
            )
            print(f"Audio content written to file '{audio_file}'")

            # Update SQLite immediately after successful generation
            cursor.execute(
                """
                UPDATE base_language
                SET audio = ?, audio_source = ?
                WHERE key = ? AND locale = ?
                """,
                (
                    df.at[rowindex, audio_col] or "",
                    df.at[rowindex, audio_source_col] or "",
                    row["key"],
                    locale,
                ),
            )
            conn.commit()
            generated_count += 1

        print(f"\nGenerated {generated_count} audio file(s).")
    finally:
        conn.close()


def _format_source(picture_source, audio_source):
    picture_part = (
        f"Picture:<br>{picture_source}"
        if pd.notna(picture_source) and picture_source != ""
        else ""
    )
    audio_part = (
        f"Audio:<br>{audio_source}"
        if pd.notna(audio_source) and audio_source != ""
        else ""
    )
    separator = "<br><br>" if picture_part and audio_part else ""
    return f"{picture_part}{separator}{audio_part}"


def fix_625_words_files(folder_path: Path):
    """
    Verify all files contain the same keys and add missing words.
    """
    # Verify the "key" column is the same in all files. If the only difference is that some files have
    # more keys than others, add the missing keys to the files that are missing them.
    # Maintain the order of the keys in all files. If the order is different, raise an error.
    keys: pd.DataSeries = None
    file_most_keys = None

    # First figure out which files has the most keys
    for csv_path in folder_path.glob("625_words-base-*.csv"):
        df = pd.read_csv(csv_path, sep=",")
        # If keys are non-unique, raise an error
        if df["key"].duplicated().any():
            raise ValueError(
                f"Duplicate keys found in '{csv_path.name}': {df[df['key'].duplicated()]}"
            )
        if keys is None:
            keys = df["key"]
            file_most_keys = csv_path
        elif len(keys) < len(df["key"]):
            keys = df["key"]
            file_most_keys = csv_path

    for csv_path in folder_path.glob("625_words-base-*.csv"):
        df = pd.read_csv(csv_path, sep=",")
        if not keys.equals(df["key"]):
            # Check if the keys are the same but in a different order
            if (
                keys.sort_values()
                .reset_index(drop=True)
                .equals(df["key"].sort_values().reset_index(drop=True))
            ):
                raise ValueError(
                    f"Keys in '{csv_path}' are in a different order than in '{file_most_keys}'"
                )
            # Add missing keys in the same order as the original keys
            missing_keys = keys[~keys.isin(df["key"])]
            df = pd.concat([df, pd.DataFrame({"key": missing_keys})], ignore_index=True)

        # Ensure that "tags:*" is set, for example tags:fr should be set to AnkiLangs::FR
        for column in df.columns:
            if column.startswith("tags:"):
                df[column] = "AnkiLangs::" + column.split(":")[1].upper()
        df.to_csv(csv_path, index=False)

    # Add all keys to the from-to files
    for csv_path in folder_path.glob("625_words-from-*-to-*.csv"):
        df = pd.read_csv(csv_path, sep=",")
        if not keys.equals(df["key"]):
            # Check if the keys are the same but in a different order
            if (
                keys.sort_values()
                .reset_index(drop=True)
                .equals(df["key"].sort_values().reset_index(drop=True))
            ):
                raise ValueError(
                    f"Keys in '{csv_path}' are in a different order than in '{file_most_keys}'"
                )
            missing_keys = keys[~keys.isin(df["key"])]
            df = pd.concat([df, pd.DataFrame({"key": missing_keys})], ignore_index=True)
        df.to_csv(csv_path, index=False)


def ensure_base_language_entries_exist(
    db_path: Path, data_dir: Path = Path("src/data")
):
    """
    Ensure all vocabulary keys have entries in all base_language locales.

    This is needed when a new deck is created with minimal entries - we want
    to ensure all 625 keys exist in every language's base file, even if the
    translations are empty.

    Updates both the database AND CSV files.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all vocabulary keys
    cursor.execute("SELECT key FROM vocabulary ORDER BY key COLLATE NOCASE")
    all_keys = [row[0] for row in cursor.fetchall()]

    if not all_keys:
        print("No vocabulary keys found")
        conn.close()
        return

    # Find all base language files
    base_locales = set()
    for csv_file in sorted(data_dir.glob("625_words-base-*.csv")):
        locale = csv_file.stem.split("-")[-1]
        base_locales.add(locale)

    if not base_locales:
        print("No base language files found")
        conn.close()
        return

    total_created = 0
    for locale in sorted(base_locales):
        lang_short = locale.split("_")[0]

        # Find missing keys for this locale
        cursor.execute(
            """
            SELECT v.key
            FROM vocabulary v
            WHERE NOT EXISTS (
                SELECT 1 FROM base_language bl
                WHERE bl.key = v.key AND bl.locale = ?
            )
            ORDER BY v.key COLLATE NOCASE
        """,
            (locale,),
        )

        missing_keys = [row[0] for row in cursor.fetchall()]

        if missing_keys:
            # Insert missing entries in database
            for key in missing_keys:
                cursor.execute(
                    """
                    INSERT INTO base_language
                    (key, locale, text, ipa, audio, audio_source)
                    VALUES (?, ?, '', '', '', '')
                """,
                    (key, locale),
                )

            conn.commit()

            # Update CSV file
            csv_file = data_dir / f"625_words-base-{locale}.csv"

            # Read existing CSV data
            existing_rows = []
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                existing_rows = list(reader)

            # Add missing keys
            for key in missing_keys:
                existing_rows.append(
                    {
                        "key": key,
                        f"text:{lang_short}": "",
                        f"ipa:{lang_short}": "",
                        f"audio:{lang_short}": "",
                        f"audio source:{lang_short}": "",
                        f"tags:{lang_short}": f"AnkiLangs::{lang_short.upper()}",
                    }
                )

            # Sort by key (case-insensitive)
            existing_rows.sort(key=lambda row: (row["key"].lower(), row["key"]))

            # Write back to CSV
            with open(csv_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
                writer.writeheader()
                writer.writerows(existing_rows)

            total_created += len(missing_keys)
            print(
                f"Created {len(missing_keys)} missing base language entries for {locale}"
            )

    conn.close()

    if total_created > 0:
        print(f"Total: Created {total_created} base language entries\n")


def ensure_translation_pairs_exist(db_path: Path, data_dir: Path = Path("src/data")):
    """
    Ensure all translation pair entries exist for vocabulary keys that are
    present in both source and target base_language tables.

    This is needed when a new deck is created with minimal entries - we want
    to automatically create empty translation pair entries for all vocabulary
    that exists in both languages.

    Updates both the database AND CSV files.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find all translation pair files to determine which language pairs should exist
    translation_pairs = set()
    for csv_file in sorted(data_dir.glob("625_words-from-*-to-*.csv")):
        match = re.match(r"625_words-from-(.+)-to-(.+)\.csv", csv_file.name)
        if match:
            source_locale, target_locale = match.groups()
            translation_pairs.add((source_locale, target_locale))

    if not translation_pairs:
        print("No translation pair files found, skipping translation pair generation")
        conn.close()
        return

    total_created = 0
    for source_locale, target_locale in sorted(translation_pairs):
        # Find all vocabulary keys that exist in both source and target languages
        cursor.execute(
            """
            SELECT DISTINCT v.key
            FROM vocabulary v
            WHERE EXISTS (
                SELECT 1 FROM base_language bl1
                WHERE bl1.key = v.key AND bl1.locale = ?
            )
            AND EXISTS (
                SELECT 1 FROM base_language bl2
                WHERE bl2.key = v.key AND bl2.locale = ?
            )
            AND NOT EXISTS (
                SELECT 1 FROM translation_pair tp
                WHERE tp.key = v.key
                  AND tp.source_locale = ?
                  AND tp.target_locale = ?
            )
            ORDER BY v.key COLLATE NOCASE
        """,
            (source_locale, target_locale, source_locale, target_locale),
        )

        missing_keys = [row[0] for row in cursor.fetchall()]

        if missing_keys:
            # Insert missing translation pairs in database with empty hints
            for key in missing_keys:
                cursor.execute(
                    """
                    INSERT INTO translation_pair
                    (key, source_locale, target_locale, guid, pronunciation_hint,
                     spelling_hint, reading_hint, listening_hint, notes)
                    VALUES (?, ?, ?, '', '', '', '', '', '')
                """,
                    (key, source_locale, target_locale),
                )

            conn.commit()

            # Also update the CSV file immediately
            csv_file = (
                data_dir / f"625_words-from-{source_locale}-to-{target_locale}.csv"
            )

            # Read existing CSV data
            existing_rows = []
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                existing_rows = list(reader)

            # Add missing keys
            for key in missing_keys:
                existing_rows.append(
                    {
                        "key": key,
                        "guid": "",
                        "pronunciation hint": "",
                        "spelling hint": "",
                        "reading hint": "",
                        "listening hint": "",
                        "notes": "",
                    }
                )

            # Sort by key (case-insensitive)
            existing_rows.sort(key=lambda row: (row["key"].lower(), row["key"]))

            # Write back to CSV
            with open(csv_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
                writer.writeheader()
                writer.writerows(existing_rows)

            total_created += len(missing_keys)
            print(
                f"Created {len(missing_keys)} missing translation pair entries for {source_locale} → {target_locale}"
            )

    conn.close()

    if total_created > 0:
        print(f"\nTotal: Created {total_created} translation pair entries")


def generate_joined_source_fields(
    db_path: Path, output_dir: Path, data_dir: Path = Path("src/data")
):
    """
    Generate CSV files that contain the joint source and license information
    from the SQLite database.

    Also ensures all vocabulary keys exist in all base language files and
    all translation pair files before generating.
    """
    _ensure_db_exists(db_path, data_dir)
    _check_db_freshness(db_path, data_dir)

    # First ensure all base language entries exist
    ensure_base_language_entries_exist(db_path, data_dir)

    # Then ensure all translation pairs exist
    ensure_translation_pairs_exist(db_path, data_dir)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all locales
    cursor.execute("SELECT DISTINCT locale FROM base_language ORDER BY locale")
    locales = [row[0] for row in cursor.fetchall()]

    os.makedirs(output_dir, exist_ok=True)

    for locale in locales:
        # Get translation pairs that have this locale as target
        cursor.execute(
            "SELECT DISTINCT source_locale FROM translation_pair WHERE target_locale = ? ORDER BY source_locale",
            (locale,),
        )
        source_locales = [row[0] for row in cursor.fetchall()]

        for source_locale in source_locales:
            # Query with joins to get key and source field
            query = """
                SELECT
                    bl.key,
                    CASE
                        WHEN p.picture_source IS NOT NULL AND p.picture_source != ''
                             AND bl.audio_source IS NOT NULL AND bl.audio_source != ''
                        THEN 'Picture:<br>' || p.picture_source || '<br><br>Audio:<br>' || bl.audio_source
                        WHEN p.picture_source IS NOT NULL AND p.picture_source != ''
                        THEN 'Picture:<br>' || p.picture_source
                        WHEN bl.audio_source IS NOT NULL AND bl.audio_source != ''
                        THEN 'Audio:<br>' || bl.audio_source
                        ELSE ''
                    END as source
                FROM base_language bl
                LEFT JOIN pictures p ON bl.key = p.key
                WHERE bl.locale = ?
                ORDER BY bl.key COLLATE NOCASE
            """

            df = pd.read_sql_query(query, conn, params=(locale,))
            df = df[df["source"] != ""]  # Only keep rows with source

            output_file = output_dir / f"625_words-from-{source_locale}-to-{locale}.csv"
            df.to_csv(output_file, index=False, lineterminator="\n")
            print(f"CSV file '{output_file}' written")

    conn.close()


class _AmbiguousWords:
    def __init__(self, filename: str):
        self.filename = filename
        # key is the word, value is a tuple of keys and empty columns
        self.ambiguous_words: Dict[str, Tuple[Tuple, Tuple]] = dict()

    def add(self, word: str, keys: Tuple, empty_columns: Tuple):
        self.ambiguous_words[word] = (keys, empty_columns)

    def __repr__(self):
        return f"{self.filename}: {self.ambiguous_words}"


def _locale_to_directory(locale: str) -> str:
    """Convert database locale (e.g., 'en_us') to directory format (e.g., 'en_US')."""
    lang, country = locale.split("_")
    return f"{lang}_{country.upper()}"


def _parse_audio_filename(audio_ref: str) -> str | None:
    """Parse audio filename from Anki [sound:...] format.

    Args:
        audio_ref: Audio reference in format '[sound:filename.mp3]'

    Returns:
        Filename (e.g., 'al_en_us_alive.mp3') or None if invalid format
    """
    if (
        not audio_ref
        or not audio_ref.startswith("[sound:")
        or not audio_ref.endswith("]")
    ):
        return None
    return audio_ref[7:-1]  # Strip '[sound:' and ']'


def _check_audio_files(
    db_path: Path, media_dir: Path | None = Path("src/media/audio")
) -> str:
    """Check for audio file mismatches between database and disk.

    Checks:
    1. Audio files referenced in DB but not on disk
    2. Audio files on disk but not referenced in DB

    Args:
        db_path: Path to SQLite database
        media_dir: Path to audio media directory (None to skip audio checks)

    Returns:
        Error message string if issues found, empty string otherwise
    """
    # Skip audio checks if media_dir is None (e.g., in tests)
    if media_dir is None:
        return ""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all audio references from base_language table
    cursor.execute("""
        SELECT locale, audio, key
        FROM base_language
        WHERE audio IS NOT NULL AND audio <> ''
        ORDER BY locale, key
    """)
    db_audio_refs = list(cursor.fetchall())

    # Get all audio references from minimal_pairs table
    cursor.execute("""
        SELECT target_locale, audio1, guid || ' (audio1)'
        FROM minimal_pairs
        WHERE audio1 IS NOT NULL AND audio1 <> ''
        UNION ALL
        SELECT target_locale, audio2, guid || ' (audio2)'
        FROM minimal_pairs
        WHERE audio2 IS NOT NULL AND audio2 <> ''
    """)
    db_audio_refs.extend(cursor.fetchall())

    conn.close()

    # Build set of audio files referenced in DB, grouped by locale
    db_files_by_locale: Dict[str, Set[str]] = {}
    missing_on_disk = []

    for locale, audio_ref, key in db_audio_refs:
        filename = _parse_audio_filename(audio_ref)
        if not filename:
            continue

        locale_dir = _locale_to_directory(locale)
        if locale_dir not in db_files_by_locale:
            db_files_by_locale[locale_dir] = set()
        db_files_by_locale[locale_dir].add(filename)

        # Check if file exists on disk
        audio_path = media_dir / locale_dir / filename
        if not audio_path.exists():
            missing_on_disk.append((locale, key, filename))

    # Build set of audio files on disk, grouped by locale
    disk_files_by_locale: Dict[str, Set[str]] = {}
    if media_dir.exists():
        for locale_dir in media_dir.iterdir():
            if not locale_dir.is_dir():
                continue

            locale_name = locale_dir.name
            disk_files_by_locale[locale_name] = set()

            for audio_file in locale_dir.glob("*.mp3"):
                disk_files_by_locale[locale_name].add(audio_file.name)

    # Find files on disk but not in DB
    unreferenced_files = []
    for locale_dir, disk_files in disk_files_by_locale.items():
        db_files = db_files_by_locale.get(locale_dir, set())
        orphaned = disk_files - db_files
        for filename in sorted(orphaned):
            unreferenced_files.append((locale_dir, filename))

    # Build output
    output = ""
    if missing_on_disk:
        output += "AUDIO FILES IN DATABASE BUT NOT ON DISK:\n"
        for locale, key, filename in missing_on_disk:
            locale_dir = _locale_to_directory(locale)
            output += f"  - {locale_dir}/{filename} (key: '{key}')\n"
        output += "\n"

    if unreferenced_files:
        output += "AUDIO FILES ON DISK BUT NOT IN DATABASE:\n"
        for locale_dir, filename in unreferenced_files:
            output += f"  - {locale_dir}/{filename}\n"
        output += "\n"

    return output


def ambiguity_detection(
    db_path: Path,
    data_dir: Path = Path("src/data"),
    media_dir: Path | None = Path("src/media/audio"),
) -> str:
    """
    Detect ambiguous words and duplicate keys in the database.

    Args:
        db_path: Path to SQLite database
        data_dir: Path to CSV data directory
        media_dir: Path to audio media directory (None to skip audio checks)

    Returns:
        Output string with any errors found
    """
    _ensure_db_exists(db_path, data_dir)
    _check_db_freshness(db_path, data_dir)

    output = ""

    # Check for duplicate keys in CSV files
    duplicate_errors = []

    # Check base language files
    for csv_file in sorted(data_dir.glob("625_words-base-*.csv")):
        df = pd.read_csv(csv_file, sep=",")
        if df["key"].duplicated().any():
            duplicates = df[df["key"].duplicated(keep=False)].sort_values("key")
            duplicate_errors.append(
                f"Duplicate keys in '{csv_file.name}':\n"
                + "\n".join(f"  - '{key}'" for key in duplicates["key"].unique())
            )

    # Check translation pair files
    for csv_file in sorted(data_dir.glob("625_words-from-*-to-*.csv")):
        df = pd.read_csv(csv_file, sep=",")
        if df["key"].duplicated().any():
            duplicates = df[df["key"].duplicated(keep=False)].sort_values("key")
            duplicate_errors.append(
                f"Duplicate keys in '{csv_file.name}':\n"
                + "\n".join(f"  - '{key}'" for key in duplicates["key"].unique())
            )

    # Check pictures file
    pictures_file = data_dir / "625_words-pictures.csv"
    if pictures_file.exists():
        df = pd.read_csv(pictures_file, sep=",")
        if df["key"].duplicated().any():
            duplicates = df[df["key"].duplicated(keep=False)].sort_values("key")
            duplicate_errors.append(
                f"Duplicate keys in '{pictures_file.name}':\n"
                + "\n".join(f"  - '{key}'" for key in duplicates["key"].unique())
            )

    # Check tts_overrides file for duplicate (key, locale) pairs
    tts_file = data_dir / "tts_overrides.csv"
    if tts_file.exists():
        df = pd.read_csv(tts_file, sep=",")
        if df[["key", "locale"]].duplicated().any():
            duplicates = df[df[["key", "locale"]].duplicated(keep=False)].sort_values(
                ["key", "locale"]
            )
            duplicate_errors.append(
                f"Duplicate (key, locale) pairs in '{tts_file.name}':\n"
                + "\n".join(
                    f"  - ('{row['key']}', '{row['locale']}')"
                    for _, row in duplicates[["key", "locale"]]
                    .drop_duplicates()
                    .iterrows()
                )
            )

    # Check minimal pairs files for duplicate guids
    for csv_file in sorted(data_dir.glob("minimal_pairs-*.csv")):
        df = pd.read_csv(csv_file, sep=",")
        if "guid" in df.columns and df["guid"].duplicated().any():
            duplicates = df[df["guid"].duplicated(keep=False)].sort_values("guid")
            duplicate_errors.append(
                f"Duplicate GUIDs in '{csv_file.name}':\n"
                + "\n".join(f"  - '{guid}'" for guid in duplicates["guid"].unique())
            )

    if duplicate_errors:
        output += "DUPLICATE KEY ERRORS FOUND:\n"
        output += "\n\n".join(duplicate_errors)
        output += "\n\n"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all translation pairs
    cursor.execute("""
        SELECT DISTINCT source_locale, target_locale
        FROM translation_pair
        ORDER BY source_locale, target_locale
    """)
    pairs = cursor.fetchall()

    aw_list: List[_AmbiguousWords] = []

    for source_locale, target_locale in pairs:
        filename = f"625_words-from-{source_locale}-to-{target_locale}.csv"
        aw_obj = _AmbiguousWords(filename)

        # Find duplicate source texts
        cursor.execute(
            """
            SELECT
                bl_from.text as word,
                GROUP_CONCAT(tp.key) as keys,
                MAX(CASE WHEN tp.pronunciation_hint IS NULL OR tp.pronunciation_hint = '' THEN 1 ELSE 0 END) as missing_pronunciation
            FROM translation_pair tp
            JOIN base_language bl_from ON tp.key = bl_from.key AND bl_from.locale = tp.source_locale
            WHERE tp.source_locale = ? AND tp.target_locale = ?
                AND bl_from.text IS NOT NULL AND bl_from.text != ''
            GROUP BY bl_from.text
            HAVING COUNT(*) > 1
        """,
            (source_locale, target_locale),
        )

        for row in cursor.fetchall():
            word, keys_str, missing_pronunciation = row
            keys = tuple(keys_str.split(","))
            columns = []

            # Check if all rows are missing the hints (all must be missing)
            if missing_pronunciation:
                # Verify all rows have missing pronunciation hint
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM translation_pair
                    WHERE key IN ({}) AND source_locale = ? AND target_locale = ?
                        AND (pronunciation_hint IS NULL OR pronunciation_hint = '')
                """.format(",".join("?" * len(keys))),
                    (*keys, source_locale, target_locale),
                )
                if cursor.fetchone()[0] == len(keys):
                    columns.append("pronunciation hint")

            # Note: spelling hints are rarely needed (only for target language
            # homophones with ambiguous source meanings), so we don't check for them

            if columns:
                aw_obj.add(word, keys, tuple(columns))

        # Find duplicate target texts
        cursor.execute(
            """
            SELECT
                bl_to.text as word,
                GROUP_CONCAT(tp.key) as keys,
                MAX(CASE WHEN tp.reading_hint IS NULL OR tp.reading_hint = '' THEN 1 ELSE 0 END) as missing_reading,
                MAX(CASE WHEN tp.listening_hint IS NULL OR tp.listening_hint = '' THEN 1 ELSE 0 END) as missing_listening
            FROM translation_pair tp
            JOIN base_language bl_to ON tp.key = bl_to.key AND bl_to.locale = tp.target_locale
            WHERE tp.source_locale = ? AND tp.target_locale = ?
                AND bl_to.text IS NOT NULL AND bl_to.text != ''
            GROUP BY bl_to.text
            HAVING COUNT(*) > 1
        """,
            (source_locale, target_locale),
        )

        for row in cursor.fetchall():
            word, keys_str, missing_reading, missing_listening = row
            keys = tuple(keys_str.split(","))
            columns = []

            if missing_reading:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM translation_pair
                    WHERE key IN ({}) AND source_locale = ? AND target_locale = ?
                        AND (reading_hint IS NULL OR reading_hint = '')
                """.format(",".join("?" * len(keys))),
                    (*keys, source_locale, target_locale),
                )
                if cursor.fetchone()[0] == len(keys):
                    columns.append("reading hint")

            if missing_listening:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM translation_pair
                    WHERE key IN ({}) AND source_locale = ? AND target_locale = ?
                        AND (listening_hint IS NULL OR listening_hint = '')
                """.format(",".join("?" * len(keys))),
                    (*keys, source_locale, target_locale),
                )
                if cursor.fetchone()[0] == len(keys):
                    columns.append("listening hint")

            if columns:
                aw_obj.add(word, keys, tuple(columns))

        aw_list.append(aw_obj)

    conn.close()

    for aw_obj in aw_list:
        if aw_obj.ambiguous_words:
            output += f"The following ambiguous words were found in the file '{aw_obj.filename}':\n"
            for word, (keys, empty_columns) in aw_obj.ambiguous_words.items():
                output += f"  - '{word}' has the key(s) {keys} and missing column(s) {empty_columns}\n"

    # Check audio files
    audio_output = _check_audio_files(db_path, media_dir)
    output += audio_output

    return output


def sort_csv_files(data_dir: Path):
    """Sort all CSV files alphabetically by first column (key or guid), case-insensitive."""
    csv_files = sorted(data_dir.glob("*.csv"))

    for csv_file in csv_files:
        with open(csv_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)

        if not rows:
            continue

        first_col = fieldnames[0]
        rows.sort(key=lambda row: (row[first_col].lower(), row[first_col]))

        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

        print(f"Sorted {csv_file.name} ({len(rows)} rows)")


def csv2sqlite(data_dir: Path, db_path: Path, force: bool = False):
    """Import all CSV files from data_dir into SQLite database."""
    # Check if database already exists and warn user
    if db_path.exists() and not force:
        response = input(
            f"Warning: Database '{db_path}' already exists and will be overwritten.\n"
            "All data will be replaced with CSV contents. Continue? (y/n): "
        )
        if response.lower() != "y":
            print("Aborting import.")
            sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            key TEXT PRIMARY KEY
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS base_language (
            key TEXT NOT NULL,
            locale TEXT NOT NULL,
            text TEXT,
            ipa TEXT,
            audio TEXT,
            audio_source TEXT,
            PRIMARY KEY (key, locale),
            FOREIGN KEY (key) REFERENCES vocabulary(key)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS translation_pair (
            key TEXT NOT NULL,
            source_locale TEXT NOT NULL,
            target_locale TEXT NOT NULL,
            guid TEXT,
            pronunciation_hint TEXT,
            spelling_hint TEXT,
            reading_hint TEXT,
            listening_hint TEXT,
            notes TEXT,
            PRIMARY KEY (key, source_locale, target_locale),
            FOREIGN KEY (key) REFERENCES vocabulary(key)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pictures (
            key TEXT PRIMARY KEY,
            picture TEXT,
            picture_source TEXT,
            FOREIGN KEY (key) REFERENCES vocabulary(key)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS minimal_pairs (
            guid TEXT PRIMARY KEY,
            source_locale TEXT NOT NULL,
            target_locale TEXT NOT NULL,
            text1 TEXT,
            audio1 TEXT,
            ipa1 TEXT,
            meaning1 TEXT,
            text2 TEXT,
            audio2 TEXT,
            ipa2 TEXT,
            meaning2 TEXT,
            tags TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tts_overrides (
            key TEXT NOT NULL,
            locale TEXT NOT NULL,
            tts_text TEXT NOT NULL,
            is_ssml BOOLEAN DEFAULT 0,
            notes TEXT,
            PRIMARY KEY (key, locale),
            FOREIGN KEY (key) REFERENCES vocabulary(key)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS _meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Clear existing data for idempotency
    cursor.execute("DELETE FROM base_language")
    cursor.execute("DELETE FROM translation_pair")
    cursor.execute("DELETE FROM pictures")
    cursor.execute("DELETE FROM minimal_pairs")
    cursor.execute("DELETE FROM tts_overrides")
    cursor.execute("DELETE FROM vocabulary")
    cursor.execute("DELETE FROM _meta")

    # Import base language files
    for csv_file in sorted(data_dir.glob("625_words-base-*.csv")):
        locale = csv_file.stem.split("-")[-1]
        lang_short = locale.split("_")[0]

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row["key"]
                cursor.execute(
                    "INSERT OR IGNORE INTO vocabulary (key) VALUES (?)", (key,)
                )
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO base_language
                    (key, locale, text, ipa, audio, audio_source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        key,
                        locale,
                        row.get(f"text:{lang_short}", ""),
                        row.get(f"ipa:{lang_short}", ""),
                        row.get(f"audio:{lang_short}", ""),
                        row.get(f"audio source:{lang_short}", ""),
                    ),
                )
        print(f"Imported {csv_file.name}")

    # Import translation pair files
    for csv_file in sorted(data_dir.glob("625_words-from-*-to-*.csv")):
        match = re.match(r"625_words-from-(.+)-to-(.+)\.csv", csv_file.name)
        if match:
            source_locale, target_locale = match.groups()

            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = row["key"]
                    cursor.execute(
                        "INSERT OR IGNORE INTO vocabulary (key) VALUES (?)", (key,)
                    )
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO translation_pair
                        (key, source_locale, target_locale, guid, pronunciation_hint,
                         spelling_hint, reading_hint, listening_hint, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            key,
                            source_locale,
                            target_locale,
                            row.get("guid", ""),
                            row.get("pronunciation hint", ""),
                            row.get("spelling hint", ""),
                            row.get("reading hint", ""),
                            row.get("listening hint", ""),
                            row.get("notes", ""),
                        ),
                    )
            print(f"Imported {csv_file.name}")

    # Import pictures
    pictures_file = data_dir / "625_words-pictures.csv"
    if pictures_file.exists():
        with open(pictures_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row["key"]
                if key:
                    cursor.execute(
                        "INSERT OR IGNORE INTO vocabulary (key) VALUES (?)", (key,)
                    )
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO pictures (key, picture, picture_source)
                        VALUES (?, ?, ?)
                    """,
                        (key, row.get("picture", ""), row.get("picture source", "")),
                    )
        print(f"Imported {pictures_file.name}")

    # Import TTS overrides
    tts_overrides_file = data_dir / "tts_overrides.csv"
    if tts_overrides_file.exists():
        with open(tts_overrides_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get("key", "")
                locale = row.get("locale", "")
                tts_text = row.get("tts_text", "")
                if key and locale and tts_text:
                    cursor.execute(
                        "INSERT OR IGNORE INTO vocabulary (key) VALUES (?)", (key,)
                    )
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO tts_overrides (key, locale, tts_text, is_ssml, notes)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            key,
                            locale,
                            tts_text,
                            1 if row.get("is_ssml", "0") == "1" else 0,
                            row.get("notes", ""),
                        ),
                    )
        print(f"Imported {tts_overrides_file.name}")

    # Import minimal pairs
    for csv_file in sorted(data_dir.glob("minimal_pairs-*.csv")):
        match = re.match(r"minimal_pairs-from-(.+)_to_(.+)\.csv", csv_file.name)
        if match:
            source_locale, target_locale = match.groups()

            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("guid"):
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO minimal_pairs
                            (guid, source_locale, target_locale, text1, audio1, ipa1, meaning1,
                             text2, audio2, ipa2, meaning2, tags)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                row["guid"],
                                source_locale,
                                target_locale,
                                row.get("text1", ""),
                                row.get("audio1", ""),
                                row.get("ipa1", ""),
                                row.get("meaning1", ""),
                                row.get("text2", ""),
                                row.get("audio2", ""),
                                row.get("ipa2", ""),
                                row.get("meaning2", ""),
                                row.get("tags", ""),
                            ),
                        )
            print(f"Imported {csv_file.name}")

    # Save metadata
    cursor.execute(
        "INSERT OR REPLACE INTO _meta (key, value) VALUES (?, ?)",
        ("import_timestamp", datetime.now().isoformat()),
    )

    conn.commit()
    conn.close()
    print(f"\nDatabase saved to {db_path}")


def sqlite2csv(db_path: Path, data_dir: Path):
    """Export SQLite database back to CSV files with deterministic formatting."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Get all locales
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT locale FROM base_language ORDER BY locale")
    locales = [row["locale"] for row in cursor.fetchall()]

    # Export base language files
    for locale in locales:
        lang_short = locale.split("_")[0]
        cursor.execute(
            """
            SELECT key, text, ipa, audio, audio_source
            FROM base_language
            WHERE locale = ?
            ORDER BY key COLLATE NOCASE
        """,
            (locale,),
        )

        rows = cursor.fetchall()
        fieldnames = [
            "key",
            f"text:{lang_short}",
            f"ipa:{lang_short}",
            f"audio:{lang_short}",
            f"audio source:{lang_short}",
            f"tags:{lang_short}",
        ]

        csv_file = data_dir / f"625_words-base-{locale}.csv"
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "key": row["key"],
                        f"text:{lang_short}": row["text"] or "",
                        f"ipa:{lang_short}": row["ipa"] or "",
                        f"audio:{lang_short}": row["audio"] or "",
                        f"audio source:{lang_short}": row["audio_source"] or "",
                        f"tags:{lang_short}": f"AnkiLangs::{lang_short.upper()}",
                    }
                )
        print(f"Exported {csv_file.name} ({len(rows)} rows)")

    # Export translation pair files
    cursor.execute("""
        SELECT DISTINCT source_locale, target_locale
        FROM translation_pair
        ORDER BY source_locale, target_locale
    """)
    pairs = cursor.fetchall()

    for pair in pairs:
        source_locale = pair["source_locale"]
        target_locale = pair["target_locale"]

        cursor.execute(
            """
            SELECT key, guid, pronunciation_hint, spelling_hint, reading_hint,
                   listening_hint, notes
            FROM translation_pair
            WHERE source_locale = ? AND target_locale = ?
            ORDER BY key COLLATE NOCASE
        """,
            (source_locale, target_locale),
        )

        rows = cursor.fetchall()
        fieldnames = [
            "key",
            "guid",
            "pronunciation hint",
            "spelling hint",
            "reading hint",
            "listening hint",
            "notes",
        ]

        csv_file = data_dir / f"625_words-from-{source_locale}-to-{target_locale}.csv"
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "key": row["key"],
                        "guid": row["guid"] or "",
                        "pronunciation hint": row["pronunciation_hint"] or "",
                        "spelling hint": row["spelling_hint"] or "",
                        "reading hint": row["reading_hint"] or "",
                        "listening hint": row["listening_hint"] or "",
                        "notes": row["notes"] or "",
                    }
                )
        print(f"Exported {csv_file.name} ({len(rows)} rows)")

    # Export pictures
    cursor.execute(
        "SELECT key, picture, picture_source FROM pictures ORDER BY key COLLATE NOCASE"
    )
    rows = cursor.fetchall()

    csv_file = data_dir / "625_words-pictures.csv"
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["key", "picture", "picture source"], lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "key": row["key"],
                    "picture": row["picture"] or "",
                    "picture source": row["picture_source"] or "",
                }
            )
    print(f"Exported {csv_file.name} ({len(rows)} rows)")

    # Export TTS overrides
    cursor.execute(
        "SELECT key, locale, tts_text, is_ssml, notes FROM tts_overrides ORDER BY key COLLATE NOCASE, locale"
    )
    rows = cursor.fetchall()

    csv_file = data_dir / "tts_overrides.csv"
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["key", "locale", "tts_text", "is_ssml", "notes"],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "key": row["key"],
                    "locale": row["locale"],
                    "tts_text": row["tts_text"] or "",
                    "is_ssml": "1" if row["is_ssml"] else "0",
                    "notes": row["notes"] or "",
                }
            )
    print(f"Exported {csv_file.name} ({len(rows)} rows)")

    # Export minimal pairs
    cursor.execute("""
        SELECT DISTINCT source_locale, target_locale
        FROM minimal_pairs
        ORDER BY source_locale, target_locale
    """)
    mp_pairs = cursor.fetchall()

    for pair in mp_pairs:
        source_locale = pair["source_locale"]
        target_locale = pair["target_locale"]

        cursor.execute(
            """
            SELECT guid, text1, audio1, ipa1, meaning1, text2, audio2, ipa2, meaning2, tags
            FROM minimal_pairs
            WHERE source_locale = ? AND target_locale = ?
            ORDER BY guid COLLATE NOCASE
        """,
            (source_locale, target_locale),
        )

        rows = cursor.fetchall()
        fieldnames = [
            "guid",
            "text1",
            "audio1",
            "ipa1",
            "meaning1",
            "text2",
            "audio2",
            "ipa2",
            "meaning2",
            "tags",
        ]

        csv_file = (
            data_dir / f"minimal_pairs-from-{source_locale}_to_{target_locale}.csv"
        )
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "guid": row["guid"],
                        "text1": row["text1"] or "",
                        "audio1": row["audio1"] or "",
                        "ipa1": row["ipa1"] or "",
                        "meaning1": row["meaning1"] or "",
                        "text2": row["text2"] or "",
                        "audio2": row["audio2"] or "",
                        "ipa2": row["ipa2"] or "",
                        "meaning2": row["meaning2"] or "",
                        "tags": row["tags"] or "",
                    }
                )
        print(f"Exported {csv_file.name} ({len(rows)} rows)")

    # Update timestamp to reflect that DB and CSV files are now in sync
    cursor.execute(
        "INSERT OR REPLACE INTO _meta (key, value) VALUES (?, ?)",
        ("import_timestamp", datetime.now().isoformat()),
    )
    conn.commit()

    conn.close()
    print(f"\nAll files exported from {db_path}")


def _create_excel_review_file(
    excel_file: Path,
    rows: List,
    fieldnames: List[str],
):
    """Create an Excel file for review with formatting and protection.

    Features:
    - Frozen header row
    - Auto-filter on all columns
    - Hidden GUID column
    - Alternating row colors
    - GUID and source_text columns are protected (non-editable)

    Args:
        excel_file: Path to output Excel file
        rows: List of row data from database
        fieldnames: List of column names
    """
    # Create workbook and worksheet
    workbook = xlsxwriter.Workbook(str(excel_file))
    worksheet = workbook.add_worksheet("Review")

    # Define formats
    header_format = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#4472C4",
            "font_color": "white",
            "align": "left",
            "valign": "vcenter",
            "border": 1,
            "locked": True,
        }
    )

    # Alternating row formats for locked columns (guid, source_text)
    locked_even = workbook.add_format(
        {
            "bg_color": "#F2F2F2",
            "border": 1,
            "locked": True,
            "align": "left",
            "valign": "top",
        }
    )

    locked_odd = workbook.add_format(
        {
            "bg_color": "#FFFFFF",
            "border": 1,
            "locked": True,
            "align": "left",
            "valign": "top",
        }
    )

    # Alternating row formats for unlocked columns (editable)
    unlocked_even = workbook.add_format(
        {
            "bg_color": "#F2F2F2",
            "border": 1,
            "locked": False,
            "align": "left",
            "valign": "top",
        }
    )

    unlocked_odd = workbook.add_format(
        {
            "bg_color": "#FFFFFF",
            "border": 1,
            "locked": False,
            "align": "left",
            "valign": "top",
        }
    )

    # Empty row format (no background color, unlocked)
    empty_format = workbook.add_format(
        {
            "locked": False,
        }
    )

    # Write header row
    for col_idx, field in enumerate(fieldnames):
        worksheet.write(0, col_idx, field, header_format)

    # Write data rows with alternating colors and empty rows every 10 entries
    current_row = 1
    for idx, row in enumerate(rows, start=1):
        # Determine if this is an alternating row
        is_even = idx % 2 == 0

        # Prepare row data
        row_data = [
            row["guid"] or "",
            row["source_text"] or "",
            row["target_text"] or "",
            row["target_ipa"] or "",
            row["pronunciation_hint"] or "",
            row["spelling_hint"] or "",
            row["reading_hint"] or "",
            row["listening_hint"] or "",
            row["notes"] or "",
            "",  # review_comment
        ]

        # Write row data
        for col_idx, value in enumerate(row_data):
            # First two columns (guid, source_text) are locked, rest are unlocked
            if col_idx < 2:
                cell_format = locked_even if is_even else locked_odd
            else:
                cell_format = unlocked_even if is_even else unlocked_odd

            worksheet.write(current_row, col_idx, value, cell_format)

        current_row += 1

        # Insert empty row every 10 entries (for visual separation)
        if idx % 10 == 0 and idx < len(rows):
            for col_idx in range(len(fieldnames)):
                worksheet.write(current_row, col_idx, "", empty_format)
            current_row += 1

    # Set column widths for better readability
    column_widths = {
        "guid": 10,
        "source_text": 20,
        "target_text": 20,
        "target_ipa": 15,
        "pronunciation_hint": 18,
        "spelling_hint": 18,
        "reading_hint": 18,
        "listening_hint": 18,
        "notes": 25,
        "review_comment": 30,
    }

    for col_idx, field in enumerate(fieldnames):
        width = column_widths.get(field, 15)
        worksheet.set_column(col_idx, col_idx, width)

    # Hide GUID column (column A / index 0)
    worksheet.set_column(0, 0, None, None, {"hidden": True})

    # Freeze header row (freeze panes at row 1)
    worksheet.freeze_panes(1, 0)

    # Add autofilter to all columns
    worksheet.autofilter(0, 0, current_row - 1, len(fieldnames) - 1)

    # Protect worksheet (allows editing unlocked cells and filtering)
    worksheet.protect(
        "",
        {
            "select_locked_cells": True,
            "select_unlocked_cells": True,
            "format_cells": False,
            "format_columns": False,
            "format_rows": False,
            "insert_columns": False,
            "insert_rows": False,
            "insert_hyperlinks": False,
            "delete_columns": False,
            "delete_rows": False,
            "sort": True,
            "autofilter": True,
        },
    )

    # Close workbook
    workbook.close()


def export_review(
    db_path: Path,
    source_locale: str,
    target_locale: str,
    output_dir: Path,
    media_dir: Path = Path("src/media/audio"),
    data_dir: Path = Path("src/data"),
):
    """Export review data for native speakers.

    Creates:
    1. CSV file with translation pairs, hints, and empty review comment column
    2. Excel file with formatting, frozen headers, and column protection
    3. Concatenated audio file with all target language audio sorted alphabetically

    Args:
        db_path: Path to SQLite database
        source_locale: Source locale (e.g., 'en_us')
        target_locale: Target locale (e.g., 'es_es')
        output_dir: Directory to write output files
        media_dir: Directory containing audio files
        data_dir: Directory containing CSV files (for DB freshness check)
    """
    _ensure_db_exists(db_path, data_dir)
    _check_db_freshness(db_path, data_dir, force=False)

    output_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query translation pairs with source and target text
    cursor.execute(
        """
        SELECT
            tp.key,
            tp.guid,
            bl_source.text as source_text,
            bl_target.text as target_text,
            bl_target.ipa as target_ipa,
            bl_target.audio as target_audio,
            tp.pronunciation_hint,
            tp.spelling_hint,
            tp.reading_hint,
            tp.listening_hint,
            tp.notes
        FROM translation_pair tp
        JOIN base_language bl_source
            ON tp.key = bl_source.key AND bl_source.locale = tp.source_locale
        JOIN base_language bl_target
            ON tp.key = bl_target.key AND bl_target.locale = tp.target_locale
        WHERE tp.source_locale = ? AND tp.target_locale = ?
        ORDER BY tp.key COLLATE NOCASE
        """,
        (source_locale, target_locale),
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"No translation pairs found for {source_locale} -> {target_locale}")
        return

    # Generate CSV with empty rows every 10 entries
    csv_file = output_dir / f"review_{source_locale}_to_{target_locale}.csv"
    fieldnames = [
        "guid",
        "source_text",
        "target_text",
        "target_ipa",
        "pronunciation_hint",
        "spelling_hint",
        "reading_hint",
        "listening_hint",
        "notes",
        "review_comment",
    ]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()

        for idx, row in enumerate(rows, start=1):
            writer.writerow(
                {
                    "guid": row["guid"] or "",
                    "source_text": row["source_text"] or "",
                    "target_text": row["target_text"] or "",
                    "target_ipa": row["target_ipa"] or "",
                    "pronunciation_hint": row["pronunciation_hint"] or "",
                    "spelling_hint": row["spelling_hint"] or "",
                    "reading_hint": row["reading_hint"] or "",
                    "listening_hint": row["listening_hint"] or "",
                    "notes": row["notes"] or "",
                    "review_comment": "",
                }
            )

            # Insert empty row every 10 entries
            if idx % 10 == 0 and idx < len(rows):
                writer.writerow({field: "" for field in fieldnames})

    print(f"CSV file '{csv_file}' written ({len(rows)} entries)")

    # Generate Excel file with formatting
    excel_file = output_dir / f"review_{source_locale}_to_{target_locale}.xlsx"
    _create_excel_review_file(excel_file, rows, fieldnames)
    print(f"Excel file '{excel_file}' written ({len(rows)} entries)")

    # Concatenate audio files
    # Collect audio file paths sorted alphabetically by key
    audio_files_with_keys = []
    target_locale_dir = _locale_to_directory(target_locale)
    audio_dir = media_dir / target_locale_dir

    if not audio_dir.exists():
        print(
            f"Warning: Audio directory '{audio_dir}' not found. Skipping audio concatenation."
        )
        return

    for row in rows:
        audio_ref = row["target_audio"]
        if not audio_ref:
            continue

        filename = _parse_audio_filename(audio_ref)
        if not filename:
            continue

        audio_path = audio_dir / filename
        if audio_path.exists():
            audio_files_with_keys.append((row["key"], audio_path))
        else:
            print(f"Warning: Audio file '{audio_path}' not found")

    if not audio_files_with_keys:
        print("No audio files found to concatenate")
        return

    # Get audio parameters from first file to ensure compatibility
    import subprocess

    first_audio = audio_files_with_keys[0][1]
    probe_result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=sample_rate,channels",
            "-of",
            "csv=p=0",
            str(first_audio),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    sample_rate, channels = probe_result.stdout.strip().split(",")

    # Create ffmpeg concat file with 5s silence after every 10th entry
    concat_file = output_dir / "concat_list.txt"
    silence_file_5s = output_dir / "silence_5s.mp3"
    silence_file_300ms = output_dir / "silence_300ms.mp3"

    # Generate silence files with same parameters as source files
    subprocess.run(
        [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r={sample_rate}:cl={'stereo' if channels == '2' else 'mono'}",
            "-t",
            "5",
            "-b:a",
            "64k",
            "-acodec",
            "libmp3lame",
            "-y",
            str(silence_file_5s),
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r={sample_rate}:cl={'stereo' if channels == '2' else 'mono'}",
            "-t",
            "300ms",
            "-b:a",
            "64k",
            "-acodec",
            "libmp3lame",
            "-y",
            str(silence_file_300ms),
        ],
        check=True,
        capture_output=True,
    )

    # Write concat file
    with open(concat_file, "w", encoding="utf-8") as f:
        for idx, (key, audio_path) in enumerate(audio_files_with_keys, start=1):
            f.write(f"file '{audio_path.absolute()}'\n")

            # Add 5s silence after every 10th entry
            if idx % 10 == 0 and idx < len(audio_files_with_keys):
                f.write(f"file '{silence_file_5s.absolute()}'\n")
            elif idx < len(audio_files_with_keys):
                f.write(f"file '{silence_file_300ms.absolute()}'\n")

    # Concatenate and re-encode to ensure compatibility
    # Re-encoding prevents issues with files that have slightly different encoding parameters
    output_audio = output_dir / f"review_{source_locale}_to_{target_locale}.mp3"
    subprocess.run(
        [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-ar",
            sample_rate,
            "-ac",
            channels,
            "-b:a",
            "64k",
            "-acodec",
            "libmp3lame",
            "-y",
            str(output_audio),
        ],
        check=True,
        capture_output=True,
    )

    # Clean up temporary files
    concat_file.unlink()
    silence_file_5s.unlink()
    silence_file_300ms.unlink()

    print(
        f"Audio file '{output_audio}' created ({len(audio_files_with_keys)} audio files concatenated)"
    )
    print(f"\nReview files exported to '{output_dir}'")
