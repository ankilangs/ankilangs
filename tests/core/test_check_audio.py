"""Tests for audio file consistency checks via ambiguity_detection."""

import sqlite3

from al_tools.core import ambiguity_detection, csv2sqlite


def _create_data_dir(tmp_path, *, audio_refs=True):
    """Create minimal CSV data with audio references."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    audio_col = "[sound:al_en_us_the_cat.mp3],Google Cloud TTS" if audio_refs else ","
    (data_dir / "625_words-base-en_us.csv").write_text(
        "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
        f"the cat,the cat,/ðə kæt/,{audio_col},AnkiLangs::EN\n"
        f"the dog,the dog,/ðə dɒɡ/,[sound:al_en_us_the_dog.mp3],Google Cloud TTS,AnkiLangs::EN\n"
    )
    (data_dir / "625_words-vocabulary.csv").write_text(
        "key,clarification\nthe cat,\nthe dog,\n"
    )
    return data_dir


def _setup(tmp_path, *, audio_refs=True):
    """Create data dir, import to DB, return (db_path, data_dir, media_dir)."""
    data_dir = _create_data_dir(tmp_path, audio_refs=audio_refs)
    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)
    media_dir = tmp_path / "audio"
    return db_path, data_dir, media_dir


def test_detects_missing_audio_on_disk(tmp_path):
    """Reports audio references in DB with no file on disk."""
    db_path, data_dir, media_dir = _setup(tmp_path)

    # Create audio dir with only one of two referenced files
    audio_dir = media_dir / "en_US"
    audio_dir.mkdir(parents=True)
    (audio_dir / "al_en_us_the_cat.mp3").write_bytes(b"fake")
    # al_en_us_the_dog.mp3 is missing

    output = ambiguity_detection(db_path, data_dir, media_dir=media_dir)

    assert "AUDIO FILES IN DATABASE BUT NOT ON DISK" in output
    assert "al_en_us_the_dog.mp3" in output
    assert "al_en_us_the_cat.mp3" not in output


def test_detects_orphaned_audio_files(tmp_path):
    """Reports audio files on disk not referenced in DB."""
    db_path, data_dir, media_dir = _setup(tmp_path)

    # Create audio dir with referenced files plus an orphan
    audio_dir = media_dir / "en_US"
    audio_dir.mkdir(parents=True)
    (audio_dir / "al_en_us_the_cat.mp3").write_bytes(b"fake")
    (audio_dir / "al_en_us_the_dog.mp3").write_bytes(b"fake")
    (audio_dir / "al_en_us_orphan.mp3").write_bytes(b"fake")

    output = ambiguity_detection(db_path, data_dir, media_dir=media_dir)

    assert "AUDIO FILES ON DISK BUT NOT IN DATABASE" in output
    assert "al_en_us_orphan.mp3" in output


def test_auto_fix_clears_db_refs_for_missing_files(tmp_path):
    """auto_fix removes DB audio refs when file doesn't exist on disk."""
    db_path, data_dir, media_dir = _setup(tmp_path)

    # Create only cat's audio, dog's is missing
    audio_dir = media_dir / "en_US"
    audio_dir.mkdir(parents=True)
    (audio_dir / "al_en_us_the_cat.mp3").write_bytes(b"fake")

    output = ambiguity_detection(db_path, data_dir, media_dir=media_dir, auto_fix=True)

    assert "FIXING" in output
    assert "Cleared audio for 'the dog'" in output

    # Verify DB was updated
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT audio, audio_source FROM base_language WHERE key = 'the dog' AND locale = 'en_us'"
    )
    row = cursor.fetchone()
    conn.close()
    assert row[0] == ""
    assert row[1] == ""


def test_auto_fix_deletes_orphaned_files(tmp_path):
    """auto_fix deletes audio files not referenced in DB."""
    db_path, data_dir, media_dir = _setup(tmp_path)

    audio_dir = media_dir / "en_US"
    audio_dir.mkdir(parents=True)
    (audio_dir / "al_en_us_the_cat.mp3").write_bytes(b"fake")
    (audio_dir / "al_en_us_the_dog.mp3").write_bytes(b"fake")
    orphan = audio_dir / "al_en_us_orphan.mp3"
    orphan.write_bytes(b"fake")

    output = ambiguity_detection(db_path, data_dir, media_dir=media_dir, auto_fix=True)

    assert "Deleted en_US/al_en_us_orphan.mp3" in output
    assert not orphan.exists()


def test_no_issues_when_consistent(tmp_path):
    """No audio output when all files match DB references."""
    db_path, data_dir, media_dir = _setup(tmp_path)

    audio_dir = media_dir / "en_US"
    audio_dir.mkdir(parents=True)
    (audio_dir / "al_en_us_the_cat.mp3").write_bytes(b"fake")
    (audio_dir / "al_en_us_the_dog.mp3").write_bytes(b"fake")

    output = ambiguity_detection(db_path, data_dir, media_dir=media_dir)

    assert "AUDIO FILES" not in output
