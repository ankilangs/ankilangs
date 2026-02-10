# Release Automation Plan

Plan for implementing automated deck releases via `al-tools release`.

## Goals

1. **Single source of truth**: All content (changelogs, descriptions, screenshots) maintained once, generated to multiple destinations
2. **Minimal manual steps**: Automate everything except Anki GUI export and AnkiWeb upload
3. **Consistent presence**: Each deck gets a GitHub release, website page, and AnkiWeb listing with consistent information

## Distribution Channels

Each deck is available through three channels:

| Channel | Download | Description | Changelog | Screenshots | Update Method |
|---------|----------|-------------|-----------|-------------|---------------|
| **GitHub Release** | `.apkg` attachment | Brief, links to website | Latest version only | None | `gh` CLI (automated) |
| **Website Page** | Deep link to GH release + AnkiWeb link | Full | Full history | Embedded | Generated from source files |
| **AnkiWeb** | AnkiWeb hosting | Full + latest changes | Link to website | Raw GitHub URLs | Manual copy-paste |

## Current State

**What's implemented:**
- `decks.yaml` registry with all 24 decks (versions, AnkiWeb IDs, locales, etc.)
- `src/deck_content/` with `description.md` and `changelog.md` for each deck
- `al-tools generate-website` generates Hugo deck pages from source content
- `al-tools generate-ankiweb` generates AnkiWeb descriptions with clipboard support
- `al-tools release --list` shows deck status overview
- `ChangelogParser` for extracting version blocks from changelog files
- i18n system for localized UI strings on deck pages
- Hugo website with per-deck pages at `website/content/decks/{slug}/`
- Deck overview page grouped by source language

**What's NOT yet implemented:**
- `al-tools release <deck> --version` (core release automation)
- `al-tools release <deck> --finalize` (GitHub release creation)
- Version bump automation
- VCS commit/tag creation
- Pre-release validation checks

**Current manual release process** (until automation is complete):
1. Update changelog with new version entry
2. Edit description HTML to set release version
3. Run `al-tools generate`, `al-tools check`, `brainbrew run`
4. Edit description HTML to set next dev version
5. Import deck into Anki GUI, export as `.apkg`
6. Create git tag, create GitHub release with `.apkg` attachment
7. Run `al-tools generate-website` and `al-tools generate-ankiweb`
8. Update AnkiWeb deck description (copy-paste) and upload `.apkg`

**Versioning:**
- Independent versions per deck stored in `decks.yaml` and `src/headers/description_*.html`
- Git tags follow `{DeckName}/{version}` pattern (e.g., `EN_to_ES_625_Words/1.0.0`)
- Development versions use `-dev` suffix (e.g., `1.1.0-dev`)

## Design

### 1. Content Architecture (Single Source of Truth)

All content lives in structured source files. Generated artifacts derive from these.

```
src/deck_content/
├── en_to_es_625/
│   ├── description.md           # Deck-specific pitch/description
│   ├── changelog.md             # Version history (append-only)
│   ├── notes.md                 # Deck-specific notes/known issues (optional)
│   └── screenshots/
│       ├── pronunciation_q.png
│       ├── pronunciation_a.png
│       ├── listening_q.png
│       ├── listening_a.png
│       ├── reading_q.png
│       ├── reading_a.png
│       ├── spelling_q.png
│       └── spelling_a.png
├── de_to_fr_625/
│   └── ...
└── en_to_de_minimal_pairs/
    └── ...
```

**Why per-deck screenshots?** Screenshots differ by language pair (different scripts, word lengths, right-to-left languages). Even for similar language pairs, card content differs.

**Changelog format** (`changelog.md`):

```markdown
## 0.3.0 - 2026-01-15

- Fixed typo in 'izquierda'
- Added disambiguation hints for 12 ambiguous words
- Added audio for 50 new words

## 0.2.0 - 2025-12-01

- Initial public release
- 200 words with audio, IPA, and translations
```

Machine-parseable: each `## X.Y.Z - YYYY-MM-DD` header starts a version block.

**Description format** (`description.md`):

