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
1. `just check-code && just test`

Before committing language data changes, always:
1. `just build` (exports to CSV, generates, and builds all decks)

## Language Data Management
**CRITICAL**: Never edit CSV files in `src/data/` directly. Always use this workflow:

1. Import CSV to SQLite: `just csv2sqlite` (or `uv run al-tools csv2sqlite -i src/data`)
2. Edit data using SQLite (via sqlite3, DB Browser, DBeaver, etc.) on `data.db`
3. Export back to CSV: `just sqlite2csv` (or `uv run al-tools sqlite2csv -d data.db -o src/data`)
4. Commit changes

## Adding Translations for a Locale

When populating translations and IPA for a locale, follow this workflow:

1. **Check current state**:
   ```sql
   SELECT COUNT(*) as total,
          COUNT(CASE WHEN text IS NOT NULL AND text <> '' THEN 1 END) as with_text,
          COUNT(CASE WHEN ipa IS NOT NULL AND ipa <> '' THEN 1 END) as with_ipa
   FROM base_language WHERE locale = 'xx_xx';
   ```

2. **Get missing entries in database order** (process in batches of 50-70):
   ```sql
   SELECT bl_en.key
   FROM base_language bl_en
   LEFT JOIN base_language bl_xx ON bl_en.key = bl_xx.key AND bl_xx.locale = 'xx_xx'
   WHERE bl_en.locale = 'en_us'
     AND (bl_xx.text IS NULL OR bl_xx.text = '')
   ORDER BY bl_en.key COLLATE NOCASE
   LIMIT 60;
   ```

3. **Add translations with UPDATE statements** (both text and IPA required):
   ```sql
   UPDATE base_language SET text = 'translation', ipa = '/aɪpiːeɪ/'
   WHERE locale = 'xx_xx' AND key = 'the word';
   ```

4. **Verify completion** (repeat step 1 until all entries are filled)

**Guidelines**:
- Always process entries in database order (`ORDER BY key COLLATE NOCASE`) rather than imposing a custom order
- IPA must be enclosed in forward slashes: `/ˈɛksæmpəl/`
- Use standard IPA symbols for the target language
- Both `text` and `ipa` columns must be populated for every entry

## Audio Generation

Generate audio files using Google Cloud Text-to-Speech:

```bash
uv run al-tools audio -l <locale>
```

**Action modes** (`-a` flag):
- `skip` (default): Only generate missing audio files
- `overwrite`: Regenerate all audio files (caution: API costs)
- `raise`: Error if audio file already exists

**Options**:
- `--limit N`: Generate only N files (useful for testing/costs)
- `--delay N`: Seconds between API calls (default: 1.0)
- `--seed N`: Random seed for reproducible voice selection (default: 42)

**Examples**:
```bash
# Generate missing audio for Russian
uv run al-tools audio -l ru_ru -a skip

# Regenerate specific file: delete it first, then generate
rm src/media/audio/ru_RU/al_ru_ru_the_lock.mp3
uv run al-tools audio -l ru_ru -a skip
```

### TTS Overrides

Use TTS overrides to fix pronunciation issues (stress, homophones, etc.) without changing the displayed text.

**Workflow for fixing pronunciation**:

1. Import CSV to SQLite: `just csv2sqlite`
2. Add TTS override to `tts_overrides` table:
   ```sql
   INSERT INTO tts_overrides (key, locale, tts_text, is_ssml, notes)
   VALUES ('the lock', 'ru_ru', 'замо́к', 0, 'Stress on second syllable (lock) not first (castle)');
   ```
3. Export to CSV: `just sqlite2csv`
4. Delete old audio file: `rm src/media/audio/ru_RU/al_ru_ru_the_lock.mp3`
5. Regenerate audio: `uv run al-tools audio -l ru_ru -a skip`

**TTS override techniques**:
- **Stress marks**: Use Unicode combining acute accent (U+0301) after stressed vowel
  - Example: `замо́к` (lock, stress on о) vs `за́мок` (castle, stress on а)
- **SSML**: Set `is_ssml = 1` and use SSML markup in `tts_text`
- **Alternate spelling**: Use phonetic spelling that TTS pronounces correctly

**Database schema**:
- `tts_overrides` table: (key, locale, tts_text, is_ssml, notes)
- When a TTS override exists, `tts_text` is sent to TTS instead of `base_language.text`

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
- ❌ `60 minutes` for "the hour" (too specific, essentially defines the word — use `unit of time` instead)

**Guidelines:**
- Only add hints when source OR target word has multiple distinct meanings
- Hints should help the user pick between the ambiguous meanings, NOT define the word. The right level of specificity is the minimum needed to distinguish the options (e.g., `device` vs `unit of time` for clock/hour, NOT `tells the time` vs `60 minutes`)
- Shorter is better, but hints can be longer if necessary
- Run `just check-data` to detect ambiguous words missing hints

## Testing Guidelines
Follow the testing guidelines in `docs/development.md`.

## Common Commands
- `just build`: Build all decks (includes sqlite2csv + generate)
- `just check`: Run all checks (code + data)
- `just check-code`: Format and lint code
- `just check-data`: Detect ambiguous words missing hints
- `just test`: Run tests
- `just test-update-golden`: Update expected test output files

## Useful SQLite Queries

### Database Schema Summary
- `vocabulary`: Primary keys for all words (key, clarification)
- `base_language`: Language-specific data (key, locale, text, ipa, audio, audio_source)
- `translation_pair`: Translation metadata (key, source_locale, target_locale, hints, notes)
- `pictures`: Picture references (sparse)
- `minimal_pairs`: Minimal pair exercises

**Note**: The `key` and `clarification` fields in `vocabulary` are internal identifiers and metadata — they do NOT appear on the final Anki cards. They exist only for data management purposes. To help learners disambiguate ambiguous words on cards, use the **hints** in `translation_pair` (see Hints System above).

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
ORDER BY locale COLLATE NOCASE;

-- Count translation pairs by direction
SELECT source_locale, target_locale, COUNT(*) as pairs
FROM translation_pair
GROUP BY source_locale, target_locale
ORDER BY source_locale COLLATE NOCASE, target_locale COLLATE NOCASE;

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
ORDER BY bl_en.key COLLATE NOCASE;

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
- `docs/development.md`: Workflows and instructions for developers
