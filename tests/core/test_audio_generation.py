"""Tests for audio generation with fake TTS client."""

import sqlite3

import pytest

from al_tools.core import AudioExistsAction, csv2sqlite, generate_audio
from tests.fakes import FakeTextToSpeechClient


def _setup_db(testdata_dir, tmp_path):
    """Import testdata CSVs into SQLite and return (db_path, audio_dir)."""
    db_path = tmp_path / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)
    audio_dir = tmp_path / "audio" / "en_US"
    return db_path, audio_dir


def test_creates_audio_files(testdata_dir, tmp_path):
    """Audio files are created for entries with text."""
    db_path, audio_dir = _setup_db(testdata_dir, tmp_path)
    fake_client = FakeTextToSpeechClient()

    generate_audio(
        db_path,
        "en_us",
        audio_dir,
        AudioExistsAction.SKIP,
        data_dir=testdata_dir,
        delay=0,
        tts_client=fake_client,
    )

    mp3_files = list(audio_dir.glob("*.mp3"))
    assert len(mp3_files) == 2
    filenames = sorted(f.name for f in mp3_files)
    assert "al_en_us_the_cat.mp3" in filenames
    assert "al_en_us_the_dog.mp3" in filenames


def test_files_contain_fake_audio_bytes(testdata_dir, tmp_path):
    """Generated files contain the bytes from the TTS client."""
    db_path, audio_dir = _setup_db(testdata_dir, tmp_path)
    fake_client = FakeTextToSpeechClient(audio_bytes=b"test-audio-123")

    generate_audio(
        db_path,
        "en_us",
        audio_dir,
        AudioExistsAction.SKIP,
        data_dir=testdata_dir,
        delay=0,
        tts_client=fake_client,
    )

    content = (audio_dir / "al_en_us_the_cat.mp3").read_bytes()
    assert content == b"test-audio-123"


def test_updates_db_with_sound_reference(testdata_dir, tmp_path):
    """DB is updated with sound reference and audio source."""
    db_path, audio_dir = _setup_db(testdata_dir, tmp_path)
    fake_client = FakeTextToSpeechClient()

    generate_audio(
        db_path,
        "en_us",
        audio_dir,
        AudioExistsAction.SKIP,
        data_dir=testdata_dir,
        delay=0,
        tts_client=fake_client,
    )

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT audio, audio_source FROM base_language WHERE key = 'the cat' AND locale = 'en_us'"
    )
    row = cursor.fetchone()
    conn.close()

    assert row[0] == "[sound:al_en_us_the_cat.mp3]"
    assert "Google Cloud TTS" in row[1]


def test_skips_empty_text_rows(testdata_dir, tmp_path):
    """Rows with empty text are not sent to TTS."""
    db_path, audio_dir = _setup_db(testdata_dir, tmp_path)
    fake_client = FakeTextToSpeechClient()

    generate_audio(
        db_path,
        "en_us",
        audio_dir,
        AudioExistsAction.SKIP,
        data_dir=testdata_dir,
        delay=0,
        tts_client=fake_client,
    )

    assert len(fake_client.calls) == 2


def test_skip_does_not_regenerate(testdata_dir, tmp_path):
    """SKIP preserves existing audio files."""
    db_path, audio_dir = _setup_db(testdata_dir, tmp_path)
    audio_dir.mkdir(parents=True)
    existing = audio_dir / "al_en_us_the_cat.mp3"
    existing.write_bytes(b"original-content")

    fake_client = FakeTextToSpeechClient(audio_bytes=b"new-content")

    generate_audio(
        db_path,
        "en_us",
        audio_dir,
        AudioExistsAction.SKIP,
        data_dir=testdata_dir,
        delay=0,
        tts_client=fake_client,
    )

    assert existing.read_bytes() == b"original-content"
    assert len(fake_client.calls) == 1


def test_overwrite_replaces_existing(testdata_dir, tmp_path):
    """OVERWRITE replaces existing audio files."""
    db_path, audio_dir = _setup_db(testdata_dir, tmp_path)
    audio_dir.mkdir(parents=True)
    existing = audio_dir / "al_en_us_the_cat.mp3"
    existing.write_bytes(b"original-content")

    fake_client = FakeTextToSpeechClient(audio_bytes=b"new-content")

    generate_audio(
        db_path,
        "en_us",
        audio_dir,
        AudioExistsAction.OVERWRITE,
        data_dir=testdata_dir,
        delay=0,
        tts_client=fake_client,
    )

    assert existing.read_bytes() == b"new-content"


def test_raise_errors_on_existing(testdata_dir, tmp_path):
    """RAISE raises FileExistsError for existing files."""
    db_path, audio_dir = _setup_db(testdata_dir, tmp_path)
    audio_dir.mkdir(parents=True)
    existing = audio_dir / "al_en_us_the_cat.mp3"
    existing.write_bytes(b"original-content")

    fake_client = FakeTextToSpeechClient()

    with pytest.raises(FileExistsError):
        generate_audio(
            db_path,
            "en_us",
            audio_dir,
            AudioExistsAction.RAISE,
            data_dir=testdata_dir,
            delay=0,
            tts_client=fake_client,
        )


def test_limit_stops_after_n_files(testdata_dir, tmp_path):
    """Limit parameter stops generation after N files."""
    db_path, audio_dir = _setup_db(testdata_dir, tmp_path)
    fake_client = FakeTextToSpeechClient()

    generate_audio(
        db_path,
        "en_us",
        audio_dir,
        AudioExistsAction.SKIP,
        data_dir=testdata_dir,
        delay=0,
        limit=1,
        tts_client=fake_client,
    )

    assert len(fake_client.calls) == 1
    mp3_files = list(audio_dir.glob("*.mp3"))
    assert len(mp3_files) == 1


def test_uses_tts_override_text(testdata_dir, tmp_path):
    """TTS override text is sent instead of base language text."""
    db_path, audio_dir = _setup_db(testdata_dir, tmp_path)
    fake_client = FakeTextToSpeechClient()

    generate_audio(
        db_path,
        "en_us",
        audio_dir,
        AudioExistsAction.SKIP,
        data_dir=testdata_dir,
        delay=0,
        tts_client=fake_client,
    )

    cat_call = fake_client.calls[0]
    assert cat_call["input"].text == "thuh cat"


def test_ssml_override(testdata_dir, tmp_path):
    """SSML override is sent as SSML input."""
    db_path, audio_dir = _setup_db(testdata_dir, tmp_path)
    fake_client = FakeTextToSpeechClient()

    generate_audio(
        db_path,
        "en_us",
        audio_dir,
        AudioExistsAction.SKIP,
        data_dir=testdata_dir,
        delay=0,
        tts_client=fake_client,
    )

    dog_call = fake_client.calls[1]
    assert dog_call["input"].ssml == "<speak>the dog</speak>"