```markdown
Learn the 625 most important Spanish words as an English speaker.

This deck uses spaced repetition to help you master vocabulary through four card types: pronunciation, listening, reading, and spelling.

**Note:** This deck is actively developed. Some words may not yet have audio.
```

### 2. Deck Registry

**File:** `decks.yaml`

```yaml
decks:
  en_to_es_625:
    name: "Spanish (EN to ES) | 625 Words | AnkiLangs.org"
    tag_name: "EN_to_ES_625_Words"
    description_file: "src/headers/description_en_to_es-625_words.html"
    content_dir: "src/deck_content/en_to_es_625"
    version: "1.1.0-dev"
    ankiweb_id: 673955494
    deck_type: "625"
    source_locale: "en_us"
    target_locale: "es_es"

  en_to_de_minimal_pairs:
    name: "German | Minimal Pairs | AnkiLangs.org"
    tag_name: "EN_to_DE_Minimal_Pairs"
    description_file: "src/headers/description_en_to_de-minimal_pairs.html"
    content_dir: "src/deck_content/en_to_de_minimal_pairs"
    version: "0.3.0-dev"
    ankiweb_id: 276400423
    deck_type: "minimal_pairs"
    source_locale: "en_us"
    target_locale: "de_de"
```

**Derived values (not stored):**
- `build_folder`: `build/{tag_name}`
- `website_slug`: `en-to-es-625` (derived from deck_id)
- `github_download_url`: computed from tag_name and version
- `screenshot_urls`: computed from content_dir for raw GitHub URLs

### 3. Generated Artifacts

From the source content, we generate:

#### 3.1 Website Deck Page

**Location:** `website/content/decks/{slug}/_index.md`

Generated from: `description.md` + `changelog.md` + `notes.md` + screenshots

Generated by `al-tools generate-website`. Uses Hugo shortcodes for internal links (`{{< ref >}}`) and frontmatter params (`{{< param >}}`):

```markdown
---
title: "Spanish (EN to ES) | 625 Words"
deck_id: en_to_es_625
version: "1.0.0"
download_url: "https://github.com/ankilangs/ankilangs/releases/download/EN_to_ES_625_Words%2F1.0.0/..."
ankiweb_url: "https://ankiweb.net/shared/info/673955494"
weight: 10
---

# Spanish (EN to ES) | 625 Words

**Latest release:** 1.0.0 (2026-01-21)

Learn the 625 most important Spanish words as an English speaker.

[Download deck]({{< param download_url >}})

Also available on [AnkiWeb]({{< param ankiweb_url >}}). If you enjoy this deck, please rate and review it there to help others find it!

See [Installation Instructions]({{< ref "/installation" >}}) and [Learning Tips]({{< ref "/learning-tips" >}}).

## Screenshots

![Pronunciation - Question](screenshots/pronunciation_q.png)
![Pronunciation - Answer](screenshots/pronunciation_a.png)
...

## Changelog

### 1.0.0 - 2026-01-21

- Complete audio and IPA for all words
- Complete hints for ambiguous words

### 0.2.0 - 2025-01-22

- Initial public release
```

#### 3.2 GitHub Release Notes

Generated from: latest changelog section + installation link

```markdown
## What's Changed

- Complete audio and IPA for all words
- Complete hints for ambiguous words

## Installation

Download the `.apkg` file below and import into Anki (File → Import).

Also available on [AnkiWeb](https://ankiweb.net/shared/info/673955494). If you like this deck, please rate and review it there!

**Full changelog & documentation:** https://ankilangs.org/decks/en-to-es-625/
```

#### 3.3 AnkiWeb Description

Generated from: description + latest changelog + screenshots + links

