from enum import Enum
from pathlib import Path
import random
import time
from typing import List, Tuple, Dict
import unicodedata
import csv
import sqlite3
from datetime import datetime

import pandas as pd
import os
import re

from google.cloud import texttospeech as tts


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


_VOICE_MAP = {
    "en_gb": [
        "en-GB-Chirp3-HD-Charon",
        "en-GB-Chirp3-HD-Kore",
        "en-GB-Chirp3-HD-Leda",
    ],
    "en_us": [
        "en-US-Chirp3-HD-Aoede",
        "en-US-Chirp3-HD-Enceladus",
        "en-US-Chirp3-HD-Sulafat",
    ],
    "es_es": [
        "es-ES-Chirp3-HD-Despina",
        "es-ES-Chirp3-HD-Gacrux",
    ],
    "fr_fr": [
        "fr-FR-Chirp3-HD-Callirrhoe",
        "fr-FR-Chirp3-HD-Puck",
        "fr-FR-Chirp3-HD-Schedar",
    ],
    "it_it": [
        "it-IT-Chirp3-HD-Autonoe",
        "it-IT-Chirp3-HD-Iapetus",
        "it-IT-Chirp3-HD-Vindemiatrix",
    ],
    "de_de": [
        "de-DE-Chirp3-HD-Erinome",
        "de-DE-Chirp3-HD-Rasalgethi",
        "de-DE-Chirp3-HD-Umbriel",
    ],
    "pt_pt": [
        "pt-PT-Chirp3-HD-Fenrir",
        "pt-PT-Chirp3-HD-Sadachbia",
        "pt-PT-Chirp3-HD-Zephyr",
    ],
}


def generate_audio(
    csv_path: Path,
    audio_folder_path: Path,
    audio_exists_action: AudioExistsAction,
    seed: int = 42,
):
    """
    Generate audio via the Google Cloud TTS API.
    As input it expects a CSV file in the correct format.
    If the directory does not exist it will be created.
    """
    random.seed(seed)

    # csv_path is something like src/data/625_words-base-es_es.csv
    language = csv_path.stem.split("-")[-1].lower()

    df = pd.read_csv(csv_path, sep=",")
    os.makedirs(audio_folder_path, exist_ok=True)

    text_col = _get_text_col(df)
    audio_col = _get_audio_col(df)
    audio_source_col = _get_audio_source_col(df)

    client = tts.TextToSpeechClient()
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3)
    try:
        for rowindex, row in df.iterrows():
            if pd.notna(row[audio_col]):
                audio_file = audio_folder_path / re.search(
                    r"\[sound:(.+)\]", row[audio_col]
                ).group(1)
            else:
                audio_file = audio_folder_path / create_mp3_filename(
                    row[text_col], prefix=f"al_{language}_"
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

            voice_name = random.choice(_VOICE_MAP[language])
            voice = tts.VoiceSelectionParams(
                language_code=f"{language.split('_')[0]}-{language.split('_')[1].upper()}",
                name=voice_name,
            )
            synthesis_input = tts.SynthesisInput(text=row[text_col])

            # Avoid rate limit
            time.sleep(1)

            try:
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config,
                )
            except Exception as e:
                raise Exception(f"Error for '{row[text_col]}': {e}") from e
            audio_file.write_bytes(response.audio_content)
            df.at[rowindex, audio_col] = f"[sound:{audio_file.name}]"
            df.at[rowindex, audio_source_col] = (
                f"Google Cloud TTS<br>Voice: {voice_name}"
            )
            print(f"Audio content written to file '{audio_file}'")
    finally:
        # Save the updated DataFrame
        df.to_csv(csv_path, index=False)


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


