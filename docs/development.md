# Development Documentation

This documentation is for developers who want to make complex changes to AnkiLangs. For simple contributions like fixing translations, see [CONTRIBUTING.md](../CONTRIBUTING.md) instead.

## Table of Contents

- [Setup](#setup)
  - [Linux](#linux-setup)
  - [macOS](#macos-setup)
  - [Windows (WSL)](#windows-wsl-setup)
- [Project Structure](#project-structure)
- [Data Flow](#data-flow)
- [Working with Data](#working-with-the-data)
- [Systematic Deck Review](#systematic-deck-review)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Learning Hints](#learning-hints)

## Setup

### Prerequisites

All platforms require:
- **Python 3.10+** - Programming language
- **uv** - Fast Python package installer and project manager
- **Anki** - Flashcard application (for testing decks)
- **CrowdAnki add-on** - Anki add-on for importing/exporting decks
- **Just** (optional) - Task runner for simplified commands
- **ffmpeg** (optional) - Required only for systematic deck reviews

### Linux Setup

#### Ubuntu/Debian

```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip git ffmpeg

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Just (task runner) - optional but recommended
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin

# Install Anki
# Download from https://apps.ankiweb.net/#download

# Clone repository
git clone https://github.com/ankilangs/ankilangs
cd ankilangs/

# Install Python dependencies. Done automatically by uv when running commands or run:
uv sync
```

#### Other Distros

Follow analogous instructions to the ones for Ubuntu/Debian above.


### macOS Setup

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install python git ffmpeg just

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Anki
# Download from https://apps.ankiweb.net/#download
# Or use Homebrew:
brew install --cask anki

# Clone repository
git clone https://github.com/ankilangs/ankilangs
cd ankilangs/

# Note: On macOS, you may need to delete .DS_Store files before building:
find src/media -name '.DS_Store' -delete
```

### Windows (WSL) Setup

**Recommended:** Use Windows Subsystem for Linux (WSL) for the best development experience on Windows.

#### Install WSL

1. Open PowerShell as Administrator and run:
   ```powershell
   wsl --install
   ```

2. Restart your computer when prompted

3. After restart, Ubuntu will open automatically. Create a username and password.

#### Setup Within WSL

Once inside WSL (Ubuntu), follow the Linux setup instructions from above:

#### Install Anki on Windows

Download and install Anki for Windows from https://apps.ankiweb.net/#download

**Note:** Anki runs on Windows, but development tools run in WSL. You'll build decks in WSL and import them into Anki on Windows.

### Install CrowdAnki Add-on

Regardless of your platform:

1. Open Anki
2. Go to **Tools → Add-ons → Get Add-ons**
3. Enter code: `1788670778`
4. Click **OK** and restart Anki

Documentation: https://docs.ankiweb.net/addons.html

## Project Structure

```
ankilangs/
├── src/                        # Source files (edit these)
│   ├── data/                   # CSV files - source of truth for vocabulary
│   │   ├── 625_words-base-*.csv     # Base vocabulary for each language
│   │   ├── 625_words-pair-*.csv     # Translation pairs and hints
│   │   ├── minimal_pairs-*.csv      # Minimal pair exercises
│   │   └── generated/               # Auto-generated derived files (don't edit)
│   │
│   ├── note_models/            # Anki note type definitions (YAML + HTML)
│   │   ├── EN_to_ES_625_Words/      # Note model for EN→ES deck
│   │   └── ...                      # One directory per language pair
│   │
│   ├── headers/                # Deck descriptions and metadata
│   │   ├── description_en_to_es.md  # Deck description (appears in Anki)
│   │   └── ...
│   │
│   ├── deck_content/           # Additional deck content
│   │   ├── EN_to_ES_625_Words/      # Changelogs, screenshots per deck
│   │   └── ...
│   │
│   └── media/                  # Media files
│       ├── audio/              # Audio recordings by language
│       │   ├── en_US/          # English audio files
│       │   ├── es_ES/          # Spanish audio files
│       │   └── ...
│       └── images/             # Shared images
│
├── build/                      # Generated Anki decks
│   ├── EN_to_ES_625_Words/     # Built deck ready for Anki import
│   └── review/                 # Generated review files (xlsx + mp3)
│
├── recipes/                    # Brainbrew build recipes (YAML config)
│   ├── source_to_anki_625_words.yaml       # Recipe for 625 word decks
│   └── source_to_anki_minimal_pairs.yaml   # Recipe for minimal pairs
│
├── al_tools/                   # Python CLI tools
│   ├── cli.py                  # Main CLI entry point
│   ├── core.py                 # Core data processing logic
│   └── ...
│
├── tests/                      # Test suite
│   ├── core/                   # Core functionality tests
│   └── content/                # Content validation tests
│
├── docs/                       # Documentation
│   ├── development.md          # This file
│   ├── learning-hints.md       # Learning hints guide
│   └── adr-*.md                # Architecture decision records
│
├── website/                    # AnkiLangs.org website (Hugo)
│
├── data.db                     # SQLite cache (git-ignored, regenerable)
├── pyproject.toml              # Python project configuration
├── uv.lock                     # Locked dependency versions
├── Justfile                    # Task runner commands
└── README.md                   # Project overview
```

### Key Directories Explained

**`src/data/`** - The single source of truth. All vocabulary, translations, IPA, audio references, and hints live here as CSV files. Everything else is derived from these files.

**`src/note_models/`** - Defines how Anki cards look and behave. Each language pair has its own note model with HTML templates, CSS styling, and card type definitions.

**`src/media/`** - All audio files and images. Audio files are named systematically (e.g., `al_es_es_the_house.mp3` for Spanish "la casa").

**`build/`** - Generated output. After running build commands, this contains importable Anki decks (via the CrowdAnki plugin).

**`recipes/`** - Configuration files that tell Brainbrew how to transform source files into CrowdAnki Anki decks.

**`al_tools/`** - Command-line tools for data manipulation, validation, audio generation, and more. Invoked via `uv run al-tools <command>`.

**`data.db`** - SQLite database cache for efficient data operations. Automatically regenerated from CSV files. Git-ignored because it's derivable.

## Data Flow

This diagram shows how data moves from source files to Anki decks:

```
                           EDITING WORKFLOW
                     ┌─────────────────────────────┐
                     │                             │
                     ▼                             │
              ┌─────────────┐   al-tools      ┌─────────────┐
              │  CSV files  │   csv2sqlite    │   SQLite    │
              │ (src/data/) │ ───────────────→│  (data.db)  │
              │             │ ←───────────────│             │
              └──────┬──────┘   al-tools      └─────────────┘
                     │         sqlite2csv      Edit with SQL
                     │                         tools (DB Browser,
                     │                         sqlite3, etc.)
                     │
           ┌─────────┴─────────┐
           │                   │
           ▼                   ▼
    ┌─────────────┐     ┌─────────────┐
    │ Note models │     │  al-tools   │
    │   + media   │     │  generate   │
    │  + recipes  │     └──────┬──────┘
    └──────┬──────┘            │
           │                   ▼
           │            ┌─────────────┐
           │            │  Generated  │  (joins license info
           │            │    CSVs     │   into single fields)
           │            └──────┬──────┘
           │                   │
           └────────┬──────────┘
                    │
                    ▼
             ┌─────────────┐
             │  Brainbrew  │  Transforms sources into
             │             │  CrowdAnki JSON format
             └──────┬──────┘
                    │
                    ▼
             ┌─────────────┐
             │   build/    │  CrowdAnki-compatible
             │             │  deck directories
             └──────┬──────┘
                    │
                    ▼  CrowdAnki plugin (File → Import from disk)
             ┌─────────────┐
             │    Anki     │
             └─────────────┘
```

### Tools Summary

| Tool | Command | Purpose |
|------|---------|---------|
| **al-tools csv2sqlite** | `just csv2sqlite` | Import CSV → SQLite for editing |
| **al-tools sqlite2csv** | `just sqlite2csv` | Export SQLite → CSV after editing |
| **al-tools generate** | (part of `just build`) | Create derived CSVs (license field joins) |
| **al-tools check** | `just check-data` | Validate data, find missing hints |
| **Brainbrew** | `just build` | Transform sources → CrowdAnki format |
| **CrowdAnki** | Anki menu | Import build/ directories into Anki |

### Key Points

- **CSV files are the source of truth** — they're versioned in git
- **SQLite is a convenience layer** — easier to query/edit than CSV, but not versioned
- **Generated CSVs are derived** — don't edit them; they're recreated on each build
- **build/ is output only** — import into Anki, don't edit directly

## Working with the Data

The project uses CSV files as the source of truth, but tools work with a SQLite database for efficiency.

### Initial Setup

Import CSV files into SQLite:

```bash
uv run al-tools csv2sqlite -i src/data
# Or: just csv2sqlite
```

This creates `data.db` (which is git-ignored).

### Workflow for Editing Data

1. **Import CSV to SQLite** (if not done already):
   ```bash
   just csv2sqlite
   ```

2. **Edit data**: Use SQL tools (sqlite3, DB Browser, DBeaver, etc.) to query/update `data.db`

   Example queries are in [CLAUDE.md](../.claude/CLAUDE.md#useful-sqlite-queries).

3. **Export back to CSV**:
   ```bash
   just sqlite2csv
   ```

4. **Commit changes**:
   ```bash
   git commit -m "feat: add Spanish audio for food vocabulary"
   ```

**Safety features:**
- Database auto-creates from CSV if missing
- Prompts with options if CSV files are newer than database (overwrite/ignore/cancel)

### Build Decks

To test your changes in Anki:

```bash
# Check for data issues
just check-data

# Build all decks (includes sqlite2csv + generate)
just build
```

### Import into Anki

1. Open Anki
2. Go to **File → CrowdAnki: Import from disk**
3. Select a directory from `build/` (e.g., `build/EN_to_ES_625_Words`)
4. Review the deck like any other Anki deck

## Systematic Deck Review

Generate a spreadsheet and combined audio file for comprehensive deck review:

```bash
uv run al-tools export-review -s en_us -t fr_fr
```

This creates:
- `build/review/review_en_us_to_fr_fr.xlsx` - Excel spreadsheet with all entries
- `build/review/review_en_us_to_fr_fr.mp3` - Combined audio file

Open the files:

```bash
# Linux
libreoffice build/review/review_en_us_to_fr_fr.xlsx &
vlc build/review/review_en_us_to_fr_fr.mp3

# macOS
open build/review/review_en_us_to_fr_fr.xlsx
open build/review/review_en_us_to_fr_fr.mp3

# Windows (in WSL, access files from Windows)
explorer.exe build/review/
```

**Requires:** ffmpeg (for audio concatenation)

For detailed instructions on how to use these files, see [CONTRIBUTING.md](../CONTRIBUTING.md#systematic-deck-review).

## Code Quality

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting Python code.

### Run Code Checks

Before committing code:

```bash
just check-code  # Format + lint
just test        # Run tests
```

Or run all checks (code + data):

```bash
just check
```

## Testing

Run the test suite:

```bash
uv run pytest
# Or: just test
```

Tests are in `tests/` and cover:
- Ambiguity detection algorithms
- Data processing and validation
- CSV file handling and transformations

### Update Golden Files

If you intentionally change test output:

```bash
just test-update-golden
```

## Learning Hints

Learning hints disambiguate words with multiple meanings (e.g., "light" = brightness vs. weight). There are four hint types: pronunciation, reading, spelling, and listening.

**For complete documentation with examples**, see [docs/learning-hints.md](learning-hints.md).

### Quick Example

English "race" has two meanings:
- Race (competition) → German "das Rennen"
- Race (ethnicity) → German "die Rasse"

Add a pronunciation hint to clarify:

```sql
UPDATE translation_pair
SET pronunciation_hint = 'competition'
WHERE key = 'race [sport]'
  AND source_locale = 'en_us'
  AND target_locale = 'de_de';
```

### Find Words Needing Hints

```bash
just check-data
```

This detects potentially ambiguous words missing hints.

## Creating New Decks

To create a new 625-word deck:

```bash
uv run al-tools create-deck <source_locale> <target_locale>
```

Example:

```bash
uv run al-tools create-deck it_it pt_pt  # Italian → Portuguese
```

This automatically:
- Creates note model directory with templates
- Generates localized card types
- Creates deck description and CSV files
- Updates build recipes and deck registry

After creating, add vocabulary data to the generated CSV file.

## Generating Audio

Requires Google Cloud account with authentication. See [Google Cloud docs](https://cloud.google.com/docs/authentication/set-up-adc-local-dev-environment).

```bash
# Import CSV to SQLite first
just csv2sqlite

# Generate audio for a language
uv run al-tools audio -l es_es

# Export updated database
just sqlite2csv
```

## Commit Message Conventions

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

### Types

- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code change that neither fixes a bug nor adds a feature
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks, dependency updates
- `style:` - Code style changes (formatting)

### Examples

```
feat: add pronunciation hints for Spanish bank/bench ambiguity
```

```
fix: correct IPA transcription for German "ich"
```

```
docs: update SQLite query examples in CLAUDE.md
```

## Task Runner (Just)

The `Justfile` is a modern replacement of the `Makefile`. View all commands:

```bash
just
```

**Note:** Just is optional. All commands can be run directly with `uv run`.

## Release Process

Releases are mostly automated using `al-tools release` commands.

### Prerequisites

- Deck must be registered in `decks.yaml`
- Changelog entry exists for target version in `src/deck_content/<deck>/changelog.md`
- Clean working directory (no uncommitted changes)
- `gh` CLI tool installed and authenticated (for finalization)

### Steps

1. **Update changelog** with new version entry:
   ```bash
   vim src/deck_content/en_to_es_625/changelog.md
   ```

   Add entry like:
   ```markdown
   ## 1.0.0 - 2026-02-10

   - Complete audio and IPA for all words
   - Complete hints for ambiguous words
   ```

2. **Run release automation** (validates, updates versions, creates commits/tag):
   ```bash
   al-tools release en_to_es_625 --version 1.0.0
   ```

   This will:
   - Validate release (changelog entry, clean working tree, etc.)
   - Run pre-release checks (code quality)
   - Update version to 1.0.0 and commit
   - Create git tag `EN_to_ES_625_Words/1.0.0`
   - Update version to 1.0.1-dev and commit

3. **Build the deck**:
   ```bash
   just build
   ```

4. **Export from Anki**:
   - Open Anki
   - File → CrowdAnki: Import from disk → select `build/EN_to_ES_625_Words`
   - File → Export
   - Select the deck, choose `.apkg` format
   - Include media, support older Anki versions
   - Save as `EN_to_ES_625_Words - 1.0.0.apkg`

5. **Finalize release** (creates GitHub release, generates AnkiWeb description):
   ```bash
   al-tools release en_to_es_625 --finalize ~/Downloads/EN_to_ES_625_Words\ -\ 1.0.0.apkg
   ```

   This will:
   - Create GitHub release with changelog
   - Upload .apkg file
   - Generate AnkiWeb description and copy to clipboard

6. **Push to GitHub**:
   ```bash
   jj git push
   git push --tags
   ```

7. **Update AnkiWeb**:
   - Visit https://ankiweb.net/shared/upload
   - Upload the .apkg file
   - Paste description from `build/ankiweb_description_<deck_id>.md`

### Dry Run

Validate without making changes:

```bash
al-tools release en_to_es_625 --version 1.0.0 --dry-run
```

### Troubleshooting

- **Validation fails**: Fix errors shown (e.g., add changelog entry, commit changes)
- **Wrong version**: Use proper semver format (X.Y.Z) without -dev suffix
- **Build fails**: Run `just check-data` to validate data quality
- **gh CLI not found**: Install from https://cli.github.com/

## Tips & Tricks

### Listen to Changed Audio Files

```bash
# Files from specific commit
cvlc `git diff --name-only --diff-filter=d c6d7af^ src/media/audio/`

# Uncommitted changes
cvlc `git diff --name-only --diff-filter=d src/media/audio/`
```

Requires VLC (tested on Linux).

## Large Changes

For significant structural changes, please [open an issue](https://github.com/ankilangs/ankilangs/issues/new/choose) first to discuss. This avoids wasted effort if the approach doesn't fit the project.

## Further Reading

- [ADR-001: SQLite Cache](adr-001-sqlite-cache.md) - Database schema and design
- [ADR-002: Audio Filenames](adr-002-audio-filenames.md) - Audio file naming conventions
- [Learning Hints Guide](learning-hints.md) - Complete guide to using hints
