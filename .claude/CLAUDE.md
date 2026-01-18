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
