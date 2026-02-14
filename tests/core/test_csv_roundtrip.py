"""Tests for CSV→SQLite→CSV round-trip preservation."""

import csv
from pathlib import Path

from al_tools.core import csv2sqlite, sqlite2csv


def _read_csv(path: Path) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


def test_roundtrip_preserves_all_files(testdata_dir, tmp_path):
    """CSV→SQLite→CSV should produce identical files for all table types."""
    db_path = tmp_path / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)

    out_dir = tmp_path / "export"
    out_dir.mkdir()
    sqlite2csv(db_path, out_dir, force=True)

    for csv_file in testdata_dir.glob("*.csv"):
        original = _read_csv(csv_file)
        exported = _read_csv(out_dir / csv_file.name)

        assert len(original) == len(exported), f"Row count mismatch in {csv_file.name}"
        for orig, exp in zip(original, exported):
            assert orig == exp, f"Row mismatch in {csv_file.name}"


def test_rows_sorted_case_insensitive(testdata_dir, tmp_path):
    """Verify export sorts by key COLLATE NOCASE."""
    db_path = tmp_path / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)

    out_dir = tmp_path / "export"
    out_dir.mkdir()
    sqlite2csv(db_path, out_dir, force=True)

    exported = _read_csv(out_dir / "625_words-base-en_us.csv")
    keys = [r["key"] for r in exported]
    assert keys == ["apple", "Banana", "Zebra"]
