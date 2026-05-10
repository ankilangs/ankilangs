"""Tests for SQLite→CSV export."""

import csv

from al_tools.core import csv2sqlite, sqlite2csv


def _export(testdata_dir, tmp_path):
    """Import testdata CSVs into SQLite, then export back."""
    db_path = tmp_path / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)

    out_dir = tmp_path / "export"
    out_dir.mkdir()
    sqlite2csv(db_path, out_dir, force=True)
    return out_dir


def test_exports_base_language_files(testdata_dir, tmp_path):
    out_dir = _export(testdata_dir, tmp_path)

    en_csv = out_dir / "625_words-base-en_us.csv"
    assert en_csv.exists()
    with open(en_csv) as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 2
    assert reader[0]["key"] == "the cat"
    assert reader[0]["text:en"] == "the cat"
    assert reader[0]["ipa:en"] == "/ðə kæt/"


def test_exports_translation_pair_files(testdata_dir, tmp_path):
    out_dir = _export(testdata_dir, tmp_path)

    tp_csv = out_dir / "625_words-from-en_us-to-es_es.csv"
    assert tp_csv.exists()
    with open(tp_csv) as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 2
    assert reader[1]["key"] == "the dog"
    assert reader[1]["notes"] == "fetch"


def test_exports_vocabulary(testdata_dir, tmp_path):
    out_dir = _export(testdata_dir, tmp_path)

    vocab_csv = out_dir / "625_words-vocabulary.csv"
    assert vocab_csv.exists()
    with open(vocab_csv) as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 2
    assert reader[1]["key"] == "the dog"
    assert reader[1]["clarification"] == "domestic animal"


def test_exports_pictures(testdata_dir, tmp_path):
    out_dir = _export(testdata_dir, tmp_path)

    pic_csv = out_dir / "625_words-pictures.csv"
    assert pic_csv.exists()
    with open(pic_csv) as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 1


def test_exports_tts_overrides(testdata_dir, tmp_path):
    out_dir = _export(testdata_dir, tmp_path)

    tts_csv = out_dir / "tts_overrides.csv"
    assert tts_csv.exists()
    with open(tts_csv) as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 1
    assert reader[0]["key"] == "the cat"
    assert reader[0]["locale"] == "es_es"
    assert reader[0]["tts_text"] == "el gáto"
    assert reader[0]["is_ssml"] == "0"


def test_csv_uses_unix_line_endings(testdata_dir, tmp_path):
    out_dir = _export(testdata_dir, tmp_path)

    en_csv = out_dir / "625_words-base-en_us.csv"
    raw = en_csv.read_bytes()
    assert b"\r\n" not in raw
    assert b"\n" in raw


def test_tags_column_generated_from_locale(testdata_dir, tmp_path):
    out_dir = _export(testdata_dir, tmp_path)

    en_csv = out_dir / "625_words-base-en_us.csv"
    with open(en_csv) as f:
        reader = list(csv.DictReader(f))
    assert reader[0]["tags:en"] == "AnkiLangs::EN"
