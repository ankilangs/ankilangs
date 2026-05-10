"""Tests for Version parsing, comparison, and bumps."""

import pytest

from al_tools.release import Version


class TestVersionParsing:
    def test_parse_release(self):
        v = Version.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert not v.is_dev

    def test_parse_dev(self):
        v = Version.parse("1.0.0-dev")
        assert v.major == 1
        assert v.minor == 0
        assert v.patch == 0
        assert v.is_dev

    def test_parse_invalid(self):
        with pytest.raises(ValueError):
            Version.parse("not-a-version")

    def test_parse_incomplete(self):
        with pytest.raises(ValueError):
            Version.parse("1.0")

    def test_str_release(self):
        assert str(Version(1, 2, 3, is_dev=False)) == "1.2.3"

    def test_str_dev(self):
        assert str(Version(1, 0, 0, is_dev=True)) == "1.0.0-dev"


class TestVersionComparison:
    def test_dev_less_than_release(self):
        assert Version.parse("1.0.0-dev") < Version.parse("1.0.0")

    def test_release_not_less_than_dev(self):
        assert not (Version.parse("1.0.0") < Version.parse("1.0.0-dev"))

    def test_lower_version_less_than_higher(self):
        assert Version.parse("1.0.0") < Version.parse("1.0.1-dev")

    def test_ordering_chain(self):
        versions = [
            Version.parse("1.0.0-dev"),
            Version.parse("1.0.0"),
            Version.parse("1.0.1-dev"),
            Version.parse("1.0.1"),
            Version.parse("1.1.0-dev"),
        ]
        for i in range(len(versions) - 1):
            assert versions[i] < versions[i + 1]

    def test_equality(self):
        assert Version.parse("1.0.0") == Version.parse("1.0.0")
        assert Version.parse("1.0.0-dev") == Version.parse("1.0.0-dev")
        assert Version.parse("1.0.0") != Version.parse("1.0.0-dev")


class TestVersionBumps:
    def test_next_patch_dev(self):
        v = Version.parse("1.0.0")
        assert str(v.next_patch_dev()) == "1.0.1-dev"

    def test_next_minor_dev(self):
        v = Version.parse("1.2.3")
        assert str(v.next_minor_dev()) == "1.3.0-dev"

    def test_next_major_dev(self):
        v = Version.parse("1.2.3")
        assert str(v.next_major_dev()) == "2.0.0-dev"

    def test_to_release(self):
        v = Version.parse("1.0.0-dev")
        assert str(v.to_release()) == "1.0.0"
