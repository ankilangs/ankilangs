# ADR-005: Testing Strategy

## Status
Decided (2026-02-14)

## Context

The project has 28 tests covering CSV/SQLite sync detection, ambiguity detection, audio filename generation, import review, and changelog parsing. These tests work well but leave significant gaps:

- **No tests for external service interactions** (Google Cloud TTS, GitHub/git CLI)
- **No integration tests** for core workflows like csv2sqlite round-trips, audio generation orchestration, or release automation
- **No tests for content generation** (website pages, AnkiWeb descriptions, deck creation)

The codebase has two external dependencies that are hard to test:
1. **Google Cloud TTS** — called directly via `tts.TextToSpeechClient()` in `generate_audio()`
2. **Subprocess calls** — `git`, `jj`, `gh`, `just`, `xclip` invoked throughout `release.py`, `registry.py`, and `cli.py`

## Decision

### Testing principles

1. **Test the public interface, not internals.** Tests call the same functions users call (e.g. `csv2sqlite()`, `generate_audio()`, `validate_release()`). Never access private attributes or patch internal helper functions — this couples tests to implementation and makes them brittle during refactoring.

2. **Prefer integration-level tests.** Each test should exercise a meaningful user-facing workflow end-to-end: set up realistic inputs, call the public function, assert on observable outputs (files on disk, database state, return values, stdout). Avoid unit tests for small internal helpers — they break on every refactor and test implementation rather than behavior.

3. **Use real dependencies where cheap, fake them where expensive.** SQLite, filesystem, and CSV parsing are fast and deterministic — use them for real. Google Cloud TTS and subprocess calls to external tools are slow, costly, or require authentication — inject fakes for those.

4. **Dependency injection over patching.** Where external services need faking, add an optional parameter to the function (e.g. `tts_client=None` defaulting to the real client). This is explicit, doesn't rely on `unittest.mock.patch` magic, and makes the seam visible in the function signature. Reserve `mock.patch` for cases where changing the signature is impractical (e.g. deeply nested subprocess calls).

5. **Test behavior, not implementation.** Assert on what changed (files created, DB rows updated, output text) rather than how it changed (which internal methods were called, in what order). This means tests survive refactoring.

6. **Golden files for complex outputs.** Continue the existing pattern of golden file comparison for content generation outputs (website pages, AnkiWeb descriptions, deck descriptions). The `--update-golden` flag makes maintenance easy.

### External service boundaries

**Google Cloud TTS:** Add an optional `tts_client` parameter to `generate_audio()`. Tests pass a fake client that returns dummy audio bytes. This tests the full orchestration (DB reads, filename generation, file writing, DB updates) without API calls.

**Subprocess calls (git, jj, gh, just):** Use `mock.patch("subprocess.run")` in tests for `release.py` and `registry.py` functions that shell out. These functions are thin wrappers around CLI tools — the interesting behavior is the orchestration logic around them, not the subprocess calls themselves.

### Test organization

```
tests/
├── conftest.py                    # Shared fixtures
├── core/
│   ├── test_csv2sqlite.py         # CSV→SQLite import (existing + new)
│   ├── test_sqlite2csv.py         # SQLite→CSV export (new)
│   ├── test_csv_roundtrip.py      # CSV→SQLite→CSV preserves data (new)
│   ├── test_sync_detection.py     # Conflict detection (existing)
│   ├── test_ambiguity_detection.py # (existing)
│   ├── test_audio_generation.py   # With fake TTS client (new)
│   ├── test_audio_file_names.py   # (existing)
│   ├── test_generate.py           # generate_joined_source_fields (new)
│   ├── test_check.py              # ambiguity_detection CLI output (new)
│   ├── test_import_review.py      # (existing)
│   ├── test_export_review.py      # (new)
│   └── test_fix_625.py            # (existing)
├── content/
│   ├── test_changelog_parser.py   # (existing)
│   ├── test_content_generator.py  # Website/AnkiWeb output (new)
│   └── test_deck_creator.py       # Deck scaffolding (new)
├── release/
│   ├── test_version.py            # Version parsing and bumps (new)
│   ├── test_validate_release.py   # Release validation (new)
│   └── test_release_workflow.py   # Release + finalize orchestration (new)
└── registry/
    └── test_registry.py           # DeckRegistry loading, queries (new)
```

