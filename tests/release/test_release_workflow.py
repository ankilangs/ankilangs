"""Tests for update_decks_yaml_version."""

import shutil

import pytest

from al_tools.release import update_decks_yaml_version
from tests.utils import compare_or_update_golden


def test_updates_target_deck_version(testdata_dir, golden_dir, pytestconfig, tmp_path):
    """Updating a deck version produces correct YAML with other decks unchanged."""
    path = tmp_path / "decks.yaml"
    shutil.copy(testdata_dir / "decks.yaml", path)

    update_decks_yaml_version(path, "en_to_es_625", "0.3.0")

    compare_or_update_golden(pytestconfig, golden_dir / "decks.yaml", path.read_text())


def test_raises_for_missing_file(testdata_dir):
    with pytest.raises(FileNotFoundError):
        update_decks_yaml_version(testdata_dir / "nonexistent.yaml", "foo", "1.0.0")


def test_raises_for_unknown_deck(testdata_dir, tmp_path):
    path = tmp_path / "decks.yaml"
    shutil.copy(testdata_dir / "decks.yaml", path)

    with pytest.raises(ValueError, match="not found"):
        update_decks_yaml_version(path, "nonexistent_deck", "1.0.0")


def test_updates_only_target_deck(testdata_dir, golden_dir, pytestconfig, tmp_path):
    """Updating one deck should not change the other's version."""
    path = tmp_path / "decks.yaml"
    shutil.copy(testdata_dir / "decks.yaml", path)

    update_decks_yaml_version(path, "en_to_fr_625", "0.2.1-dev")

    compare_or_update_golden(pytestconfig, golden_dir / "decks.yaml", path.read_text())
