"""Tests for DeckRegistry loading and queries."""

from pathlib import Path
from unittest import mock

import pytest

from al_tools.registry import DeckRegistry


def test_loads_all_decks(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    assert len(reg) == 3


def test_get_returns_deck(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    deck = reg.get("en_to_es_625")
    assert deck is not None
    assert deck.name == "Spanish (EN to ES) | 625 Words | AnkiLangs.org"
    assert deck.version == "0.3.0"
    assert deck.ankiweb_id == "1234567890"


def test_get_returns_none_for_missing(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    assert reg.get("nonexistent") is None


def test_raises_for_missing_file(testdata_dir):
    with pytest.raises(FileNotFoundError):
        DeckRegistry(testdata_dir / "nonexistent.yaml")


def test_raises_for_invalid_format(testdata_dir):
    with pytest.raises(ValueError):
        DeckRegistry(testdata_dir / "decks.yaml")


def test_by_type_625(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    decks = reg.by_type("625")
    assert len(decks) == 2
    assert all(d.deck_type == "625" for d in decks)


def test_by_type_minimal_pairs(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    decks = reg.by_type("minimal_pairs")
    assert len(decks) == 1
    assert decks[0].deck_id == "en_to_es_mp"


def test_by_source_locale(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    decks = reg.by_source_locale("en_us")
    assert len(decks) == 3


def test_all_returns_all(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    assert len(reg.all()) == 3


def test_iter(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    assert len(list(reg)) == 3


def test_build_folder(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    deck = reg.get("en_to_es_625")
    assert deck.build_folder == Path("build/EN_to_ES_625_Words")


def test_website_slug(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    deck = reg.get("en_to_es_625")
    assert deck.website_slug == "en-to-es-625"


def test_is_dev_version(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    assert not reg.get("en_to_es_625").is_dev_version
    assert reg.get("en_to_fr_625").is_dev_version


def test_release_version(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    assert reg.get("en_to_fr_625").release_version == "0.2.0"
    assert reg.get("en_to_es_625").release_version == "0.3.0"


def test_returns_latest_from_tags(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(
            stdout="EN_to_ES_625_Words/0.1.0\nEN_to_ES_625_Words/0.2.0\nEN_to_ES_625_Words/0.3.0\n",
            returncode=0,
        )
        version = reg.get_latest_release_version("en_to_es_625")
    assert version == "0.3.0"


def test_skips_dev_tags(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(
            stdout="EN_to_ES_625_Words/0.2.0\nEN_to_ES_625_Words/0.3.0-dev\n",
            returncode=0,
        )
        version = reg.get_latest_release_version("en_to_es_625")
    assert version == "0.2.0"


def test_returns_none_when_no_tags(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(stdout="", returncode=0)
        version = reg.get_latest_release_version("en_to_es_625")
    assert version is None


def test_returns_none_for_unknown_deck(testdata_dir):
    reg = DeckRegistry(testdata_dir / "decks.yaml")
    assert reg.get_latest_release_version("nonexistent") is None
