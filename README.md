# AnkiLangs

The aim of this project is collaborating in the creation of high quality, free
and open source Anki decks for language learning. Check the website for more
details [AnkiLangs.org](https://ankilangs.org).

AnkiLangs is not part of nor necessarily endorsed by Anki (https://apps.ankiweb.net/).

This is a [monorepo](https://en.wikipedia.org/wiki/Monorepo) containing everything.


## Try it out

Download decks:

* [AnkiLangs | EN to DE | 625 Words (Beta)](https://github.com/ankilangs/ankilangs/releases/download/EN_to_DE_625_Words%2F0.0.1-beta/AnkiLangs._.EN.to.DE._.625.Words.apkg)
* [AnkiLangs | EN to PT | 625 Words (Beta)](https://github.com/ankilangs/ankilangs/releases/download/EN_to_PT_625_Words%2F0.0.1-beta/AnkiLangs._.EN.to.PT._.625.Words.apkg)


## Contribute changes

Edit the CSV files under `src/data/`. CSV files can be imported into Microsoft Excel or LibreOffice
Calc in order to edit them.

If you want to add or modify media files (e.g. audio) you must do so in the `src/media/` directory.

For example:
* The "Portuguese 625 words" deck contains a typo → you should edit `src/data/EN to PT - 625 Words.csv`.
* A German audio recording for the word "Flugzeug" is incorrect → you should replace the file `src/media/audio/de_DE/al_de_de_das_flugzeug.ogg`

If there are any large structural changes you want to make or anything else that involves a lot of
work on your side, please open a [new issue](https://github.com/ankilangs/ankilangs/issues/new/choose)
first in order to discuss it! Otherwise you risk investing much work only to get it rejected, which
is very frustrating.


### Send a pull request

In order for you modification to become part of the project you must send a PR (pull request) as documented
[here](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).


## Build

If you want you can build the decks (i.e. convert the CSV files into Anki decks).
Note that you do not need to do this in order to make a contribution. If you want to improve a deck
you can stick to the "Contribute changes" section above and leave the complicated stuff to us 🙂.

To build the decks you need the following:

* Python 3 ([Installation](https://wiki.python.org/moin/BeginnersGuide/Download)).
* Pipenv ([Installation](https://pipenv.pypa.io/en/latest/installation/)).
* Anki ([Installation](https://apps.ankiweb.net/#download)).
* Within Anki the [CrowdAnki add-on](https://ankiweb.net/shared/info/1788670778) (code 1788670778).
  [Add-on installation](https://docs.ankiweb.net/addons.html).

```bash
pipenv sync
pipenv run brainbrew run recipes/source_to_anki.yaml
```

Open Anki and via `File / CrowdAnki: Import from disk` import any of the `build/` subdirectories of this
Git repository.

Then you may review them like any deck.


### To create a new deck

Copy existing files:

```bash
cp "src/headers/Header EN to PT - 625 Words.yaml" "src/headers/Header DE to ES - 625 Words.yaml"
cp -r "src/note_models/AnkiLangs EN to PT" "src/note_models/AnkiLangs DE to ES"
```

Edit those new files.

Generate new UUIDs using the command:

```bash
python3 -c "import uuid; print(uuid.uuid4())"
```

* header file (`src/headers/Header DE to ES - 625 Words.yaml`)
  * `crowdanki_uuid`
  * `desc`
  * `name`
* note models (`src/note_models/AnkiLangs DE to ES`)
  * Rename the .yaml file
  * Search and replace `EN to PT` with `DE to ES` everywhere
  * `id` in the .yaml file
  * Search and replace `Portuguese` with `Spanisch` in the .html files
  * Search and replace `| Listening` and similar in the .html files

Create a file in `src/data` with at least one entry. Copy the format of one of
the existing files. Note that the first column (guid) is generated
automatically so leave it blank.

Edit `recipes/source_to_anki.yaml` and copy and edit multiple blocks in there.