```markdown
Learn the 625 most important Spanish words as an English speaker.

This deck uses spaced repetition to help you master vocabulary through four card types: pronunciation, listening, reading, and spelling.

If you find this deck useful, please rate it and leave a review to help other learners find it!

See [ankilangs.org/decks/en-to-es-625](https://ankilangs.org/decks/en-to-es-625/) for full documentation, learning tips, and to report issues.

Check [AnkiLangs.org](https://ankilangs.org/) for more decks and to help improve this deck.

<div>
  <img src="https://raw.githubusercontent.com/ankilangs/ankilangs/main/src/deck_content/en_to_es_625/screenshots/pronunciation_q.png" width="400" alt="Pronunciation card - Question">
  <img src="https://raw.githubusercontent.com/ankilangs/ankilangs/main/src/deck_content/en_to_es_625/screenshots/pronunciation_a.png" width="400" alt="Pronunciation card - Answer">
</div>

[View all screenshots](https://ankilangs.org/decks/en-to-es-625/#screenshots)

**Version: 1.0.0 (2026-01-21)** ([changelog](https://ankilangs.org/decks/en-to-es-625/#changelog))

### What's New in 1.0.0

- Complete audio and IPA for all words
- Complete hints for ambiguous words
```

**Why include latest changes directly?** Users on AnkiWeb see the description before deciding to download. Showing recent improvements directly (rather than just linking) helps them decide.

### 4. CLI Commands

#### `al-tools release <deck_id> [--version VERSION]`

Main release command. Automates everything except Anki GUI steps.

```
$ al-tools release en_to_es_625 --version 1.1.0

[1/8] Validating release...
  ✓ Deck 'en_to_es_625' found
  ✓ Version bump 1.1.0-dev → 1.1.0 is valid
  ✓ No uncommitted changes
  ✓ Tag EN_to_ES_625_Words/1.1.0 does not exist
  ✓ Changelog entry for 1.1.0 exists

[2/8] Running pre-release checks...
  ✓ Tests pass
  ✓ Lint clean
  ✓ Ambiguity check passed

[3/8] Updating version to 1.1.0...
  ✓ Updated decks.yaml
  ✓ Updated src/headers/description_en_to_es-625_words.html

[4/8] Building deck...
  ✓ al-tools generate
  ✓ brainbrew run (or al-tools build-deck once ADR-004 is implemented)

[5/8] Generating website page...
  ✓ Generated website/content/decks/en-to-es-625/_index.md

[6/8] Creating commit and tag...
  ✓ jj commit: "release: EN_to_ES_625_Words 1.1.0"
  ✓ git tag: EN_to_ES_625_Words/1.1.0

[7/8] Updating to next dev version (1.1.1-dev)...
  ✓ Updated decks.yaml
  ✓ Updated description file
  ✓ jj commit: "chore: bump en_to_es_625 to 1.1.1-dev"

[8/8] Manual steps required:
  → Import deck from: build/EN_to_ES_625_Words
  → Export as: EN_to_ES_625_Words - 1.1.0.apkg
  → Then run: al-tools release en_to_es_625 --finalize <path-to-apkg>
```

#### `al-tools release <deck_id> --finalize <apkg_path>`

Completes release after manual Anki export.

```
$ al-tools release en_to_es_625 --finalize ~/Downloads/EN_to_ES_625_Words.apkg

[1/3] Validating .apkg file...
  ✓ File exists and is valid

[2/3] Creating GitHub release...
  ✓ Release EN_to_ES_625_Words/1.1.0 created
  ✓ Uploaded EN_to_ES_625_Words - 1.1.0.apkg

[3/3] Generating AnkiWeb description...
  ✓ Written to: build/ankiweb_description_en_to_es_625.md

Done!
  GitHub Release: https://github.com/ankilangs/ankilangs/releases/tag/EN_to_ES_625_Words%2F1.1.0

Manual steps:
  → Push tags: git push --tags
  → Update AnkiWeb: upload .apkg and paste description from build/ankiweb_description_en_to_es_625.md
```

#### `al-tools generate-ankiweb <deck_id>`

Generates AnkiWeb description for any deck (useful for updating description without full release).

```
$ al-tools generate-ankiweb en_to_es_625

✓ Written to: build/ankiweb_description_en_to_es_625.md
✓ Copied to clipboard

Paste this into AnkiWeb deck description.
```

#### `al-tools generate-website [--deck DECK_ID | --all]`

Regenerates website pages from source content.

