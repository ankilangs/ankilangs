"""Tests for fix_625_words_files key synchronization across files."""

import csv

from al_tools.core import fix_625_words_files

import pytest


def _read_keys(path):
    with open(path) as f:
        return [r["key"] for r in csv.DictReader(f)]


def test_adds_missing_keys_to_base_file(tmp_path):
    """Base file with fewer keys gets the missing ones added."""
    # en_us has 3 keys, es_es has only 2
    (tmp_path / "625_words-base-en_us.csv").write_text(
        "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
        "the cat,the cat,,,AnkiLangs::EN,\n"
        "the dog,the dog,,,AnkiLangs::EN,\n"
        "the bird,the bird,,,AnkiLangs::EN,\n"
    )
    (tmp_path / "625_words-base-es_es.csv").write_text(
        "key,text:es,ipa:es,audio:es,audio source:es,tags:es\n"
        "the cat,el gato,,,AnkiLangs::ES,\n"
        "the dog,el perro,,,AnkiLangs::ES,\n"
    )

    fix_625_words_files(tmp_path)

    keys = _read_keys(tmp_path / "625_words-base-es_es.csv")
    assert "the bird" in keys
    assert len(keys) == 3


def test_adds_missing_keys_to_translation_file(tmp_path):
    """Translation pair file with fewer keys gets the missing ones added."""
    (tmp_path / "625_words-base-en_us.csv").write_text(
        "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
        "the cat,the cat,,,,\n"
        "the dog,the dog,,,,\n"
        "the bird,the bird,,,,\n"
    )
    (tmp_path / "625_words-from-en_us-to-es_es.csv").write_text(
        "key,guid,pronunciation hint,spelling hint,reading hint,listening hint,notes\n"
        "the cat,abc123,,,,,\n"
        "the dog,def456,,,,,\n"
    )

    fix_625_words_files(tmp_path)

    keys = _read_keys(tmp_path / "625_words-from-en_us-to-es_es.csv")
    assert "the bird" in keys
    assert len(keys) == 3


def test_sets_tags_column(tmp_path):
    """Tags columns are set to AnkiLangs::XX format."""
    (tmp_path / "625_words-base-fr_fr.csv").write_text(
        "key,text:fr,ipa:fr,audio:fr,audio source:fr,tags:fr\nthe cat,le chat,,,,\n"
    )

    fix_625_words_files(tmp_path)

    with open(tmp_path / "625_words-base-fr_fr.csv") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["tags:fr"] == "AnkiLangs::FR"


def test_raises_on_different_key_order(tmp_path):
    """Raises ValueError when keys exist in both files but in different order."""
    (tmp_path / "625_words-base-en_us.csv").write_text(
        "key,text:en,ipa:en,audio:en,audio source:en,tags:en\n"
        "the cat,the cat,,,,\n"
        "the dog,the dog,,,,\n"
    )
    (tmp_path / "625_words-base-es_es.csv").write_text(
        "key,text:es,ipa:es,audio:es,audio source:es,tags:es\n"
        "the dog,el perro,,,,\n"
        "the cat,el gato,,,,\n"
    )

    with pytest.raises(ValueError, match="different order"):
        fix_625_words_files(tmp_path)
