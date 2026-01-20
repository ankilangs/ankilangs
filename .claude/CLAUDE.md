# AnkiLangs Project Instructions

## Project Structure
- `src/data/`: CSV files (source of truth for language data)
- `src/note_models/`: Language-specific Anki note types (YAML + HTML templates)
- `src/media/`: Audio files and images
- `al_tools/`: Python CLI tools
- `recipes/`: Brainbrew build recipes
- `build/`: Generated Anki decks
- `data.db`: SQLite cache (git-ignored, regenerable)

## Version Control
- Use `jj` (jujutsu) if available, otherwise fall back to `git`
- Commit messages follow conventional commits format (e.g., `feat:`, `fix:`, `refactor:`)

## Python Environment
- Run Python code using `uv`

## Code Verification
Before committing code, always:
1. `just verify-code` (or individually: `just test`, `just format`, `just check`)

Before committing language data changes, always:
1. `just verify-data` (includes: export to CSV, generate, check, and build all decks)

## Language Data Management
**CRITICAL**: Never edit CSV files in `src/data/` directly. Always use this workflow:

1. Import CSV to SQLite: `just csv2sqlite` (or `uv run al-tools csv2sqlite -i src/data`)
2. Edit data using SQLite (via sqlite3, DB Browser, DBeaver, etc.) on `data.db`
3. Export back to CSV: `just sqlite2csv` (or `uv run al-tools sqlite2csv -d data.db -o src/data`)
4. Commit changes

**Supported locales**: `de_de`, `en_us`, `es_es`, `fr_fr`, `it_it`, `la_la`, `pt_pt`, `sq_al`

## Hints System
Hints disambiguate ambiguous words without revealing the translation. There are 4 card types, each with its own hint column:

**Reading hint** - User reads target word, produces source meaning
- EN→ES example: User sees "el banco" and doesn't know if it means "bank" (financial) or "bench" (sitting). Hint: `for money`

**Listening hint** - User hears target word, produces source meaning
- EN→ES example: User hears "el banco" and doesn't know if it means "bank" or "bench". Hint: `for money`

**Pronunciation hint** - User sees source word, pronounces target word
- EN→ES example: User sees "the bank" and doesn't know whether to say "el banco" (financial) or "la orilla" (river). Hint: `financial institution`

**Spelling hint** - User sees source word AND hears target word, spells target word
- Hardly ever needed: the combination of seeing meaning and hearing pronunciation removes almost all ambiguity. Only needed for target language homophones where the source language meaning is also ambiguous.

**Key insight:** Reading/Listening hints address **target language** ambiguity (what the user sees/hears). Pronunciation/Spelling hints address **source language** ambiguity (what the user must produce). These may require *different* hints for the same entry.

**Complete example - EN→ES entry for "the bank" → "el banco" (financial):**
- `pronunciation hint`: `financial institution` — EN "bank" is ambiguous (financial vs river)
- `spelling hint`: (not needed — user sees meaning and hears pronunciation)
- `reading hint`: `for money` — ES "banco" is ambiguous (bank vs bench)
- `listening hint`: `for money` — same reason

**When hints are NOT required:**
- Unambiguous words in both languages: `cat`/`gato`, `dog`/`perro`, `house`/`casa`
- When neither source nor target word has multiple common meanings

