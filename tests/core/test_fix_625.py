from pytest import raises


def test_duplicate_keys(testdata_dir, tmpdir, golden_dir):
    from al_tools.core import fix_625_words_files

    with raises(Exception) as excinfo:
        fix_625_words_files(testdata_dir)

    assert "Duplicate keys found in '625_words-base-fr_fr.csv'" in str(excinfo.value)