```
$ al-tools generate-website --all

✓ Generated website/content/decks/en-to-es-625/_index.md
✓ Generated website/content/decks/en-to-fr-625/_index.md
...
✓ Generated 24 deck pages + overview
```

#### `al-tools release --list`

Shows status of all decks.

```
$ al-tools release --list

DECK                    VERSION      LAST RELEASE    ANKIWEB
en_to_es_625            1.1.0-dev    1.0.0           ✓ 673955494
de_to_fr_625            0.3.0-dev    0.2.0           ✓ 453325701
en_to_de_minimal_pairs  0.3.0-dev    0.2.0           ✓ 276400423
en_to_sq_625            0.1.0-dev    -               ✗ (not uploaded)
```

### 5. Version Bump Logic

**Automatic detection (if `--version` not specified):**

```python
def suggest_version(current: str, commits_since_release: list[str]) -> str:
    """
    Suggest next version based on conventional commits.
    - feat: → minor bump
    - fix:  → patch bump
    - BREAKING CHANGE: → major bump
    """
```

**Validation rules:**

| Current        | Allowed Bumps                      |
|----------------|-------------------------------------|
| `0.2.0-dev`    | `0.2.0`, `0.3.0`, `1.0.0`          |
| `0.2.0`        | `0.2.1-dev`, `0.3.0-dev`, `1.0.0-dev` |
| `1.0.0-dev`    | `1.0.0`, `1.1.0`, `2.0.0`          |

**Pre-release validation includes:**
- Changelog entry exists for the version being released
- Screenshots exist in content_dir (warn if missing)
- description.md exists and is non-empty

### 6. Description File Sync

The `description_*.html` files (used by brainbrew for in-Anki deck description) stay in sync with `decks.yaml`. This sync is performed as part of the release flow (step 3), not as a separate command.

**Template approach:**

```html
Learn the 625 most important Spanish words if you already speak English.
Note that this deck is not finished!
<b>Version: </b>{{version}} ({{release_date}})
Check <a href="{{deck_url}}">here</a> for deck updates or <a href="https://ankilangs.org">AnkiLangs.org</a> for more decks.
```

### 7. Pre-release Validation

```python
def validate_release(deck_id: str) -> list[str]:
    errors = []
    warnings = []

    # Hard errors
    if has_uncommitted_changes():
        errors.append("Uncommitted changes exist")
    if tag_exists(deck.tag_name, deck.version):
        errors.append(f"Tag already exists")
    if not changelog_has_version(deck, deck.version):
        errors.append(f"No changelog entry for {deck.version}")
    if not description_exists(deck):
        errors.append("Missing description.md")

    # Soft warnings
    if not screenshots_exist(deck):
        warnings.append("No screenshots found - AnkiWeb description will lack images")
    if not deck.ankiweb_id:
        warnings.append("No AnkiWeb ID - deck not yet uploaded to AnkiWeb")

    return errors, warnings
```

### 8. VCS Operations (jj/jujutsu)

**Commit strategy:**

```bash
# Release commit (tagged)
jj commit -m "release: EN_to_ES_625_Words 1.1.0"

# Post-release commit
jj commit -m "chore: bump en_to_es_625 to 1.1.1-dev"
```

**Tag format:**

```bash
git tag EN_to_ES_625_Words/1.1.0
```

**Push strategy:** Tags are NOT automatically pushed. The `--finalize` step reminds you to push.

### 9. Screenshot Management

**Per-deck screenshots** in `src/deck_content/{deck_id}/screenshots/`.

**Naming convention:**
- `{card_type}_q.png` - Question side
- `{card_type}_a.png` - Answer side
- Card types: `pronunciation`, `listening`, `reading`, `spelling`

**For AnkiWeb:** Screenshots are referenced via raw GitHub URLs:
```
https://raw.githubusercontent.com/ankilangs/ankilangs/main/src/deck_content/en_to_es_625/screenshots/pronunciation_q.png
```

**Important:** These URLs use the `main` branch. Screenshots should be committed before release so the URLs work immediately.

