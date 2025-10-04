"""
Test file name normalisation from vocabulary items

Ensure that generated MP3 files have very tame non-whitespace ASCII file names.
"""


def test_avoid_spaces():
    """
    Whitespace should be replaced with underscores.
    """
    from al_tools.core import _create_mp3_filename

    output = _create_mp3_filename("el coche", "al_es_es_")

    assert output == "al_es_es_el_coche.mp3"


def test_normalise_case():
    """
    The file name should be only in lower case.
    """
    from al_tools.core import _create_mp3_filename

    output = _create_mp3_filename("la Tierra", "al_es_es_")

    assert output == "al_es_es_la_tierra.mp3"


def test_remove_diacritics():
    """
    Diacritics should be normalised by keeping the letter but without the diacritics.
    """
    from al_tools.core import _create_mp3_filename

    output = _create_mp3_filename("el pájaro", "al_es_es_")

    assert output == "al_es_es_el_pajaro.mp3"