**Negative examples (DON'T do this):**
- ❌ `banco` as hint (reveals translation)
- ❌ `one meaning of bank` (too vague, useless)
- ❌ `where you put your savings` (gives away the meaning)
- ❌ `the animal` on `cat` (unnecessary, unambiguous word)

**Guidelines:**
- Only add hints when source OR target word has multiple distinct meanings
- Shorter is better, but hints can be longer if necessary
- Run `just check-data` to detect ambiguous words missing hints

## Common Commands
- `just generate`: Generate derived CSV files
- `just check-data`: Detect ambiguous words missing hints
- `just build-625`: Build main decks
- `just build-minimal-pairs`: Build minimal pairs
- `just build-all`: Build all decks
- `just test-update-golden`: Update expected test output files
- `just verify-code`: Run all code quality checks
- `just verify-data`: Run all data verification and builds
- `just verify`: Full verification (code + data)

## Useful SQLite Queries

### Database Schema Summary
- `vocabulary`: Primary keys for all words
- `base_language`: Language-specific data (key, locale, text, ipa, audio, audio_source)
- `translation_pair`: Translation metadata (key, source_locale, target_locale, hints, notes)
- `pictures`: Picture references (sparse)
- `minimal_pairs`: Minimal pair exercises

**IMPORTANT**: SQLite uses `<>` or `!=` for not-equal, but `<>` is more standard. Use `IS NULL OR column = ''` to check for empty values.

### Finding Missing Data

```sql
-- Find entries missing IPA for a specific locale
SELECT key, text
FROM base_language
WHERE locale = 'en_us'
  AND (ipa IS NULL OR ipa = '');

-- Count missing IPA by locale
SELECT locale, COUNT(*) as missing_ipa
FROM base_language
WHERE ipa IS NULL OR ipa = ''
GROUP BY locale;

-- Find entries missing audio for a specific locale
SELECT key, text
FROM base_language
WHERE locale = 'es_es'
  AND (audio IS NULL OR audio = '');

-- Count missing audio by locale
SELECT locale, COUNT(*) as missing_audio
FROM base_language
WHERE audio IS NULL OR audio = ''
GROUP BY locale;

-- Find keys missing entirely from a locale (data integrity check)
SELECT v.key
FROM vocabulary v
LEFT JOIN base_language bl ON v.key = bl.key AND bl.locale = 'it_it'
WHERE bl.key IS NULL;
```

### Statistics and Counts

```sql
-- Count total entries per locale
SELECT locale, COUNT(*) as entries
FROM base_language
GROUP BY locale
ORDER BY locale;

-- Count translation pairs by direction
SELECT source_locale, target_locale, COUNT(*) as pairs
FROM translation_pair
GROUP BY source_locale, target_locale
ORDER BY source_locale, target_locale;

-- Count entries with any type of hint
SELECT COUNT(*) as entries_with_hints
FROM translation_pair
WHERE (pronunciation_hint IS NOT NULL AND pronunciation_hint <> '')
   OR (reading_hint IS NOT NULL AND reading_hint <> '')
   OR (spelling_hint IS NOT NULL AND spelling_hint <> '')
   OR (listening_hint IS NOT NULL AND listening_hint <> '');

-- Count hints by type for a language pair
SELECT
  COUNT(CASE WHEN pronunciation_hint <> '' THEN 1 END) as pronunciation_hints,
  COUNT(CASE WHEN reading_hint <> '' THEN 1 END) as reading_hints,
  COUNT(CASE WHEN spelling_hint <> '' THEN 1 END) as spelling_hints,
  COUNT(CASE WHEN listening_hint <> '' THEN 1 END) as listening_hints
FROM translation_pair
WHERE source_locale = 'en_us' AND target_locale = 'es_es';
```

### Cross-Language Comparisons

```sql
-- Compare translations across two languages
SELECT
  bl_en.key,
  bl_en.text as english,
  bl_es.text as spanish,
  bl_en.ipa as en_ipa,
  bl_es.ipa as es_ipa
FROM base_language bl_en
JOIN base_language bl_es ON bl_en.key = bl_es.key
WHERE bl_en.locale = 'en_us' AND bl_es.locale = 'es_es'
ORDER BY bl_en.key;

-- Find words with same text in different languages (cognates)
SELECT bl1.locale, bl2.locale, bl1.text, COUNT(*) as count
FROM base_language bl1
JOIN base_language bl2 ON bl1.key = bl2.key AND bl1.text = bl2.text
WHERE bl1.locale < bl2.locale
GROUP BY bl1.locale, bl2.locale, bl1.text
HAVING count > 5;
```

### Working with Hints

```sql
-- Find all entries with pronunciation hints for a language pair
SELECT key, pronunciation_hint
FROM translation_pair
WHERE source_locale = 'en_us'
  AND target_locale = 'es_es'
  AND pronunciation_hint IS NOT NULL
  AND pronunciation_hint <> '';

-- Find entries with reading hints
SELECT key, reading_hint
FROM translation_pair
WHERE source_locale = 'en_us'
  AND target_locale = 'es_es'
  AND reading_hint IS NOT NULL
  AND reading_hint <> '';
```

### Bulk Updates

```sql
-- Update IPA for multiple entries
UPDATE base_language
SET ipa = '/newipa/'
WHERE locale = 'en_us' AND key IN ('word1', 'word2', 'word3');

-- Update audio source for a locale
UPDATE base_language
SET audio_source = 'Google TTS'
WHERE locale = 'es_es' AND (audio IS NOT NULL AND audio <> '');

-- Add a pronunciation hint
UPDATE translation_pair
SET pronunciation_hint = 'financial institution'
WHERE key = 'the bank'
  AND source_locale = 'en_us'
  AND target_locale = 'es_es';
```

## Documentation
- `docs/adr-001-sqlite-cache.md`: SQLite schema and design
- `README.md`: Full development setup and workflows
