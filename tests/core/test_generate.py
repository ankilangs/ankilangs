"""Tests for generate_joined_source_fields."""

import csv
from pathlib import Path

from al_tools.core import csv2sqlite, generate_joined_source_fields


def _read_csv(path: Path) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


def test_generates_source_csv_with_audio_and_picture(testdata_dir, tmp_path):
    """Entries with both audio source and picture source get combined."""
    db_path = tmp_path / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)

    out_dir = tmp_path / "generated"
    generate_joined_source_fields(db_path, out_dir, testdata_dir)

    out_file = out_dir / "625_words-from-en_us-to-es_es.csv"
    assert out_file.exists()

    rows = _read_csv(out_file)
    keys = [r["key"] for r in rows]
    assert "the cat" in keys

    cat_row = next(r for r in rows if r["key"] == "the cat")
    assert "Picture:" in cat_row["source"]
    assert "Unsplash" in cat_row["source"]
    assert "Audio:" in cat_row["source"]
    assert "Google Cloud TTS" in cat_row["source"]


def test_audio_only_source(testdata_dir, tmp_path):
    """Entry with audio source but no picture only shows audio."""
    db_path = tmp_path / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)

    out_dir = tmp_path / "generated"
    generate_joined_source_fields(db_path, out_dir, testdata_dir)

    out_file = out_dir / "625_words-from-en_us-to-es_es.csv"
    rows = _read_csv(out_file)
    assert len(rows) == 1
    assert rows[0]["source"] == "Audio:<br>Google TTS"


def test_no_source_rows_excluded(testdata_dir, tmp_path):
    """Entries with no audio source or picture source are excluded."""
    db_path = tmp_path / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)

    out_dir = tmp_path / "generated"
    generate_joined_source_fields(db_path, out_dir, testdata_dir)

    out_file = out_dir / "625_words-from-en_us-to-es_es.csv"
    rows = _read_csv(out_file)
    keys = [r["key"] for r in rows]
    assert "the dog" not in keys
