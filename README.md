# AnkiLangs

AnkiLangs monorepo containing everything.

Currently it's a work in progress and the other repositories are being
migrated here.


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

TODO Does not work currently.

### Edit as CSV

Edit the content of the directories `src/data/` and `src/media/` .

### Send a pull request

Via
[GitHub](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).
