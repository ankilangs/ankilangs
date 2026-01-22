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

When developing on a Mac, it might be necessary to delete any .DS_Store files before running the commands above.
Simply run:
``` bash
find src/media -name '.DS_Store' -delete
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

Use the `create-deck` command to automatically generate all necessary files:

```bash
uv run al-tools create-deck <source_locale> <target_locale>
```

For example, to create a German to French deck:

```bash
uv run al-tools create-deck de_de fr_fr
```

Or an Italian to Portuguese deck:

```bash
uv run al-tools create-deck it_it pt_pt
```

This command will:
* Create the note model directory with all HTML templates and CSS
* Generate properly localized card types (e.g., "Hörverständnis" for German source)
* Create the deck description file
* Create an empty CSV file with proper headers
* Create the deck content directory with changelog and screenshots folder
* Update `recipes/source_to_anki_625_words.yaml`
* Update `decks.yaml` registry

The command validates that both locales are supported and automatically handles all string localization.

After creating the deck, add vocabulary data to the generated CSV file and follow the workflow described above.


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
