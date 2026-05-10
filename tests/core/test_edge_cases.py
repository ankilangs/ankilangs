"""Tests for edge cases in core.py: filename errors, parse helpers, import_review IPA-only changes."""

import csv
import sqlite3

import pytest

from al_tools.core import create_mp3_filename, csv2sqlite, import_review


def test_create_mp3_filename_empty_text_raises():
    """ValueError raised when text produces an empty filename."""
    with pytest.raises(ValueError, match="Invalid text"):
        create_mp3_filename("!!!")


def test_import_review_ipa_only_change(tmp_path):
    """IPA change without text change updates IPA in database."""
    # Use the existing import_review testdata pattern
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "625_words-base-de_de.csv").write_text(
        "key,text:de,ipa:de,audio:de,audio source:de,tags:de\n"
        "the cat,die Katze,/diː ˈkat͡sə/,,,AnkiLangs::DE\n"
    )
    (data_dir / "625_words-base-fr_fr.csv").write_text(
        "key,text:fr,ipa:fr,audio:fr,audio source:fr,tags:fr\n"
        "the cat,le chat,/lə ʃa/,,,AnkiLangs::FR\n"
    )
    (data_dir / "625_words-from-de_de-to-fr_fr.csv").write_text(
        "key,guid,pronunciation hint,spelling hint,reading hint,listening hint,notes\n"
        "the cat,guid-cat,,,,,\n"
    )
    (data_dir / "625_words-vocabulary.csv").write_text("key,clarification\nthe cat,\n")

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)

    # Create reviewed CSV with only IPA change (text stays the same)
    reviewed = tmp_path / "reviewed.csv"
    with open(reviewed, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
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
        )
        writer.writerow(
            [
                "guid-cat",
                "die Katze",
                "le chat",
                "/lə ʃɑ/",  # IPA changed
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )

    import_review(
        reviewed,
        db_path,
        source_locale="de_de",
        target_locale="fr_fr",
        media_dir=tmp_path / "audio",
        data_dir=data_dir,
    )

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT text, ipa FROM base_language WHERE key = 'the cat' AND locale = 'fr_fr'"
    )
    row = cursor.fetchone()
    conn.close()

    assert row[0] == "le chat"  # text unchanged
    assert row[1] == "/lə ʃɑ/"  # IPA updated


def test_import_review_unsupported_format_raises(tmp_path):
    """ValueError raised for unsupported file format."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "625_words-base-en_us.csv").write_text(
        "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
        "the cat,the cat,/ðə kæt/,,,AnkiLangs::EN\n"
    )
    (data_dir / "625_words-vocabulary.csv").write_text("key,clarification\nthe cat,\n")

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)

    bad_file = tmp_path / "reviewed.json"
    bad_file.write_text("{}")

    with pytest.raises(ValueError, match="Unsupported file format"):
        import_review(
            bad_file,
            db_path,
            source_locale="en_us",
            target_locale="es_es",
            media_dir=tmp_path / "audio",
            data_dir=data_dir,
        )


def test_import_review_empty_file(tmp_path, capsys):
    """Empty review file prints message and returns."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "625_words-base-en_us.csv").write_text(
        "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
        "the cat,the cat,/ðə kæt/,,,AnkiLangs::EN\n"
    )
    (data_dir / "625_words-vocabulary.csv").write_text("key,clarification\nthe cat,\n")

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)

    # CSV with only headers, no data rows
    empty_review = tmp_path / "reviewed.csv"
    empty_review.write_text(
        "guid,source_text,target_text,target_ipa,"
        "pronunciation_hint,spelling_hint,reading_hint,"
        "listening_hint,notes,review_comment\n"
    )

    import_review(
        empty_review,
        db_path,
        source_locale="en_us",
        target_locale="es_es",
        media_dir=tmp_path / "audio",
        data_dir=data_dir,
    )

    captured = capsys.readouterr()
    assert "No data found" in captured.out
