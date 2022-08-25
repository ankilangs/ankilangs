# AnkiLangs - DE German

Decks for learning German.

Currently there is only one deck for [minimals
pairs](https://en.wikipedia.org/wiki/Minimal_pair).

## Import into Anki

Install the [CrowdAnki plugin](https://ankiweb.net/shared/info/1788670778)
(code 1788670778) and then import the
`build/AnkiLangs___EN_to_DE___Minimal_Pairs/` directory of this Git repository as
it is.

Then you may use it to review like any deck.

## Contribute changes

### Edit in Anki

Edit the cards in Anki and then export with the CrowdAnki plugin, overwriting
the directory `build/AnkiLangs___EN_to_DE___Minimal_Pairs/` .

### Edit as CSV

Edit the content of the directories `src/data/` and `src/media/` .

### (Optional) Synchronize the changes

The CrowdAnki JSON and the CSV representation should always be in sync. That is
what [Brain Brew](https://github.com/ohare93/brain-brew) is used for. If you
want you can install it and execute the commands below, otherwise you can also
send the pull request directly and someone else will do the rest.

```bash
pip install brain-brew
brain-brew run recipes/source_to_anki.yaml  # To convert CSV to JSON
brain-brew run recipes/anki_to_source.yaml  # To convert JSON to CSV
```

### Send a pull request

Via
[GitHub](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).
