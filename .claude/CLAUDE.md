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
1. Run tests: `uv run pytest`
2. Format: `uv run ruff format .`
3. Check: `uv run ruff check .`

Before committing language data changes, always:
1. Export data to CSV: `uv run al-tools sqlite2csv -d data.db -o src/data`
2. Generate derived data `uv run al-tools generate -o src/data/generated`
3. Verify data: `uv run al-tools check`
4. Ensure the build is successful:
  - `uv run brainbrew run recipes/source_to_anki_625_words.yaml`
  - `uv run brainbrew run recipes/source_to_anki_minimal_pairs.yaml`

## Language Data Management
**CRITICAL**: Never edit CSV files in `src/data/` directly. Always use this workflow:

1. Import CSV to SQLite: `uv run al-tools csv2sqlite -i src/data`
2. Edit data using SQLite (via sqlite3, DB Browser, DBeaver, etc.) on `data.db`
3. Export back to CSV: `uv run al-tools sqlite2csv -d data.db -o src/data`
4. Commit changes

**Supported locales**: `de_de`, `en_us`, `es_es`, `fr_fr`, `it_it`, `la_la`, `pt_pt`, `sq_sq`

## Common Commands
- `uv run al-tools generate -o src/data/generated`: Generate derived CSV files
- `uv run al-tools check`: Detect ambiguous words missing hints
- `uv run brainbrew run recipes/source_to_anki_625_words.yaml`: Build main decks
- `uv run brainbrew run recipes/source_to_anki_minimal_pairs.yaml`: Build minimal pairs
- `uv run pytest --update-golden`: Update expected test output files

## Documentation
- `docs/adr-001-sqlite-cache.md`: SQLite schema and design
- `README.md`: Full development setup and workflows
