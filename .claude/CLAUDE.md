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

**Supported locales**: `de_de`, `en_us`, `es_es`, `fr_fr`, `it_it`, `la_la`, `pt_pt`, `sq_sq`

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

## Documentation
- `docs/adr-001-sqlite-cache.md`: SQLite schema and design
- `README.md`: Full development setup and workflows
