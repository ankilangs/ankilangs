import pytest


@pytest.mark.parametrize(
    "word, filename",
    [
        # Whitespace should be replaced with underscores
        ("el coche", "al_es_es_el_coche.mp3"),
        # Lower case only
        ("la Tierra", "al_es_es_la_tierra.mp3"),
        # Keep the letter but not the diacritics
        ("el pájaro", "al_es_es_el_pajaro.mp3"),
    ],
)
def test_file_name(word, filename):
    """
    Test file name normalisation from vocabulary items

    Ensure that generated MP3 files have very tame non-whitespace ASCII file names.
    """
    from al_tools.core import create_mp3_filename

    output = create_mp3_filename(word, "al_es_es_")
    assert output == filename