**Screenshot creation workflow:**
1. Take screenshots in Anki
2. Save to `src/deck_content/{deck_id}/screenshots/`
3. Commit to main
4. URLs now work in AnkiWeb description

### 10. Website Integration

**Structure:**

```
website/content/
├── _index.md                    # Main page (links to deck pages, no direct downloads)
├── decks/
│   ├── _index.md                # Deck listing/overview page grouped by source language
│   ├── en-to-es-625/
│   │   ├── _index.md            # Generated deck page
│   │   └── screenshots/         # Symlink or copy of source screenshots
│   └── ...
└── docs/
    └── ...
```

**Deck overview page (`decks/_index.md`):** Generated by `al-tools generate-website --all`. Lists all decks grouped by source language with version info. Section headers and intro text are localized per source language.

**Individual deck pages:** Generated from source content. Include:
- Description
- Download button (deep link to GitHub release)
- AnkiWeb link with rating/review encouragement (if `ankiweb_id` exists)
- Screenshots
- Full changelog

### 11. AnkiWeb Integration

**Workflow (manual but streamlined):**

1. `al-tools release --finalize` generates `build/ankiweb_description_{deck_id}.md`
2. Open AnkiWeb shared deck page
3. Paste generated description
4. Upload new `.apkg` file

**AnkiWeb ID tracking:** Store in `decks.yaml`. For new decks, leave blank (`null`) until first upload, then add the ID.

**AnkiWeb description includes:**
- Deck description from `description.md`
- Rating/review encouragement
- Link to website for full docs
- Screenshots (as raw GitHub `main` branch URLs)
- Latest changelog entry with version and date

**Decks currently on AnkiWeb:**

| Deck | AnkiWeb ID |
|------|-----------|
| `de_to_es_625` | 1751530227 |
| `de_to_fr_625` | 453325701 |
| `en_to_de_625` | 531645128 |
| `en_to_de_minimal_pairs` | 276400423 |
| `en_to_es_625` | 673955494 |
| `en_to_fr_625` | 866693291 |
| `en_to_it_625` | 1652158130 |
| `en_to_pt_625` | 17319344 |
| `es_to_en_625` | 312293880 |

### 12. Configuration

**`pyproject.toml` additions:**

```toml
[tool.al-tools.release]
interactive = true
auto_push = false

pre_release_hooks = [
    "uv run pytest",
    "uv run ruff check .",
    "uv run al-tools check -i src/data/",
]

[tool.al-tools.content]
# GitHub org/repo for raw URLs
github_repo = "ankilangs/ankilangs"
github_branch = "main"

# Website base URL
website_url = "https://ankilangs.org"
```

## Implementation Phases

### Phase 1: Content Infrastructure -- DONE

1. ~~Create `src/deck_content/` directory structure~~
2. ~~Create initial `description.md` for each existing deck~~
3. ~~Create `changelog.md` for each deck~~
4. ~~Move/create screenshots into per-deck directories~~ (directory structure exists; most decks still need actual screenshots)
5. ~~Create shared website pages (`installation.md`, `learning_tips.md`)~~

### Phase 2: Deck Registry -- DONE

1. ~~Create `decks.yaml` schema and parser (`DeckRegistry` + `Deck` dataclass)~~
2. ~~Migrate all 24 decks to `decks.yaml`~~
3. ~~Add AnkiWeb IDs for existing decks~~
4. ~~Add `al-tools release --list` command~~

### Phase 3: Website Pages -- DONE

Skipped the manual-first approach; went directly to generated pages.

1. ~~Define Hugo template for deck pages~~
2. ~~Generate deck pages from content files~~
3. ~~Setup screenshot directories~~
4. ~~Deck overview page grouped by source language~~
5. ~~i18n: localized section headers and UI strings per source language~~

### Phase 4: Content Generation Tooling -- DONE

1. ~~Implement `ChangelogParser` (extract version blocks)~~
2. ~~Implement `al-tools generate-website` (single deck or all)~~
3. ~~Implement `al-tools generate-ankiweb` (with clipboard support)~~
4. ~~Implement `ContentGenerator.generate_github_release_notes()`~~

