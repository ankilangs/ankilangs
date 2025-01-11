from enum import Enum
from pathlib import Path
import random
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

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )
        audio_file.write_bytes(response.audio_content)
        df.at[rowindex, audio_col] = f"[sound:{audio_file.name}]"
        df.at[rowindex, audio_source_col] = f"Google Cloud TTS<br>Voice: {voice_name}"
        print(f"Audio content written to file '{audio_file}'")

    df.to_csv(csv_path, index=False)
