# Development

This is documentation for making complex changes to the projects and it requires some technical expertise. If you simply want to make small improvements like fixing an incorrect translation check out [CONTRIBUTING.md](../CONTRIBUTING.md) instead.

## Setup

**Required:**
* Python 3 ([Installation](https://wiki.python.org/moin/BeginnersGuide/Download)).
* uv ([Installation](https://docs.astral.sh/uv/getting-started/installation/)).
* Anki ([Installation](https://apps.ankiweb.net/#download)).
* Within Anki the [CrowdAnki add-on](https://ankiweb.net/shared/info/1788670778) (code 1788670778).
  [Add-on installation](https://docs.ankiweb.net/addons.html).

**Optional:**
* Just - Task runner for simplified commands ([Installation](https://github.com/casey/just#installation)).

```bash
git clone https://github.com/ankilangs/ankilangs
cd ankilangs/
```

## Working with the Data

The project uses CSV files as the source of truth, but tools work with a SQLite database for efficiency.

### Initial Setup

First, import the CSV files into SQLite:

```bash
uv run al-tools csv2sqlite -i src/data
# Or: just csv2sqlite
```

This creates `data.db` (which is gitignored).

### Build the decks

If you want you can build the decks (i.e. convert the CSV files into Anki decks).
Note that you do not need to do this in order to make a contribution. If you want to improve a deck
you can stick to the "Contribute changes" section above and leave the complicated stuff to us 🙂.

```bash
uv run al-tools generate -o src/data/generated
uv run al-tools check
uv run brainbrew run recipes/source_to_anki_minimal_pairs.yaml
uv run brainbrew run recipes/source_to_anki_625_words.yaml
```

Or with Just:
```bash
just build-all
```

Open Anki and via `File / CrowdAnki: Import from disk` import any of the `build/` subdirectories of this
Git repository.

Then you may review them like any deck.

### Workflow for Editing Data

1. **Import CSV to SQLite** (if not done already):
   ```bash
   uv run al-tools csv2sqlite -i src/data
   # Or: just csv2sqlite
   ```

2. **Edit data**: Use SQL tools (sqlite3, DB Browser, DBeaver, etc.) to query/update `data.db`

3. **Export back to CSV**:
   ```bash
   uv run al-tools sqlite2csv -d data.db -o src/data
   # Or: just sqlite2csv
   ```

4. **Commit changes**: `jj commit` the modified CSV files

The database includes safety checks:
- Auto-creates database from CSV files if it doesn't exist
- Prompts with options if CSV files are newer than the database (overwrite/ignore/cancel)


## Code Quality

To maintain code quality, this project uses [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting Python code.

To check for linting issues:
```bash
uv run ruff check .
# Or: just check
```

To automatically format all Python files:
```bash
uv run ruff format .
# Or: just format
```

To run all code quality checks (format + check + test):
```bash
just verify-code
```

## Testing

This project uses [pytest](https://docs.pytest.org/) for testing. To run the test suite:

```bash
uv run pytest
# Or: just test
```

The tests are located in the `tests/` directory and cover core functionality including:
- Ambiguity detection algorithms
- Data processing and validation
- CSV file handling and transformations


## Task Runner (Optional)

This project includes a [`Justfile`](https://github.com/casey/just) for common tasks. If you have Just installed, you can use simplified commands:

```bash
# See all available commands
just

# Run tests
just test

# Format and check code
just format
just check

# Run all code quality checks
just verify-code

# Build all decks
just build-all

# Full verification (code + data)
just verify
```

All recipes in the Justfile are optional shortcuts. You can always use the direct `uv run` commands shown throughout this document instead.


## To create a new 625 words deck

* Copy and adapt one of the directories in `src/note_models/`

```bash
# Probably leave the following unchanged
export AL_SRC_NAME="en_to_pt"
export AL_SRC_NAME_2="EN to PT"
export AL_SRC_LANG_NAME="Portuguese"
export AL_SRC_LISTENING="Listening"
export AL_SRC_PRONUNCIATION="Pronunciation"
export AL_SRC_READING="Reading"
export AL_SRC_SPELLING="Spelling"

# CHANGE ME!
export AL_DST_NAME="de_to_fr"
export AL_DST_NAME_2="DE to FR"
export AL_DST_LANG_NAME="Französisch"
export AL_DST_LISTENING="Listening"
export AL_DST_PRONUNCIATION="Pronunciation"
export AL_DST_READING="Reading"
export AL_DST_SPELLING="Spelling"
## Use the following if the source language is not EN
#export AL_DST_LISTENING="Hörverständnis"
#export AL_DST_PRONUNCIATION="Aussprache"
#export AL_DST_READING="Leseverständnis"
#export AL_DST_SPELLING="Rechtschreibung"


cp "src/headers/description_${AL_SRC_NAME}-625_words.html" \
  "src/headers/description_${AL_DST_NAME}-625_words.html"

cp -r "src/note_models/vocabulary_${AL_SRC_NAME}" \
  "src/note_models/vocabulary_${AL_DST_NAME}"

sed -i "s/id: .*/id: `uv run python -c "import uuid; print(uuid.uuid4())"`/" \
  "src/note_models/vocabulary_${AL_DST_NAME}/note.yaml"

find "src/note_models/vocabulary_${AL_DST_NAME}/" -type f \
  -exec sed -i "s/${AL_SRC_NAME}/${AL_DST_NAME}/g" {} +

find "src/note_models/vocabulary_${AL_DST_NAME}/" -type f \
  -exec sed -i "s/${AL_SRC_NAME_2}/${AL_DST_NAME_2}/g" {} +

find "src/note_models/vocabulary_${AL_DST_NAME}/" -type f \
  -exec sed -i "s/${AL_SRC_LANG_NAME}/${AL_DST_LANG_NAME}/g" {} +

find "src/note_models/vocabulary_${AL_DST_NAME}/" -type f \
  -exec sed -i "s/| ${AL_SRC_LISTENING}/| ${AL_DST_LISTENING}/g" {} +

find "src/note_models/vocabulary_${AL_DST_NAME}/" -type f \
  -exec sed -i "s/| ${AL_SRC_PRONUNCIATION}/| ${AL_DST_PRONUNCIATION}/g" {} +

find "src/note_models/vocabulary_${AL_DST_NAME}/" -type f \
  -exec sed -i "s/| ${AL_SRC_READING}/| ${AL_DST_READING}/g" {} +

find "src/note_models/vocabulary_${AL_DST_NAME}/" -type f \
  -exec sed -i "s/| ${AL_SRC_SPELLING}/| ${AL_DST_SPELLING}/g" {} +
```

Edit the deck description file:

```bash
vim "src/headers/description_${AL_DST_NAME}-625_words.html"
```

To generate new UUIDs you can use this command:

```bash
uv run python -c "import uuid; print(uuid.uuid4())"
```

Edit `recipes/source_to_anki_625_words.yaml`:
* Add the new source files under `generate_guids_in_csvs`
* Copy a block under `note_models_from_yaml_part` and:
  * Edit the `part_id` and `file`
* In the `headers_from_yaml_part` section copy a block and:
  * Edit the `part_id`
  * Edit the `name`
  * Replace `crowdanki_uuid` with a new UUID
  * Set the path of the `deck_description_html_file`
* In the `notes_from_csvs` section copy a block and:
  * Adapt all strings to the new language
* Copy a `generate_crowd_anki` section and replace all strings with the new
  language

Create the new CSV files you need under `src/data/` by copying and adapting
existing files. Note that the `guid` columns must stay empty since they have
to be unique and will automatically be generated during build.


## Generate Audio files

You need a Google Cloud account and need to be
[authenticated](https://cloud.google.com/docs/authentication/set-up-adc-local-dev-environment).

Make sure you have imported the CSV files to SQLite first:

```bash
uv run al-tools csv2sqlite -i src/data
```

Then execute, for example:

```bash
uv run al-tools audio -l de_de -o src/media/audio/de_DE/
uv run al-tools audio -l pt_pt -o src/media/audio/pt_PT/
uv run al-tools audio -l it_it -o src/media/audio/it_IT/
uv run al-tools audio -l fr_fr -o src/media/audio/fr_FR/
uv run al-tools audio -l en_us -o src/media/audio/en_US/
uv run al-tools audio -l es_es -o src/media/audio/es_ES/
```

After audio generation, export the updated database back to CSV:

```bash
uv run al-tools sqlite2csv -d data.db -o src/data
```


## Release

To release a deck do the following:

* Update the version in the `src/headers/description*` file
* Build as described above
* Update the version in the `src/headers/description*` file to the next dev version
* Import the deck into Anki
* Export from Anki:
  * Include media
  * Support older Anki versions
* Rename the exported deck so it ends with the version e.g. `- 0.0.1`
* Add a new Git tag
* Create a release on GitHub with the exported deck
* Update the README and website with download links


## Tips & Tricks

To listen to all audio files modified or added in a particular commit (requires VLC to be installed and only tested on Linux):

```bash
# Files added or modified in commit c6d7af
cvlc `git diff --name-only --diff-filter=d c6d7af^ src/media/audio/`

# Or for currently uncommitted changes:
cvlc `git diff --name-only --diff-filter=d src/media/audio/`
```
