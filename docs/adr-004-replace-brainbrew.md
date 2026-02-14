# ADR-004: Replace Brain Brew with Direct SQLite to CrowdAnki Export

## Status
Draft

## Context

The project currently uses a pipeline to transform language data into Anki decks:

```
CSV files → Brain Brew → CrowdAnki JSON → Anki (via CrowdAnki plugin)
```

With ADR-001, SQLite was introduced as a working cache:

```
CSV files ↔ SQLite (editing) → CSV files → Brain Brew → CrowdAnki JSON
```

### Current Pain Points

**1. Brain Brew recipe complexity**

The `recipes/source_to_anki_625_words.yaml` file is ~1150 lines of highly repetitive YAML. Each language pair requires ~70 lines of boilerplate:
- Note model definition
- Header definition
- Media group definition
- CSV-to-field mappings
- CrowdAnki output configuration

Adding a new language pair requires copying and modifying multiple sections, which is error-prone.

**2. Limited flexibility for deck composition**

Some words should appear in some decks but not others. Examples:
- A word may not have an equivalent concept in the target language
- A word may be culturally inappropriate for certain audiences
- A word may be pending review and not ready for inclusion

Brain Brew's recipe DSL doesn't elegantly support conditional inclusion logic. The current implicit approach (empty translation = excluded) cannot distinguish between "not translated yet" and "intentionally excluded."

**3. Maintenance concerns**

Brain Brew's last release was in 2024. While functional, sparse maintenance raises long-term sustainability questions.

**4. CSV file proliferation**

The current structure optimized for Brain Brew requires many CSV files:
- One `625_words-base-{locale}.csv` per locale (~20 files)
- One `625_words-from-{src}-to-{tgt}.csv` per translation pair (~25 files)
- Generated files in `src/data/generated/` (~25 files)

This creates ~70 CSV files, many with redundant structure.

**5. Contributor accessibility**

While CSV is theoretically easy to edit, the current multi-file structure is confusing. Non-technical contributors need a simpler workflow.

**6. Note model duplication**

The `src/note_models/` directory contains ~25 subdirectories (one per language pair), each with:
- `note.yaml` - note model definition
- `style.css` - stylesheet (identical across all pairs)
- 4 HTML templates (listening, pronunciation, reading, spelling)

This totals ~150 files that are 95% identical. The only differences:
- `note.yaml`: name, UUID, and file paths
- HTML templates: language name in the `.type` div (e.g., "Spanish | Reading" vs "German | Reading")

Adding a new language pair requires copying an entire directory and doing find-replace on the language name.

### Constraints

- **CrowdAnki is non-negotiable**: It provides the bridge between version-controlled JSON and Anki itself via a well-maintained plugin.
- **Git diff readability matters**: PRs should show human-readable changes even if contributions are infrequent.
- **Data format should optimize for editing**, not for Anki's internal format.

## Decision

Replace Brain Brew with:

1. **Table-mirroring CSV files** that directly reflect SQLite tables (one CSV per table)
2. **Direct SQLite → CrowdAnki JSON export** implemented in `al_tools`
3. **Explicit deck inclusion tracking** via status columns
4. **Excel-based contribution workflow** for non-technical contributors

## New Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Table-Mirroring CSVs (git)                     │
│  vocabulary.csv, base_language.csv, translation_pair.csv   │
│  pictures.csv, minimal_pairs.csv, tts_overrides.csv        │
└─────────────────────────────────────────────────────────────┘
                          ↕ csv2sqlite / sqlite2csv
┌─────────────────────────────────────────────────────────────┐
│                   SQLite (editing cache)                    │
└─────────────────────────────────────────────────────────────┘
           │                              │
           ▼                              ▼
    ┌─────────────┐              ┌────────────────┐
    │ Excel files │              │ CrowdAnki JSON │
    │ (contrib)   │              │ (build output) │
    └─────────────┘              └────────────────┘
