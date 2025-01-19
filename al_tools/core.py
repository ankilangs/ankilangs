from enum import Enum
from pathlib import Path
import random
import time
from typing import List, Tuple, Dict

import pandas as pd
import os
import re

from google.cloud import texttospeech as tts


class AudioExistsAction(Enum):
    SKIP = "skip"
    OVERWRITE = "overwrite"
    RAISE = "raise"


def _create_mp3_filename(text: str, prefix: str = "") -> str:
    """
    Create a valid filename for the given text.
    """
    clean_name = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
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
                audio_file = audio_folder_path / _create_mp3_filename(
                    row[text_col], prefix=f"al_{language}_"
                )
            if audio_file.exists():
                if audio_exists_action == AudioExistsAction.SKIP:
                    print(f"Skipping existing audio file '{audio_file}'")
                    if pd.isna(row[audio_col]):
                        df.at[rowindex, audio_col] = f"[sound:{audio_file.name}]"
                        # find the source of that audio
                        audio_source = df[df[audio_col] == f"[sound:{audio_file.name}]"][
                            audio_source_col
                        ].values[0]
                        df.at[rowindex, audio_source_col] = audio_source
                        print(f"  ** Setting audio of '{row[text_col]}' to '{audio_file.name}'")
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
    for csv_path in folder_path.glob("625_words-from-*-to-*.csv"):
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

        for rowindex, row in df[df.duplicated(f"text:{from_lang_short}")].iterrows():
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

        for rowindex, row in df[df.duplicated(f"text:{to_lang_short}")].iterrows():
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
