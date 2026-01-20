# ADR-001: SQLite Cache for CSV Data Operations

## Status
Decided (2026-01-17)

## Context

The project stores all vocabulary data in CSV files which serve as the single source of truth. This allows:
- Version control via Git
- Editing via Excel/spreadsheet tools
- Human-readable diffs

However, certain operations are difficult with raw CSV files:
- Finding rows with missing data (e.g., words lacking translations)
- Updating specific columns for a subset of rows
- Cross-file queries (e.g., comparing translations across languages)
- Maintaining consistent CSV formatting (sorting, quoting)

Recent pain points include:
- Replacing audio and license columns for 10 specific Spanish words
- Finding all entries lacking a particular translation
- Maintaining deterministic CSV output to minimize Git merge conflicts

## Decision

Introduce an ephemeral SQLite database as a working cache with scripts to:
1. Import all CSV files into SQLite
2. Export SQLite tables back to CSV with deterministic formatting

CSV files remain the source of truth. The SQLite DB is disposable and can be regenerated at any time.

## CSV File Structure

### File Types

| File Pattern | Purpose | Row Count |
|-------------|---------|-----------|
| `625_words-base-{locale}.csv` | Base vocabulary per language | 629 |
| `625_words-from-{src}-to-{tgt}.csv` | Translation pair metadata | 629 |
| `625_words-pictures.csv` | Picture references | 2 (sparse) |
| `minimal_pairs-from-{src}-to-{tgt}.csv` | Minimal pair exercises | 6 |
| `generated/*.csv` | Derived files (not imported) | varies |

### Current Locales
`de_de`, `en_us`, `es_es`, `fr_fr`, `it_it`, `la_la`, `pt_pt`, `sq_al`

### Relationships
```
key (string) is the universal primary key across all tables

Translation Pair ──────┬──────> Base Language (source)
                       └──────> Base Language (target)

Pictures ─────────────────────> Base Language (any)
```

## Proposed SQLite Schema

```sql
-- Core vocabulary entries (one row per concept)
CREATE TABLE vocabulary (
    key TEXT PRIMARY KEY
);

-- Language-specific data (one row per key-language combination)
-- Note: tags column omitted - generated deterministically on export as "AnkiLangs::{LANG_CODE_UPPER}"
CREATE TABLE base_language (
    key TEXT NOT NULL,
    locale TEXT NOT NULL,  -- e.g., 'de_de', 'en_us'
    text TEXT,
    ipa TEXT,
    audio TEXT,
    audio_source TEXT,
    PRIMARY KEY (key, locale),
    FOREIGN KEY (key) REFERENCES vocabulary(key)
);

-- Translation pair metadata
CREATE TABLE translation_pair (
    key TEXT NOT NULL,
    source_locale TEXT NOT NULL,
    target_locale TEXT NOT NULL,
    guid TEXT,
    pronunciation_hint TEXT,
    spelling_hint TEXT,
    reading_hint TEXT,
    listening_hint TEXT,
    notes TEXT,
    PRIMARY KEY (key, source_locale, target_locale),
    FOREIGN KEY (key) REFERENCES vocabulary(key)
);

-- Pictures (sparse, only some keys have pictures)
CREATE TABLE pictures (
    key TEXT PRIMARY KEY,
    picture TEXT,
    picture_source TEXT,
    FOREIGN KEY (key) REFERENCES vocabulary(key)
);

-- Minimal pairs (separate concept, not linked by key)
CREATE TABLE minimal_pairs (
    guid TEXT PRIMARY KEY,
    source_locale TEXT NOT NULL,
    target_locale TEXT NOT NULL,
    text1 TEXT,
    audio1 TEXT,
    ipa1 TEXT,
    meaning1 TEXT,
    text2 TEXT,
    audio2 TEXT,
    ipa2 TEXT,
    meaning2 TEXT,
    tags TEXT
);

-- Metadata about import
CREATE TABLE _meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

**Schema notes:**
- Normalized design for easier cross-language queries
- `tags` column omitted from `base_language` - generated on export as `AnkiLangs::{LANG_CODE_UPPER}` (e.g., de_de → AnkiLangs::DE)
- Single table to update for bulk operations across languages
- Foreign key relationships enforce referential integrity

## Example Queries

```sql
-- Find all Spanish words missing audio
SELECT key, text FROM base_language
WHERE locale = 'es_es' AND (audio IS NULL OR audio = '');

-- Find all entries missing German translation
SELECT v.key FROM vocabulary v
LEFT JOIN base_language bl ON v.key = bl.key AND bl.locale = 'de_de'
WHERE bl.key IS NULL;

-- Update audio for specific Spanish words
UPDATE base_language
SET audio = '[sound:new_file.mp3]', audio_source = 'New Source'
WHERE locale = 'es_es' AND key IN ('word1', 'word2', 'word3');

-- Compare translations across languages for a word
SELECT locale, text FROM base_language WHERE key = 'the car';