**Remaining improvements:**
- Website deck pages should show AnkiWeb link with rating/review encouragement when `ankiweb_id` exists
- AnkiWeb description should include rating/review encouragement
- GitHub release notes should link to AnkiWeb when available

### Phase 5: Core Release Flow -- TODO

1. Implement version parsing and validation
2. Add `al-tools release <deck> --dry-run`
3. Add changelog validation (entry must exist)
4. Implement description file version update
5. Implement version bump in `decks.yaml` and description file

### Phase 6: VCS & GitHub Integration -- TODO

1. Add jj status checks
2. Implement commit creation with `jj commit`
3. Implement tag creation with `git tag`
4. Add `gh` CLI wrapper for GitHub releases
5. Implement `--finalize` to create GitHub release and generate AnkiWeb description

### Phase 7: Polish -- TODO

1. Add `--interactive` mode with prompts
2. Add `--batch` mode for multiple decks
3. Documentation and tests
4. Clipboard copy for AnkiWeb description (already done for `generate-ankiweb`)

## Corner Cases

| Scenario | Handling |
|----------|----------|
| Uncommitted changes | Error, require clean state |
| Tag already exists | Error, suggest checking version |
| Non-main branch | Warning, allow with confirmation |
| Missing changelog entry | Error, must add entry before release |
| Missing screenshots | Warning, proceed but note in output |
| Missing AnkiWeb ID | Warning, remind to upload and add ID |
| First release (no previous tag) | Handle gracefully |
| Network failure during `gh` | Retry logic, manual fallback |
| Screenshot URL before commit | Error: screenshots must be committed to main first |

## Content Update Workflows

### Update changelog only (no release)

```bash
# Edit changelog
vim src/deck_content/en_to_es_625/changelog.md

# Regenerate website page
al-tools generate-website --deck en_to_es_625

# Regenerate AnkiWeb description (if you want to update it)
al-tools generate-ankiweb en_to_es_625
# Then paste to AnkiWeb manually

# Commit
jj commit -m "docs: update en_to_es_625 changelog"
```

### Update description/screenshots (no release)

```bash
# Edit description or add screenshots
vim src/deck_content/en_to_es_625/description.md

# Regenerate
al-tools generate-website --deck en_to_es_625
al-tools generate-ankiweb en_to_es_625

# Commit
jj commit -m "docs: update en_to_es_625 description"

# Push so screenshot URLs work
jj git push

# Update AnkiWeb manually
```

### Full release

```bash
# 1. Update changelog with new version entry
vim src/deck_content/en_to_es_625/changelog.md

# 2. Start release
al-tools release en_to_es_625 --version 1.1.0

# 3. Manual Anki steps (import, export)

# 4. Finalize
al-tools release en_to_es_625 --finalize ~/Downloads/deck.apkg

# 5. Push
jj git push && git push --tags

# 6. Update AnkiWeb (paste description, upload .apkg)
```

## Design Decisions

1. **Website deck pages are committed** - Allows PR review of generated content and works without running generation.

2. **Generation by `al-tools` with Hugo shortcodes** - `al-tools generate-website` produces markdown files that use Hugo shortcodes for internal links (`{{< ref >}}`) and frontmatter params (`{{< param >}}`). Content (description, changelog) is concatenated from source files; Hugo handles linking and theming.

3. **Main page links to deck pages** - No direct download links on main page. Each deck page has the download button. This keeps the main page cleaner and ensures users see full deck info before downloading.

4. **Minimal pairs decks use the same workflow** - Same `decks.yaml` structure, same content architecture. May have different shared content (e.g., different card type explanations) selected via `deck_type` field.

5. **Screenshots hosted on GitHub `main` branch** - Raw GitHub URLs are acceptable. Screenshots must be committed before release.

6. **AnkiWeb rating encouragement** - All generated content (website pages, AnkiWeb descriptions, GitHub release notes) encourages users to rate and review the deck on AnkiWeb when an `ankiweb_id` exists. This helps with discoverability.

7. **Description file sync is part of release flow** - No separate `sync-descriptions` command. The release automation updates `description_*.html` files as part of the version bump step.
