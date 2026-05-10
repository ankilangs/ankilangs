"""Tests for minimal pairs and i18n import/export via csv2sqlite/sqlite2csv."""

import csv
import sqlite3

from al_tools.core import csv2sqlite, sqlite2csv


def _read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def _create_full_data(data_dir):
    """Create CSV data including minimal pairs and i18n tables."""
    (data_dir / "625_words-base-en_us.csv").write_text(
        "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
        "the cat,the cat,/ðə kæt/,,,AnkiLangs::EN\n"
    )
    (data_dir / "625_words-vocabulary.csv").write_text("key,clarification\nthe cat,\n")

    # Minimal pairs file
    (data_dir / "minimal_pairs-from-en_us_to_es_es.csv").write_text(
        "guid,text1,audio1,ipa1,meaning1,text2,audio2,ipa2,meaning2,tags\n"
        "mp-guid-1,ship,[sound:ship.mp3],/ʃɪp/,boat,sheep,[sound:sheep.mp3],/ʃiːp/,animal,AnkiLangs::MP\n"
        "mp-guid-2,bit,,/bɪt/,piece,beat,,/biːt/,strike,AnkiLangs::MP\n"
    )

    # i18n files
    i18n_dir = data_dir / "i18n"
    i18n_dir.mkdir()

    (i18n_dir / "language_names.csv").write_text(
        "source_locale,target_locale,name\nen_us,es_es,Spanish\nes_es,en_us,Inglés\n"
    )
    (i18n_dir / "ui_strings.csv").write_text(
        "locale,key,value\nen_us,card_front,Front\nes_es,card_front,Frente\n"
    )
    (i18n_dir / "card_types.csv").write_text(
        "locale,card_type,name\nen_us,reading,Reading\nes_es,reading,Lectura\n"
    )


def test_minimal_pairs_imported_to_sqlite(tmp_path):
    """Minimal pairs CSV is imported into the database."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_full_data(data_dir)

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM minimal_pairs")
    assert cursor.fetchone()[0] == 2

    cursor.execute(
        "SELECT text1, ipa1, meaning1, text2, ipa2, meaning2 FROM minimal_pairs WHERE guid = 'mp-guid-1'"
    )
    row = cursor.fetchone()
    assert row == ("ship", "/ʃɪp/", "boat", "sheep", "/ʃiːp/", "animal")
    conn.close()


def test_minimal_pairs_roundtrip(tmp_path):
    """Minimal pairs survive a CSV→SQLite→CSV round-trip."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_full_data(data_dir)

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)

    out_dir = tmp_path / "export"
    out_dir.mkdir()
    sqlite2csv(db_path, out_dir, force=True)

    exported = _read_csv(out_dir / "minimal_pairs-from-en_us_to_es_es.csv")
    assert len(exported) == 2
    assert exported[0]["guid"] == "mp-guid-1"  # sorted by guid
    assert exported[0]["text1"] == "ship"
    assert exported[0]["audio1"] == "[sound:ship.mp3]"
    assert exported[1]["guid"] == "mp-guid-2"
    assert exported[1]["text1"] == "bit"


def test_i18n_language_names_imported(tmp_path):
    """i18n language names are imported into the database."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_full_data(data_dir)

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM i18n_language_names WHERE source_locale = 'en_us' AND target_locale = 'es_es'"
    )
    assert cursor.fetchone()[0] == "Spanish"
    conn.close()


def test_i18n_language_names_roundtrip(tmp_path):
    """i18n language names survive a round-trip."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_full_data(data_dir)

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)

    out_dir = tmp_path / "export"
    out_dir.mkdir()
    sqlite2csv(db_path, out_dir, force=True)

    exported = _read_csv(out_dir / "i18n" / "language_names.csv")
    assert len(exported) == 2
    names = {r["target_locale"]: r["name"] for r in exported}
    assert names["es_es"] == "Spanish"
    assert names["en_us"] == "Inglés"


def test_i18n_ui_strings_roundtrip(tmp_path):
    """i18n UI strings survive a round-trip."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_full_data(data_dir)

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)

    out_dir = tmp_path / "export"
    out_dir.mkdir()
    sqlite2csv(db_path, out_dir, force=True)

    exported = _read_csv(out_dir / "i18n" / "ui_strings.csv")
    assert len(exported) == 2
    values = {r["locale"]: r["value"] for r in exported}
    assert values["en_us"] == "Front"
    assert values["es_es"] == "Frente"


def test_i18n_card_types_roundtrip(tmp_path):
    """i18n card types survive a round-trip."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_full_data(data_dir)

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)

    out_dir = tmp_path / "export"
    out_dir.mkdir()
    sqlite2csv(db_path, out_dir, force=True)

    exported = _read_csv(out_dir / "i18n" / "card_types.csv")
    assert len(exported) == 2
    names = {r["locale"]: r["name"] for r in exported}
    assert names["en_us"] == "Reading"
    assert names["es_es"] == "Lectura"
