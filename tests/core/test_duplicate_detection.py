"""Tests for duplicate key detection in ambiguity_detection."""

from al_tools.core import ambiguity_detection, csv2sqlite


def _create_base_data(data_dir, *, extra_files=None):
    """Create minimal CSV data. extra_files is a dict of filename -> content to add."""
    (data_dir / "625_words-base-en_us.csv").write_text(
        "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
        "the cat,the cat,/ðə kæt/,,,AnkiLangs::EN\n"
    )
    (data_dir / "625_words-vocabulary.csv").write_text("key,clarification\nthe cat,\n")
    if extra_files:
        for name, content in extra_files.items():
            (data_dir / name).write_text(content)


def test_detects_duplicate_keys_in_base_language(tmp_path):
    """Duplicate keys in a base language file are reported."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_base_data(data_dir)

    # Overwrite with duplicate keys
    (data_dir / "625_words-base-en_us.csv").write_text(
        "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
        "the cat,the cat,/ðə kæt/,,,AnkiLangs::EN\n"
        "the cat,the cat again,/ðə kæt/,,,AnkiLangs::EN\n"
    )

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)
    output = ambiguity_detection(db_path, data_dir, media_dir=None)

    assert "DUPLICATE KEY ERRORS FOUND" in output
    assert "625_words-base-en_us.csv" in output
    assert "'the cat'" in output


def test_detects_duplicate_keys_in_translation_pair(tmp_path):
    """Duplicate keys in a translation pair file are reported."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_base_data(
        data_dir,
        extra_files={
            "625_words-base-es_es.csv": (
                "key,text:es,ipa:es,audio:es,audio source:es,tags:es\n"
                "the cat,el gato,/el ˈɡato/,,,AnkiLangs::ES\n"
            ),
            "625_words-from-en_us-to-es_es.csv": (
                "key,guid,pronunciation hint,spelling hint,reading hint,listening hint,notes\n"
                "the cat,abc123,,,,,\n"
                "the cat,def456,,,,,\n"
            ),
        },
    )

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)
    output = ambiguity_detection(db_path, data_dir, media_dir=None)

    assert "DUPLICATE KEY ERRORS FOUND" in output
    assert "625_words-from-en_us-to-es_es.csv" in output


def test_detects_duplicate_keys_in_pictures(tmp_path):
    """Duplicate keys in the pictures file are reported."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_base_data(
        data_dir,
        extra_files={
            "625_words-pictures.csv": (
                "key,picture,picture source\n"
                "the cat,cat.jpg,Unsplash\n"
                "the cat,cat2.jpg,Pexels\n"
            ),
        },
    )

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)
    output = ambiguity_detection(db_path, data_dir, media_dir=None)

    assert "DUPLICATE KEY ERRORS FOUND" in output
    assert "625_words-pictures.csv" in output


def test_detects_duplicate_tts_overrides(tmp_path):
    """Duplicate (key, locale) pairs in tts_overrides are reported."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_base_data(
        data_dir,
        extra_files={
            "tts_overrides.csv": (
                "key,locale,tts_text,is_ssml,notes\n"
                "the cat,en_us,thuh cat,0,fix\n"
                "the cat,en_us,thee cat,0,another fix\n"
            ),
        },
    )

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)
    output = ambiguity_detection(db_path, data_dir, media_dir=None)

    assert "DUPLICATE KEY ERRORS FOUND" in output
    assert "tts_overrides.csv" in output
    assert "'the cat'" in output


def test_detects_duplicate_guids_in_minimal_pairs(tmp_path):
    """Duplicate GUIDs in minimal pairs files are reported."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_base_data(
        data_dir,
        extra_files={
            "minimal_pairs-from-en_us_to_es_es.csv": (
                "guid,text1,audio1,ipa1,meaning1,text2,audio2,ipa2,meaning2,tags\n"
                "guid1,ship,,/ʃɪp/,boat,sheep,,/ʃiːp/,animal,\n"
                "guid1,bit,,/bɪt/,piece,beat,,/biːt/,strike,\n"
            ),
        },
    )

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)
    output = ambiguity_detection(db_path, data_dir, media_dir=None)

    assert "DUPLICATE KEY ERRORS FOUND" in output
    assert "minimal_pairs-from-en_us_to_es_es.csv" in output
    assert "'guid1'" in output


def test_no_duplicates_clean_output(tmp_path):
    """No duplicate errors when data is clean."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _create_base_data(data_dir)

    db_path = tmp_path / "test.db"
    csv2sqlite(data_dir, db_path, force=True)
    output = ambiguity_detection(db_path, data_dir, media_dir=None)

    assert "DUPLICATE" not in output
