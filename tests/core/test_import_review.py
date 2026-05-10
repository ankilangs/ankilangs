import csv
import sqlite3
from pathlib import Path


def test_import_review_updates_text_with_new_ipa(testdata_dir, tmpdir):
    """Test that when text changes with a new IPA, both are updated."""
    from al_tools.core import import_review, csv2sqlite

    tmpdir = Path(tmpdir)

    # Set up database
    db_path = tmpdir / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)

    # Create a mock audio file that should be deleted
    audio_dir = tmpdir / "audio" / "fr_FR"
    audio_dir.mkdir(parents=True)
    audio_file = audio_dir / "al_fr_fr_la_fille.mp3"
    audio_file.write_text("fake audio")

    # Create reviewed CSV file with text AND IPA change
    reviewed_file = tmpdir / "reviewed.csv"
    with open(reviewed_file, "w", newline="") as f:
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
        # Change text from "la fille" to "la jeune fille" with new IPA
        writer.writerow(
            [
                "cx}-x(|5qC",
                "the girl",
                "la jeune fille",
                "/la ʒœn fij/",  # New IPA provided
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )

    # Run import
    import_review(
        reviewed_file,
        db_path,
        source_locale="de_de",
        target_locale="fr_fr",
        media_dir=tmpdir / "audio",
        data_dir=testdata_dir,
    )

    # Verify database was updated
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT text, ipa, audio, audio_source FROM base_language WHERE key = ? AND locale = ?",
        ("the girl", "fr_fr"),
    )
    row = cursor.fetchone()
    assert row[0] == "la jeune fille"
    assert row[1] == "/la ʒœn fij/"  # New IPA should be set
    assert row[2] is None  # audio should be cleared
    assert row[3] is None  # audio_source should be cleared

    conn.close()

    # Verify audio file was deleted
    assert not audio_file.exists()


def test_import_review_clears_ipa_when_text_changes(testdata_dir, tmpdir):
    """Test that when text changes without a new IPA, IPA is cleared."""
    from al_tools.core import import_review, csv2sqlite

    tmpdir = Path(tmpdir)

    # Set up database
    db_path = tmpdir / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)

    # Create reviewed CSV file with text change but same old IPA
    reviewed_file = tmpdir / "reviewed.csv"
    with open(reviewed_file, "w", newline="") as f:
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
        # Change text but keep the old IPA (which is now invalid)
        writer.writerow(
            [
                "cx}-x(|5qC",
                "the girl",
                "la jeune fille",  # Changed text
                "/la fij/",  # Old IPA (same as in DB)
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )

    # Run import
    import_review(
        reviewed_file,
        db_path,
        source_locale="de_de",
        target_locale="fr_fr",
        media_dir=tmpdir / "audio",
        data_dir=testdata_dir,
    )

    # Verify IPA was cleared
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT text, ipa FROM base_language WHERE key = ? AND locale = ?",
        ("the girl", "fr_fr"),
    )
    row = cursor.fetchone()
    assert row[0] == "la jeune fille"
    assert row[1] is None  # IPA should be cleared since no new IPA was provided

    conn.close()


def test_import_review_updates_hints(testdata_dir, tmpdir):
    """Test that import_review updates hint fields."""
    from al_tools.core import import_review, csv2sqlite

    tmpdir = Path(tmpdir)

    # Set up database
    db_path = tmpdir / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)

    # Create reviewed CSV file with hint changes
    reviewed_file = tmpdir / "reviewed.csv"
    with open(reviewed_file, "w", newline="") as f:
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
        # Add hints without changing text
        writer.writerow(
            [
                "Jl(bTNf7.m",
                "the daughter",
                "la fille",
                "/la fij/",
                "female child",
                "",
                "not the girl",
                "family member",
                "ambiguous word",
                "reviewer note",
            ]
        )

    # Run import
    import_review(
        reviewed_file,
        db_path,
        source_locale="de_de",
        target_locale="fr_fr",
        media_dir=tmpdir / "audio",
        data_dir=testdata_dir,
    )

    # Verify hints were updated
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT pronunciation_hint, reading_hint, listening_hint, notes FROM translation_pair WHERE guid = ?",
        ("Jl(bTNf7.m",),
    )
    row = cursor.fetchone()
    assert row[0] == "female child"
    assert row[1] == "not the girl"
    assert row[2] == "family member"
    assert row[3] == "ambiguous word"

    conn.close()