```

### Table-Mirroring CSV Structure

Replace the current ~70 CSV files with 6 files that mirror SQLite tables exactly:

```
src/data/
├── vocabulary.csv           # key
├── base_language.csv        # key, locale, text, ipa, audio, audio_source
├── translation_pair.csv     # key, source_locale, target_locale, status, status_note, hints..., guid
├── pictures.csv             # key, picture, picture_source
├── minimal_pairs.csv        # guid, source_locale, target_locale, text1, audio1, ...
└── tts_overrides.csv        # key, locale, override_text
```

**Advantages over current structure:**
- 1:1 mapping with SQLite (trivial import/export)
- Fewer files to manage
- No "generated" folder needed
- Clear which file contains what data

**Diff readability:**

A PR adding Spanish translations shows:
```csv
# base_language.csv
+apple,es_es,la manzana,/la manˈθana/,apple_es.mp3,Google TTS
+banana,es_es,el plátano,/el ˈplatano/,banana_es.mp3,Google TTS
```

The locale column in each row provides context within the diff.

### Explicit Deck Inclusion

Add columns to `translation_pair` for explicit inclusion control:

```sql
ALTER TABLE translation_pair ADD COLUMN status TEXT DEFAULT 'pending';
-- Values: 'pending', 'active', 'excluded'

ALTER TABLE translation_pair ADD COLUMN status_note TEXT;
-- "No equivalent concept", "Pending native speaker review", etc.
```

Deck generation query becomes:
```sql
SELECT ... FROM translation_pair tp
JOIN base_language bl_src ON tp.key = bl_src.key AND tp.source_locale = bl_src.locale
JOIN base_language bl_tgt ON tp.key = bl_tgt.key AND tp.target_locale = bl_tgt.locale
WHERE tp.status = 'active'
  AND bl_tgt.text IS NOT NULL AND bl_tgt.text <> ''
```

This cleanly separates:
- `status = 'pending'`: Not translated yet, will be included once complete
- `status = 'active'`: Ready for inclusion in deck
- `status = 'excluded'`: Intentionally omitted, with reason in `status_note`

### SQLite → CrowdAnki Export

New command: `al-tools build-deck`

```bash
al-tools build-deck --pair en_us-es_es -o build/EN_to_ES_625_Words
```

Implementation:
1. Query SQLite for active translation pairs with complete data
2. Query note model configuration from `decks.yaml` registry
3. Generate CrowdAnki JSON structure (notes, note models, deck metadata)
4. Copy referenced media files to output folder

The CrowdAnki JSON format is straightforward:
```json
{
  "__type__": "Deck",
  "crowdanki_uuid": "...",
  "name": "Spanish (EN to ES) | 625 Words | AnkiLangs.org",
  "note_models": [...],
  "notes": [...],
  "media_files": [...]
}
```

### Deck Configuration

Move deck definitions from Brain Brew recipes to `decks.yaml`:

```yaml
decks:
  en_to_es_625:
    name: "Spanish (EN to ES) | 625 Words | AnkiLangs.org"
    source_locale: en_us
    target_locale: es_es
    deck_type: "625"
    crowdanki_uuid: "f9534636-57c4-4c8c-8b48-9733d696d49a"
    note_model: vocabulary_en_to_es
    # ... other metadata already in decks.yaml
```

This consolidates configuration and eliminates recipe file duplication.

### Note Model Management

**Current state:** ~150 files across ~25 directories, 95% identical.

**New approach:** Template-based generation with shared base files.

#### Source Structure

```
src/
├── note_models/
│   ├── vocabulary/                # Template for 625-word decks
│   │   ├── fields.yaml            # Field definitions (shared by all vocabulary decks)
│   │   ├── style.css              # Stylesheet (shared)
│   │   ├── listening.html         # Card template with {{target_language_name}}, {{card_type}}
│   │   ├── pronunciation.html
│   │   ├── reading.html
│   │   └── spelling.html
│   └── minimal_pairs/             # Template for minimal pairs decks
│       ├── fields.yaml
│       ├── style.css
│       └── *.html
└── i18n/
    └── card_strings.yaml          # Localized card type names and language names
