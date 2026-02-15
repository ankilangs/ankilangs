# ADR-006: CSV-Based Internationalization

## Status
Decided (2026-02-15)

## Context

The project stores UI strings, language names, and card type labels in `al_tools/i18n.py` as hardcoded Python dictionaries (~800 lines of code). This includes:

- **Language names**: How to say "Spanish" in German, French, etc. (~290 entries)
- **UI strings**: Labels like "Download deck", "Changelog", etc. (~400 entries)
- **Card types**: "Listening", "Pronunciation", etc. (~60 entries)

Problems with the current approach:

1. **Code as data** — Translation updates require editing Python code
2. **Hard to contribute** — Contributors must understand Python syntax
3. **Not reviewable** — Translation changes mixed with code changes in diffs
4. **No tooling** — Cannot use standard translation platforms
5. **ASCII workarounds** — Comments like `# ASCII-safe (no umlaut)` indicate encoding concerns drove decisions
6. **Inconsistent** — Different workflow from vocabulary data (which uses CSV)

## Decision

Store i18n data in CSV files under `src/data/i18n/`, following the same patterns as vocabulary data:

```
src/data/i18n/
  language_names.csv   # source_locale, target_locale, name
  ui_strings.csv       # locale, key, value
  card_types.csv       # locale, card_type, name
```

These files are imported into SQLite tables by `csv2sqlite` and exported by `sqlite2csv`, mirroring the vocabulary workflow.

## CSV Schemas

### language_names.csv

How to say each language name in each source language.

| Column | Description | Example |
|--------|-------------|---------|
| source_locale | The language the name is written in | `de_de` |
| target_locale | The language being named | `es_es` |
| name | The localized name | `Spanisch` |

### ui_strings.csv

UI labels and messages.

| Column | Description | Example |
|--------|-------------|---------|
| locale | Target locale | `de_de` |
| key | String identifier | `download_deck` |
| value | Localized string | `Stapel herunterladen` |

### card_types.csv

Card type display names.

| Column | Description | Example |
|--------|-------------|---------|
| locale | Target locale | `de_de` |
| card_type | Card type key | `listening` |
| name | Localized name | `Hörverständnis` |

## SQLite Schema

```sql
CREATE TABLE i18n_language_names (
    source_locale TEXT NOT NULL,
    target_locale TEXT NOT NULL,
    name TEXT NOT NULL,
    PRIMARY KEY (source_locale, target_locale)
);

CREATE TABLE i18n_ui_strings (
    locale TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (locale, key)
);

CREATE TABLE i18n_card_types (
    locale TEXT NOT NULL,
    card_type TEXT NOT NULL,
    name TEXT NOT NULL,
    PRIMARY KEY (locale, card_type)
);
```

## Implementation

The `i18n.py` module changes from ~800 lines of data dictionaries to ~100 lines of loader code:

1. On first access, load data from SQLite into memory
2. Provide the same API: `get_language_name()`, `get_ui_string()`, `get_card_type_name()`
3. Fall back to English (en_us) if a translation is missing

## Workflow

Same as vocabulary data:

1. `just csv2sqlite` — Import CSV to SQLite
2. Edit via SQL tools (sqlite3, DB Browser, etc.)
3. `just sqlite2csv` — Export back to CSV
4. Commit CSV changes

## Alternatives Considered

### gettext/PO files

**Pros**: Industry standard, excellent tooling (Weblate, POEdit)
**Cons**: Overkill for ~750 simple strings, different workflow from vocabulary, no plural/gender needs

### JSON files per locale

**Pros**: Standard format, widely supported
**Cons**: Language names matrix awkward to represent, harder to review all translations of one key

### Keep hardcoded Python

**Cons**: Current pain points remain, inconsistent with vocabulary workflow

## Advantages

1. **Consistent workflow** — Same CSV/SQLite pattern as vocabulary
2. **Easy contribution** — No Python knowledge needed
3. **Clear diffs** — Translation changes visible in CSV diffs
4. **Reviewable** — All translations of a key visible in one place
5. **Familiar tooling** — Contributors already use SQLite for vocabulary

## Migration

1. Export current dictionaries to CSV files
2. Update `csv2sqlite` and `sqlite2csv` to handle i18n tables
3. Rewrite `i18n.py` to load from database
4. Delete hardcoded dictionaries
