# AnkiLangs

The aim of this project is collaborating in the creation of high quality, free
and open source Anki decks for language learning. Check the website for more
details [AnkiLangs.org](https://ankilangs.org).

This is a monorepo containing everything.


## Build

```bash
pipenv sync
pipenv run brainbrew run recipes/source_to_anki.yaml
```


## Import into Anki

Install the [CrowdAnki plugin](https://ankiweb.net/shared/info/1788670778)
(code 1788670778) and then import any of the `build/` subdirectories of this
Git repository.

Then you may review them like any deck.


## Contribute changes

### Edit in Anki

Does not work currently. [#1](https://github.com/ankilangs/ankilangs/issues/1).

### Edit as CSV

Edit the content of the directories `src/data/` and `src/media/` .

### Send a pull request

Via
[GitHub](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).