```

This reduces ~150 files to ~15 files (template sets + i18n).

#### Template Placeholders

HTML templates use placeholders for all language-specific strings:

```html
<!-- Before (per-language file): -->
<div class="type">Spanish | Reading</div>

<!-- After (template): -->
<div class="type">{{target_language_name}} | {{card_type}}</div>
```

The `{{card_type}}` must be in the **source language** (the learner's native language):
- EN→ES deck: "Spanish | Reading" (English UI)
- DE→ES deck: "Spanisch | Lesen" (German UI)
- ES→DE deck: "Alemán | Lectura" (Spanish UI)

#### Internationalization

Card type strings vary only by source language, so define them once per locale:

```yaml
# src/i18n/card_strings.yaml
en_us:
  card_types:
    reading: Reading
    listening: Listening
    pronunciation: Pronunciation
    spelling: Spelling
  # Target language names (how English speakers refer to languages)
  language_names:
    de_de: German
    es_es: Spanish
    fr_fr: French
    it_it: Italian
    # ...

de_de:
  card_types:
    reading: Lesen
    listening: Hören
    pronunciation: Aussprache
    spelling: Rechtschreibung
  language_names:
    en_us: Englisch
    es_es: Spanisch
    fr_fr: Französisch
    it_it: Italienisch
    # ...

es_es:
  card_types:
    reading: Lectura
    listening: Escucha
    pronunciation: Pronunciación
    spelling: Ortografía
  language_names:
    en_us: Inglés
    de_de: Alemán
    fr_fr: Francés
    it_it: Italiano
    # ...
```

#### Deck-Specific Configuration

Deck configuration references locales; strings are resolved from i18n:

```yaml
# decks.yaml
decks:
  en_to_es_625:
    name: "Spanish (EN to ES) | 625 Words | AnkiLangs.org"
    source_locale: en_us
    target_locale: es_es
    deck_type: "625"
    crowdanki_uuid: "f9534636-57c4-4c8c-8b48-9733d696d49a"
    note_model:
      template: vocabulary
      uuid: "ac2a1848-b0b7-4562-85a0-5826fbf6c9b2"
      name: "EN to ES | Basic | AnkiLangs.org"
      # target_language_name resolved from i18n: en_us.language_names.es_es → "Spanish"
      # card_types resolved from i18n: en_us.card_types.* → "Reading", "Listening", etc.

  de_to_es_625:
    source_locale: de_de
    target_locale: es_es
    # ...
    note_model:
      # target_language_name resolved: de_de.language_names.es_es → "Spanisch"
      # card_types resolved: de_de.card_types.* → "Lesen", "Hören", etc.
```

#### Template Resolution

At build time, for each card template (e.g., `reading.html`):

1. Load i18n strings for `source_locale`
2. Resolve `{{target_language_name}}` = `i18n[source_locale].language_names[target_locale]`
3. Resolve `{{card_type}}` = `i18n[source_locale].card_types[template_name]`
4. Substitute into HTML template

#### Build Process

`al-tools build-deck` generates note models at build time:

1. Read template from `src/note_models/{template}/`
2. Load field definitions from `fields.yaml`
3. Read CSS from `style.css`
4. For each HTML template:
   - Substitute `{{target_language}}` with configured value
   - Include front/back HTML in note model
5. Generate note model JSON with configured UUID and name
6. Embed in CrowdAnki output

#### fields.yaml Example

```yaml
fields:
  - name: Source Text
  - name: Target Text
    font: Arial
  - name: Target IPA
    font: Arial
  - name: Target Audio
    font: Arial
  - name: Picture
    font: Arial
  - name: Notes
    font: Arial
    font_size: 15
  - name: Pronunciation Hint
    font: Arial
    font_size: 15
  - name: Spelling Hint
    font: Arial
    font_size: 15
  - name: Reading Hint
    font: Arial
    font_size: 15
  - name: Listening Hint
    font: Arial
    font_size: 15
  - name: Source & License
    font: Arial
    font_size: 15

