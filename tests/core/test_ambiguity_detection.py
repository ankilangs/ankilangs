def test_basic_french_fille(testdata_dir, tmpdir, golden_dir):
    from al_tools.core import ambiguity_detection, csv2sqlite

    db_path = tmpdir / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)
    output = ambiguity_detection(db_path, testdata_dir, media_dir=None)

    assert (
        output
        == """The following ambiguous words were found in the file '625_words-from-de_de-to-fr_fr.csv':
  - 'la fille' has the key(s) ('the daughter', 'the girl') and missing column(s) ('reading hint', 'listening hint')
The following ambiguous words were found in the file '625_words-from-fr_fr-to-de_de.csv':
  - 'la fille' has the key(s) ('the daughter', 'the girl') and missing column(s) ('pronunciation hint',)
"""
    )


def test_basic_french_fille_fixed(testdata_dir, tmpdir, golden_dir):
    from al_tools.core import ambiguity_detection, csv2sqlite

    db_path = tmpdir / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)
    output = ambiguity_detection(db_path, testdata_dir, media_dir=None)

    assert output == ""


def test_basic_french_no_ambiguity(testdata_dir, tmpdir, golden_dir):
    from al_tools.core import ambiguity_detection, csv2sqlite

    db_path = tmpdir / "test.db"
    csv2sqlite(testdata_dir, db_path, force=True)
    output = ambiguity_detection(db_path, testdata_dir, media_dir=None)

    assert output == ""