def test_import_review_xlsx_with_text_change(testdata_dir, tmpdir):
    """Test import from Excel file with text change, audio deletion, and IPA clearing."""
    from al_tools.core import import_review, csv2sqlite
    from openpyxl import Workbook

    tmpdir = Path(tmpdir)

    # Set up database
    db_path = tmpdir / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)

    # Create a mock audio file that should be deleted
    audio_dir = tmpdir / "audio" / "fr_FR"
    audio_dir.mkdir(parents=True)
    audio_file = audio_dir / "al_fr_fr_le_fils.mp3"
    audio_file.write_text("fake audio")

    # Create reviewed Excel file with text change but same old IPA
    reviewed_file = tmpdir / "reviewed.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(
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
    # Change "le fils" to "le garcon" but keep old IPA
    ws.append(
        [
            "u&?9)X(F>^",
            "the son",
            "le garcon",  # Changed text
            "/lə fis/",  # Old IPA (same as DB)
            "",
            "",
            "",
            "",
            "",
            "",
        ]
    )
    wb.save(reviewed_file)

    # Run import
    import_review(
        reviewed_file,
        db_path,
        source_locale="de_de",
        target_locale="fr_fr",
        media_dir=tmpdir / "audio",
        data_dir=testdata_dir,
    )

    # Verify database was updated
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT text, ipa, audio, audio_source FROM base_language WHERE key = ? AND locale = ?",
        ("the son", "fr_fr"),
    )
    row = cursor.fetchone()
    assert row[0] == "le garcon"
    assert row[1] is None  # IPA should be cleared (no new IPA provided)
    assert row[2] is None  # audio should be cleared
    assert row[3] is None  # audio_source should be cleared

    conn.close()

    # Verify audio file was deleted
    assert not audio_file.exists()


def test_import_review_partial_file(testdata_dir, tmpdir):
    """Importing a subset of entries updates only those entries, leaving others unchanged."""
    from al_tools.core import import_review, csv2sqlite

    tmpdir = Path(tmpdir)

    # Set up database (3 entries: the son, the daughter, the girl)
    db_path = tmpdir / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)

    # Create reviewed CSV with only 1 of 3 entries changed
    reviewed_file = tmpdir / "reviewed.csv"
    with open(reviewed_file, "w", newline="") as f:
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
        # Only include "the girl" with changed text
        writer.writerow(
            [
                "cx}-x(|5qC",
                "the girl",
                "la jeune fille",
                "/la ʒœn fij/",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )

    # Run import
    import_review(
        reviewed_file,
        db_path,
        source_locale="de_de",
        target_locale="fr_fr",
        media_dir=tmpdir / "audio",
        data_dir=testdata_dir,
    )

    # Verify "the girl" was updated
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT text, ipa FROM base_language WHERE key = ? AND locale = ?",
        ("the girl", "fr_fr"),
    )
    row = cursor.fetchone()
    assert row[0] == "la jeune fille"
    assert row[1] == "/la ʒœn fij/"

    # Verify "the son" and "the daughter" are unchanged
    cursor.execute(
        "SELECT text, ipa FROM base_language WHERE key = ? AND locale = ?",
        ("the son", "fr_fr"),
    )
    row = cursor.fetchone()
    assert row[0] == "le fils"
    assert row[1] == "/lə fis/"

    cursor.execute(
        "SELECT text, ipa FROM base_language WHERE key = ? AND locale = ?",
        ("the daughter", "fr_fr"),
    )
    row = cursor.fetchone()
    assert row[0] == "la fille"
    assert row[1] == "/la fij/"

    conn.close()


def test_import_review_no_changes(testdata_dir, tmpdir, capsys):
    """Test that import_review reports no changes when file matches database."""
    from al_tools.core import import_review, csv2sqlite

    tmpdir = Path(tmpdir)

    # Set up database
    db_path = tmpdir / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)

    # Create reviewed CSV file with no changes (same as database)
    reviewed_file = tmpdir / "reviewed.csv"
    with open(reviewed_file, "w", newline="") as f:
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
                "cx}-x(|5qC",
                "the girl",
                "la fille",
                "/la fij/",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )

    # Run import
    import_review(
        reviewed_file,
        db_path,
        source_locale="de_de",
        target_locale="fr_fr",
        media_dir=tmpdir / "audio",
        data_dir=testdata_dir,
    )

    captured = capsys.readouterr()
    assert "No changes found" in captured.out
