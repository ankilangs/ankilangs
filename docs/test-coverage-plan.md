# Test Coverage Improvement Plan

## Current state (2026-02-14)

108 tests, 41% line coverage. All pass.

| Module | Coverage | Assessment |
|--------|----------|------------|
| `registry.py` | 85% | Good — remaining gaps are minor edge cases |
| `core.py` | 59% | Largest module, biggest opportunity |
| `release.py` | 54% | Moderate — git/jj orchestration untested |
| `content.py` | 51% | Moderate — some generators untested |
| `i18n.py` | 38% | Small module, quick win |
| `cli.py` | 0% | Thin CLI wiring — low priority |
| `deck_creator.py` | 0% | Untested, but rarely changes |

ADR-005 priorities 1–4 are implemented. This plan covers what remains.

## Guiding principles

From ADR-005: test public interfaces and observable behavior, not internals.
Coverage is a diagnostic tool, not a goal — every new test should catch
a real class of bugs, not just paint lines green.

## Phase 1: Quick wins (i18n, export_review)

**`i18n.py`** (34 statements, 38% covered): Pure lookup functions with no
external deps. Test `get_language_name()`, `get_ui_string()`,
`get_card_type_name()`, `get_apkg_filename()` with representative locales
and missing-key edge cases. Expected: ~90%+.

**`export_review()`** in `core.py`: Set up a small SQLite DB, call
`export_review()`, assert on the generated CSV/Excel files and audio
directory. This also covers the `export_review → import_review` round-trip.

## Phase 2: Deck creator

**`deck_creator.py`** (143 statements, 0%): Test `create_625_deck()` in a
temp directory. Assert that all expected files are scaffolded (YAML, CSV,
HTML templates, changelog, description) and `decks.yaml` is updated.
Uses real filesystem, no mocks needed.

## Phase 3: Content generation gaps

**`generate_deck_overview_page()`** in `content.py`: Golden-file test
comparing output against expected markdown. Uses existing
`--update-golden` pattern.

## Phase 4: Release orchestration (lower priority)

**`create_release_commit()`, `create_git_tag()`, `create_post_release_commit()`**
in `release.py`: These shell out to git/jj. Test with `mock.patch("subprocess.run")`,
asserting on the commands issued and orchestration logic (correct version
strings, file modifications before commit). Only worth testing if this code
is actively changing.

**`regenerate_description_file()`**: Golden-file test, straightforward.

## What NOT to add

- **CLI argument parsing tests** (`cli.py`): Thin wiring, tested implicitly
  by using the tool. Only add if CLI bugs actually occur.
- **Tests for private helpers**: Covered implicitly through public function tests.
- **Coverage-only tests**: Don't add tests just to cover lines that are
  already exercised through realistic workflows.

## CI coverage gate

Set `--cov-fail-under=40` as a floor. Ratchet up as coverage improves:
- After Phase 1: raise to 45%
- After Phase 2: raise to 50%
- After Phase 3+4: raise to 55%