def generate_joined_source_fields(folder_path: Path):
    """
    Generate CSV files that contain the joint source and license information
    from other 625 words CSV files.
    """
    langs = set()
    for csv_path in folder_path.glob("625_words-base-*.csv"):
        langs.add(csv_path.stem.split("-")[-1])

    pictures_df = pd.read_csv(folder_path / "625_words-pictures.csv", sep=",")

    for lang in langs:
        base_lang_df = pd.read_csv(folder_path / f"625_words-base-{lang}.csv", sep=",")
        for csv_path in folder_path.glob(f"625_words-from-*-to-{lang}.csv"):
            csv_path_generated = folder_path / "generated" / csv_path.name
            joined_df = pd.merge(
                base_lang_df,
                pictures_df,
                how="left",
                on="key",
            )
            joined_df["source"] = joined_df.apply(
                lambda row: _format_source(
                    row["picture source"], row[f"audio source:{lang.split('_')[0]}"]
                ),
                axis=1,
            )
            # keep 'key' and 'source' columns and only if 'source' is not empty
            joined_df = joined_df[["key", "source"]][joined_df["source"] != ""]
            joined_df.to_csv(csv_path_generated, index=False)
            print(f"CSV file '{csv_path_generated}' written")


class _AmbiguousWords:
    def __init__(self, filename: str):
        self.filename = filename
        # key is the word, value is a tuple of keys and empty columns
        self.ambiguous_words: Dict[str, Tuple[Tuple, Tuple]] = dict()

    def add(self, word: str, keys: Tuple, empty_columns: Tuple):
        self.ambiguous_words[word] = (keys, empty_columns)

    def __repr__(self):
        return f"{self.filename}: {self.ambiguous_words}"


def ambiguity_detection(folder_path: Path) -> str:
    """
    Detect ambiguous words in the given folder.
    """
    aw_list: List[_AmbiguousWords] = []
    for csv_path in sorted(folder_path.glob("625_words-from-*-to-*.csv")):
        aw_obj = _AmbiguousWords(csv_path.name)
        re_result = re.search(r"625_words-from-(.*)-to-(.*)", csv_path.stem).groups()
        from_lang = re_result[0]
        from_lang_short = from_lang.split("_")[0]
        to_lang = re_result[1]
        to_lang_short = to_lang.split("_")[0]

        # join with the two base files
        df = pd.read_csv(csv_path, sep=",")
        from_df = pd.read_csv(folder_path / f"625_words-base-{from_lang}.csv", sep=",")
        to_df = pd.read_csv(folder_path / f"625_words-base-{to_lang}.csv", sep=",")
        df = pd.merge(df, from_df, how="left", on="key")
        df = pd.merge(df, to_df, how="left", on="key")

        for rowindex, row in df[
            df.duplicated(f"text:{from_lang_short}")
            & df[f"text:{from_lang_short}"].notna()
        ].iterrows():
            duplicate_rows = df[
                df[f"text:{from_lang_short}"] == row[f"text:{from_lang_short}"]
            ]
            columns = []
            if duplicate_rows["pronunciation hint"].isnull().all():
                columns.append("pronunciation hint")
            if duplicate_rows["spelling hint"].isnull().all():
                columns.append("spelling hint")
            if columns:
                aw_obj.add(
                    row[f"text:{from_lang_short}"],
                    tuple(duplicate_rows["key"]),
                    tuple(columns),
                )

        for rowindex, row in df[
            df.duplicated(f"text:{to_lang_short}") & df[f"text:{to_lang_short}"].notna()
        ].iterrows():
            duplicate_rows = df[
                df[f"text:{to_lang_short}"] == row[f"text:{to_lang_short}"]
            ]
            columns = []
            if duplicate_rows["reading hint"].isnull().all():
                columns.append("reading hint")
            if duplicate_rows["listening hint"].isnull().all():
                columns.append("listening hint")
            if columns:
                aw_obj.add(
                    row[f"text:{to_lang_short}"],
                    tuple(duplicate_rows["key"]),
                    tuple(columns),
                )

        aw_list.append(aw_obj)

    output = ""
    for aw_obj in aw_list:
        if aw_obj.ambiguous_words:
            output += f"The following ambiguous words were found in the file '{aw_obj.filename}':\n"
            for word, (keys, empty_columns) in aw_obj.ambiguous_words.items():
                output += f"  - '{word}' has the key(s) {keys} and missing column(s) {empty_columns}\n"
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