-- Find words with translation hints (non-empty)
SELECT key, source_locale, target_locale, pronunciation_hint
FROM translation_pair
WHERE pronunciation_hint IS NOT NULL AND pronunciation_hint != '';
```

## CSV Export Format

To minimize Git merge conflicts, exported CSVs must be deterministic:

1. **Sorting**: Rows sorted alphabetically by `key` column
2. **Quoting**: Use quotes only when necessary (contains comma, quote, or newline)
3. **Line endings**: Unix-style LF (`\n`)
4. **Header**: Always present, columns in fixed order
5. **Empty values**: Empty string, not NULL representation
6. **Encoding**: UTF-8 without BOM

### Column Order (preserved from original)

Base files: `key`, `text:{lang}`, `ipa:{lang}`, `audio:{lang}`, `audio source:{lang}`, `tags:{lang}`

Translation pairs: `key`, `guid`, `pronunciation hint`, `spelling hint`, `reading hint`, `listening hint`, `notes`

## Workflow

```
┌─────────────┐   uv run al-tools      ┌─────────────┐
│  CSV Files  │      csv2sqlite        │   SQLite    │
│   (truth)   │ ─────────────────────> │   (cache)   │
└─────────────┘                        └─────────────┘
                                              │
                  ┌───────────────────────────┘
                  │
                  │ All tools now read from SQLite:
                  │ - generate (creates generated/)
                  │ - check (ambiguity detection)
                  │ - audio (TTS generation)
                  │
                  v
┌─────────────┐   uv run al-tools      ┌─────────────┐
│  CSV Files  │      sqlite2csv        │   SQLite    │
│   (truth)   │ <───────────────────── │   (cache)   │
└─────────────┘                        └─────────────┘
```

1. **Initial import**: `uv run al-tools csv2sqlite -i src/data` creates `data.db`
2. **Edit**: Use SQL (CLI, GUI tool, or Python) to make changes
3. **Work**: All al-tools commands now use the SQLite database
4. **Export** (if edited): `uv run al-tools sqlite2csv -d data.db -o src/data` overwrites CSV files
5. **Commit**: `jj commit` the changed CSV files

The SQLite DB is gitignored. It can persist for convenience but is always rebuildable.

**Important**: Tools that read data (`generate`, `check`, `audio`) will:
- Check if database exists, abort with clear message if not
- Check if database is stale (CSV files modified after last import)
- Prompt user to confirm if database may be out of sync

## Implementation

All functionality is implemented in `al_tools/core.py` and exposed via `al_tools/cli.py`:

### `al-tools csv2sqlite`
- Reads all CSV files from `src/data/` (excluding `generated/`)
- Populates normalized tables with proper schema
- Tracks import timestamp in `_meta` table
- Idempotent: can re-run safely (clears and reimports)
- Usage: `uv run al-tools csv2sqlite -i src/data -d data.db`

### `al-tools sqlite2csv`
- Exports each locale back to its base file
- Exports each translation pair to its file
- Exports pictures and minimal pairs files
- Sorts all rows case-insensitively by key (with case-sensitive tie-breaking)
- Uses consistent CSV formatting (Unix line endings, minimal quoting)
- Usage: `uv run al-tools sqlite2csv -d data.db -o src/data`

### `al-tools sort-csv`
- Sorts CSV files case-insensitively by first column (key or guid)
- Used for normalizing existing CSV files
- Usage: `uv run al-tools sort-csv -i src/data`

### Database Safety Checks
All commands that read from the database include:
- `_ensure_db_exists()`: Aborts with helpful message if database not found
- `_check_db_freshness()`: Compares CSV mtimes with import timestamp, prompts user if stale

## Alternatives Considered

### 1. DuckDB
**Pros**: Query CSV directly without conversion, fast, SQL support
**Cons**: Still need export step for edits, less tooling than SQLite, overkill for this dataset size

### 2. Pandas scripts
**Pros**: Simple, no schema to maintain
**Cons**: Need to write custom script for each operation, no persistent query interface

### 3. csvkit / q
**Pros**: Command-line SQL on CSV
**Cons**: Limited editing capability, awkward for updates

### 4. Keep current approach
**Cons**: Proven difficult for targeted edits, inconsistent CSV formatting

## Advantages of SQLite Approach

1. **Familiar SQL syntax** for queries and updates
2. **GUI tools available** (DB Browser for SQLite, DBeaver, etc.)
3. **Atomic transactions** for multi-row updates
4. **Validation via constraints** (foreign keys, NOT NULL)
5. **Consistent export** solves CSV formatting issues
6. **Cross-language queries** become trivial

## Disadvantages

1. **Two-step workflow**: Must remember to export after changes
2. **Drift risk**: CSV and DB can diverge if not careful
3. **Schema maintenance**: Must update scripts when CSV structure changes
4. **Learning curve**: Team must understand the workflow

## Migration Plan

1. Sort all existing CSV files alphabetically by key (one-time normalization)
2. Implement and test `csv2sqlite.py`
3. Implement and test `sqlite2csv.py` (round-trip must match sorted CSVs)
4. Add `data.db` to `.gitignore`
5. Document workflow in README