templates:
  - name: Pronunciation
    file: pronunciation.html
  - name: Spelling
    file: spelling.html
  - name: Listening
    file: listening.html
  - name: Reading
    file: reading.html

# Card generation rules (which cards to create based on field presence)
required_fields_per_template:
  Pronunciation: [[Source Text], [Picture, Pronunciation Hint]]
  Spelling: [[Source Text], [Picture, Spelling Hint]]
  Listening: [[Target Audio], [Listening Hint]]
  Reading: [[Target Text], [Reading Hint]]
```

#### Advantages

1. **Single source of truth**: Change CSS once, affects all decks
2. **Easy to add languages**: Add entry to `decks.yaml` + i18n strings, no file copying
3. **Consistent updates**: Template changes propagate to all decks on next build
4. **Reduced maintenance**: ~15 files instead of ~150
5. **Clear separation**: Presentation (templates), configuration (decks.yaml), and localization (i18n) are distinct
6. **Reusable i18n**: Card type translations defined once per source language, reused across all decks from that language

#### Migration

1. Extract one complete template set as the base (e.g., from `vocabulary_en_to_es/`)
2. Replace language-specific strings with `{{target_language}}`
3. Create `fields.yaml` from existing `note.yaml`
4. Add `note_model` section to each deck in `decks.yaml`
5. Delete per-language directories after verifying build output matches

### Contributor Workflow

For non-technical contributors, extend the existing `export-review` pattern:

**Export contribution tasks:**
```bash
# Generate Excel for adding translations
al-tools export-contribution --task translate --target ja_jp --limit 50

# Generate Excel for adding hints to ambiguous words
al-tools export-contribution --task hints --pair en_us-es_es