## Concrete test plan

### Priority 1: Core data workflows (highest value, no external deps)

**csv2sqlite / sqlite2csv round-trip**
- Import CSV files into SQLite, export back to CSV, verify files are identical
- Verify all table schemas are created correctly
- Verify deterministic CSV output (sorted rows, consistent quoting, Unix line endings)

**generate_joined_source_fields**
- Set up a minimal SQLite DB, call `generate_joined_source_fields()`, verify generated CSV files contain correct joined data

**export_review / import_review round-trip**
- Export review data for a language pair, modify it, import it back, verify DB was updated correctly
- Verify audio file deletion when text changes during import

### Priority 2: Audio generation (needs fake TTS client)

**generate_audio with fake client**
- Fake `TextToSpeechClient` that returns dummy MP3 bytes
- Verify: correct files created on disk with expected filenames
- Verify: DB updated with `[sound:filename]` references and audio source
- Verify: `skip` mode skips existing files
- Verify: `overwrite` mode replaces existing files
- Verify: `raise` mode errors on existing files
- Verify: `limit` parameter stops after N files
- Verify: TTS overrides are used when present (SSML and plain text)
- Verify: empty text rows are skipped

### Priority 3: Content generation (pure logic, no external deps)

**ContentGenerator**
- Generate website page from a Deck object, compare against golden file
- Generate AnkiWeb description, compare against golden file
- Generate GitHub release notes, verify correct changelog section extracted

**DeckCreator**
- Create a new deck, verify all expected files are created (YAML, CSV, HTML templates, changelog, description)
- Verify decks.yaml is updated with new deck entry

### Priority 4: Registry and release (needs subprocess mocking)

**DeckRegistry**
- Load registry from a test YAML file, verify all decks parsed correctly
- `get()`, `by_type()`, `by_source_locale()` return correct results
- `get_latest_release_version()` with mocked `git tag` output

**Version**
- Parse valid versions: `1.0.0`, `1.0.0-dev`
- Reject invalid versions
- Comparison: `1.0.0-dev < 1.0.0 < 1.0.1-dev`
- `next_patch_dev()`, `next_minor_dev()`, `next_major_dev()` produce correct results

**validate_version_bump**
- All valid transitions: dev→release, release→dev
- All invalid transitions rejected with clear error messages

**validate_release**
- Mock subprocess calls for `jj status` and `git tag`
- Verify: detects uncommitted changes, existing tags, missing changelog, missing description
- Verify: screenshots missing produces warning not error

**update_decks_yaml_version**
- Update version in a test YAML file, verify only the target deck's version changed and file formatting preserved

**regenerate_description_file**
- Verify description file content matches golden file

### Priority 5: CLI integration (optional, lower value)

**CLI argument parsing**
- Verify each subcommand parses its arguments correctly and calls the right function
- These are thin wiring tests — only add them if CLI bugs actually occur

## What NOT to test

- **Private helper functions** (e.g. `_compute_csv_hashes`, `_get_text_col`, `_format_source`). These are tested implicitly through the public functions that use them. Testing them directly couples tests to implementation.
- **Third-party library behavior** (pandas CSV parsing, SQLite operations, YAML loading). Trust them.
- **Exact print output** beyond golden files. Testing specific emoji or formatting in console output is fragile.

## Resolved questions

1. **Fake TTS client location.** Fakes live in `tests/fakes.py`. The fake `TextToSpeechClient` must match the real client's interface closely enough that `generate_audio` works, but doesn't need to be exhaustive.

2. **Test data size.** Most tests use minimal data (3-5 entries) for speed. At least one test per core workflow (csv2sqlite round-trip, audio generation, generate) uses a large dataset with several thousand dummy entries to catch scale-dependent issues like sorting edge cases, performance regressions, or off-by-one errors at boundaries.
