"""Tests for CSV/SQLite sync detection."""

import sqlite3
import time

import pytest

from al_tools.core import csv2sqlite, sqlite2csv, SyncConflictError


@pytest.fixture
def minimal_csv_data(tmp_path):
    """Create minimal CSV files for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create a minimal base language file
    base_csv = data_dir / "625_words-base-en_us.csv"
    base_csv.write_text(
        "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
        "the cat,the cat,/ðə kæt/,,,AnkiLangs::EN\n"
    )

    return data_dir


class TestCsv2SqliteSucceedsWhenCsvModified:
    """Normal workflow: CSV changed, we want to import it."""

    def test_fresh_import(self, minimal_csv_data, tmp_path):
        db_path = tmp_path / "test.db"
        csv2sqlite(minimal_csv_data, db_path, force=True)

        # Verify import succeeded
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM base_language")
        assert cursor.fetchone()[0] == 1
        conn.close()

    def test_reimport_after_csv_change(self, minimal_csv_data, tmp_path):
        db_path = tmp_path / "test.db"

        # Initial import
        csv2sqlite(minimal_csv_data, db_path, force=True)

        # Modify CSV
        base_csv = minimal_csv_data / "625_words-base-en_us.csv"
        base_csv.write_text(
            "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
            "the cat,the cat,/ðə kæt/,,,AnkiLangs::EN\n"
            "the dog,the dog,/ðə dɒɡ/,,,AnkiLangs::EN\n"
        )

        # Reimport with force (simulates user choosing to overwrite)
        csv2sqlite(minimal_csv_data, db_path, force=True)

        # Verify both rows exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM base_language")
        assert cursor.fetchone()[0] == 2
        conn.close()


class TestCsv2SqliteFailsWhenDbHasUnsavedEdits:
    """Detects db_data_modified_at > synced_at."""

    def test_detects_unsaved_db_edits(self, minimal_csv_data, tmp_path):
        db_path = tmp_path / "test.db"

        # Initial import
        csv2sqlite(minimal_csv_data, db_path, force=True)

        # Wait to ensure trigger timestamp will be different (second precision)
        time.sleep(1.1)

        # Simulate a DB edit (triggers should update db_data_modified_at)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE base_language SET text = 'modified cat' WHERE key = 'the cat'"
        )
        conn.commit()
        conn.close()

        # Attempting to import should fail with --fail-if-conflict
        with pytest.raises(SyncConflictError) as exc_info:
            csv2sqlite(minimal_csv_data, db_path, fail_if_conflict=True)

        assert "unsaved edits" in str(exc_info.value)

    def test_force_bypasses_unsaved_edits_check(self, minimal_csv_data, tmp_path):
        db_path = tmp_path / "test.db"

        # Initial import
        csv2sqlite(minimal_csv_data, db_path, force=True)

        # Wait to ensure trigger timestamp will be different
        time.sleep(1.1)

        # Simulate a DB edit
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE base_language SET text = 'modified cat' WHERE key = 'the cat'"
        )
        conn.commit()
        conn.close()

        # Force should bypass the check
        csv2sqlite(minimal_csv_data, db_path, force=True)

        # Verify the CSV data overwrote the DB edit
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT text FROM base_language WHERE key = 'the cat'")
        assert cursor.fetchone()[0] == "the cat"
        conn.close()


class TestSqlite2CsvSucceedsWhenDbModified:
    """Normal workflow: DB has edits, we want to export them."""

    def test_export_after_db_edit(self, minimal_csv_data, tmp_path):
        db_path = tmp_path / "test.db"

        # Initial import
        csv2sqlite(minimal_csv_data, db_path, force=True)

        # Modify DB
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE base_language SET text = 'the fat cat' WHERE key = 'the cat'"
        )
        conn.commit()
        conn.close()

        # Export should succeed (DB modified, CSV unchanged since sync)
        sqlite2csv(db_path, minimal_csv_data, force=True)

        # Verify CSV was updated
        base_csv = minimal_csv_data / "625_words-base-en_us.csv"
        content = base_csv.read_text()
        assert "the fat cat" in content


class TestSqlite2CsvFailsWhenCsvModified:
    """Detects hash mismatch when CSV changed externally."""

    def test_detects_csv_changes(self, minimal_csv_data, tmp_path):
        db_path = tmp_path / "test.db"

        # Initial import
        csv2sqlite(minimal_csv_data, db_path, force=True)

        # Modify CSV externally (simulates another process or manual edit)
        base_csv = minimal_csv_data / "625_words-base-en_us.csv"
        base_csv.write_text(
            "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
            "the cat,external edit,/ðə kæt/,,,AnkiLangs::EN\n"
        )

        # Attempting to export should fail with --fail-if-conflict
        with pytest.raises(SyncConflictError) as exc_info:
            sqlite2csv(db_path, minimal_csv_data, fail_if_conflict=True)

        assert "CSV files have changed" in str(exc_info.value)

    def test_force_bypasses_csv_freshness_check(self, minimal_csv_data, tmp_path):
        db_path = tmp_path / "test.db"

        # Initial import
        csv2sqlite(minimal_csv_data, db_path, force=True)

        # Modify CSV externally
        base_csv = minimal_csv_data / "625_words-base-en_us.csv"
        base_csv.write_text(
            "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
            "the cat,external edit,/ðə kæt/,,,AnkiLangs::EN\n"
        )

        # Force should bypass the check and overwrite
        sqlite2csv(db_path, minimal_csv_data, force=True)

        # Verify CSV was overwritten with DB content
        content = base_csv.read_text()
        assert "the cat,the cat" in content
        assert "external edit" not in content