# Generate Excel for reviewing existing translations
al-tools export-contribution --task review --pair en_us-es_es
```

**Import contributions:**
```bash
al-tools import-contribution contributions/ja_jp_translations.xlsx --validate
al-tools import-contribution contributions/ja_jp_translations.xlsx --apply
```

Contributors never touch CSV or SQLite directly. They:
1. Download an Excel file (from GitHub release, shared folder, or generated on request)
2. Fill in their contributions
3. Upload/submit the Excel file
4. Maintainer validates and imports

## Alternatives Considered

### 1. Keep Brain Brew, manage complexity

**Approach:** Accept recipe verbosity, use code generation to maintain recipes.

**Pros:**
- No migration effort
- Brain Brew handles CrowdAnki format details

**Cons:**
- Still can't handle conditional deck inclusion elegantly
- Recipe DSL is a leaky abstraction
- Dependency on sparsely-maintained project

**Verdict:** Rejected. The abstraction doesn't fit our use case.

### 2. Fork Brain Brew

**Approach:** Fork and modify Brain Brew to support our requirements.

**Pros:**
- Incremental changes to working system

**Cons:**
- Inherit maintenance burden for code we didn't write
- Recipe DSL is the fundamental problem; forking doesn't fix it
- Would need to understand Brain Brew internals deeply

**Verdict:** Rejected. Higher effort than direct implementation with less control.

### 3. WebUI for data editing (Datasette, NocoDB, custom)

**Approach:** Provide a web interface for contributors to edit data directly.

**Pros:**
- Familiar spreadsheet-like interface
- Real-time collaboration possible

**Cons:**
- Requires hosting and authentication
- Concurrent edit conflicts need resolution
- Significant development/maintenance overhead
- Unclear if contributors actually need this vs. Excel workflow

**Verdict:** Deferred. Excel workflow should be tried first. WebUI can be added later if contributor volume justifies it.

### 4. SQL dump files instead of CSV for git

**Approach:** Version control SQL INSERT statements instead of CSV.

**Pros:**
- Still human-readable diffs
- Self-documenting (includes table names)

**Cons:**
- More verbose than CSV
- Less familiar to contributors
- Harder to edit directly if needed

**Verdict:** Rejected. CSV diffs are more compact and GitHub renders them nicely.

### 5. SQLite file directly in git (no CSV)

**Approach:** Version control the SQLite database file directly.

**Pros:**
- Single file, no conversion step
- Schema enforcement

**Cons:**
- Binary diffs not human-readable
- Merge conflicts very difficult to resolve
- PRs would show "binary file changed"

**Verdict:** Rejected. Readable diffs are important for PR review.

## Comparison: CSV Structures

| Aspect | Current (Brain Brew) | Table-Mirroring |
|--------|---------------------|-----------------|
| Number of files | ~70 | 6 |
| 1:1 with SQLite | No (complex joins) | Yes (trivial) |
| Redundancy | High (repeated structure) | None |
| Adding new locale | Create 2+ new files | Add rows to existing files |
| Diff context | Filename indicates locale | Locale column in each row |
| Generated files needed | Yes | No |

## Advantages of New Architecture

1. **Simpler data model**: 6 CSV files instead of 70
2. **Explicit inclusion control**: Clear distinction between "not yet" and "excluded"
3. **Flexible deck composition**: Query logic in code, not DSL
4. **Reduced dependencies**: Remove Brain Brew dependency
5. **Testable build process**: Python code vs. YAML recipes
6. **Contributor-friendly**: Excel workflow doesn't require understanding CSV structure
7. **Maintainable**: All logic in `al_tools`, which we control

## Disadvantages

1. **Migration effort**: One-time work to restructure CSVs and implement exporter
2. **CrowdAnki format responsibility**: Must implement JSON generation (but format is simple)
3. **Loss of Brain Brew features**: Any features we use but haven't identified (likely none)

## Migration Plan

### Phase 1: Schema Changes
1. Add `status` and `status_note` columns to `translation_pair` table
2. Update `csv2sqlite` and `sqlite2csv` to handle new columns
3. Set all existing translation pairs to `status = 'active'`

### Phase 2: CSV Restructure
1. Implement new `sqlite2csv` that outputs table-mirroring format
2. Run migration: old CSVs → SQLite → new CSVs
3. Verify data integrity (row counts, checksums)
4. Remove old CSV files and `generated/` folder
5. Update `.gitignore` if needed

### Phase 3: Note Model Templates
1. Extract base template from one existing note model (e.g., `vocabulary_en_to_es/`)
2. Replace language-specific strings with placeholders (`{{target_language_name}}`, `{{card_type}}`)
3. Create `fields.yaml` from existing `note.yaml` structure
4. Create `src/i18n/card_strings.yaml` with strings for all source locales
5. Add `note_model` section to each deck in `decks.yaml` (UUID, name, template reference)
6. Delete per-language-pair directories after verifying build output matches

### Phase 4: CrowdAnki Export
1. Implement `al-tools build-deck` command with:
   - Note model generation from templates + i18n
   - Note generation from SQLite query
   - Media file handling
2. Test output against Brain Brew output for equivalence
3. Remove Brain Brew recipes and dependency

### Phase 5: Contributor Workflow
1. Implement `export-contribution` command with task types
2. Implement `import-contribution` command with validation
3. Document contributor workflow
4. Create GitHub issue template for contributions

### Phase 6: Cleanup
1. Remove Brain Brew from dependencies
2. Delete `recipes/` directory
3. Delete old per-language note model directories
4. Update documentation and CLAUDE.md
5. Update `just build` command

## Open Questions

1. **Media file handling**: Should `build-deck` copy media files or reference them in place? Copying is safer for distribution but increases build size.

2. **GUID stability**: Brain Brew generates GUIDs for new entries. The new system needs to preserve existing GUIDs and generate stable new ones. Should GUIDs be stored in `translation_pair` (current) or computed deterministically from key + locales?

3. **Backward compatibility**: Should we maintain ability to export to Brain Brew format temporarily, or make a clean break?

4. **i18n completeness**: The i18n file needs card type names and language names for every source locale. Should missing translations fall back to English, or fail the build?
