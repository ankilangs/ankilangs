# ADR-002: ASCII Audio Filenames with Locale Prefix

## Status
Decided (2026-01-20)

## Context

Audio files are stored in locale-specific directories during development (`src/media/audio/{locale}/`), but Anki merges all media files into a single flat directory (`collection.media/`) during deck import. This creates two requirements:

1. **Collision avoidance**: Filenames must be unique across all locales
2. **Cross-platform compatibility**: Files must sync reliably across Linux, macOS, Windows, iOS (AnkiMobile), and Android (AnkiDroid)

The problem surfaced when adding Farsi (fa_ir) audio generation, where Persian script filenames (e.g., `al_fa_ir_سلام..mp3`) would be natural but raised concerns about filesystem and Anki compatibility.

## Decision

Use ASCII-only filenames with the pattern: `al_{locale}_{key}.mp3`

Examples:
- `al_en_us_the_bank.mp3`
- `al_es_es_the_bank.mp3`
- `al_fa_ir_the_bank.mp3`

The `{key}` portion comes from the database `vocabulary.key` column (English phrases). Spaces and special characters are replaced for easier handling.

## Alternatives Considered

### 1. UTF-8 filenames (native script)
**Structure**: `al_fa_ir_سلام..mp3`

**Pros**:
- Human-readable for native speakers
- Preserves original script

**Cons**:
- **Anki media sync has historically had issues with non-ASCII filenames**
- Windows MAX_PATH limits hit faster with multi-byte encodings
- Cloud sync services may normalize Unicode differently (NFD vs NFC)
- Command-line tool compatibility varies
- Would require extensive testing across all platforms (Anki Desktop, AnkiWeb, AnkiMobile, AnkiDroid)
- Risk of silent data corruption or sync failures

**Verdict**: Too risky given the cross-platform requirements and Anki's media syncing complexity.

### 2. Transliteration (romanization)
**Structure**: `al_fa_ir_salam.mp3` (for "سلام")

**Pros**:
- ASCII-safe
- Phonetically represents the word
- Readable to those familiar with romanization

**Cons**:
- Requires choosing a transliteration standard (Fingilish, ISO 233, BGN/PCGN)
- Libraries like `unidecode` can be lossy or inaccurate
- Different languages have different romanization conventions
- Not readable to those unfamiliar with the system
- Adds complexity to filename generation
- Potential collisions (different words may romanize identically)

**Verdict**: Adds complexity without clear benefit over using database keys.

### 3. Random identifiers
**Structure**: `al_fa_ir_a8d9f2e1.mp3`

**Pros**:
- No collision risk
- No encoding issues

**Cons**:
- Completely opaque - impossible to identify content without database lookup
- Difficult to manually organize, edit, or debug
- Poor developer experience

**Verdict**: Sacrifices too much usability.

## Consequences

Database keys are already English phrases serving as universal identifiers across all locales. Using them in filenames is natural and consistent with the data model.

**Trade-offs**:
- ✅ Human-readable and debuggable (e.g., `al_de_de_the_house.mp3`)
- ✅ Cross-platform safe with no Anki sync risks
- ✅ Direct mapping to `vocabulary.key`
- ❌ Filenames in English, not native script (Persian script preserved in `base_language.text`)
