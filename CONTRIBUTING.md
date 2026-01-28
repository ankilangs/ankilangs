# How to contribute to AnkiLangs

Thank you for your interest in improving AnkiLangs! This guide is for non-technical contributors who want to help improve translations, audio, and other content.

If you're comfortable with technical tools and want to set up the full development environment, see the [technical documentation](docs/development.md).

## Quick Navigation

- [Error Corrections](#error-corrections) - Fix typos and translation mistakes
- [Contributing Audio](#contributing-audio) - Record or improve audio files
- [Systematic Deck Review](#systematic-deck-review) - Review entire decks comprehensively
- [Learning Hints](#learning-hints) - Add hints for ambiguous words
- [Sending Your Changes](#send-a-pull-request) - How to submit your contributions

Nomenclature:
* **Source language:** The (native) language that the learner already speaks (fluently).
* **Target language:** The new language that the learner wants to learn.
* If you see "EN to FR" or "from EN to FR" then EN (English) is the source language and FR (French) is the target language.

## File Structure (What You Need to Know)

AnkiLangs stores all language data in structured files. Here's what matters for contributors:

```
ankilangs/
├── src/
│   ├── data/           ← CSV files with all vocabulary and translations
│   └── media/
│       └── audio/      ← Audio recordings (MP3 files)
└── docs/               ← Documentation
```

**What about the rest?** The project contains other directories (`build/`, `recipes/`, `al_tools/`, etc.) that handle technical aspects like building Anki decks and processing data. You don't need to understand or modify these. If you're curious about the complete structure, check the [technical documentation](docs/development.md#project-structure).

## Error Corrections

**Example:** The Portuguese 625 words deck contains a typo.

**How to fix it:**

1. Find the CSV file in `src/data/` (e.g., `625_words-base-pt_pt.csv`)
2. Open it in Microsoft Excel, LibreOffice Calc, or any spreadsheet program
3. Make your correction
4. [Send your changes](#send-a-pull-request)

**CSV Structure:** Each CSV file contains columns for the English word, translation, pronunciation (IPA), audio filename, and various [learning hints](#learning-hints).

## Contributing Audio

**Example:** A German audio recording for "Flugzeug" sounds unnatural.

**How to fix it:**

Replace the file `src/media/audio/de_DE/al_de_de_the_plane.mp3` with your improved recording.

### Audio Recording Guidelines

#### Physical Setup
- Use the best microphone available
- Find a quiet, noise-free environment

#### Recording
- Record a bit of silence at the beginning (helps remove background noise)
- Speak slowly but pronounce words naturally
- Leave breaks between words to help with audio editing

#### File Format
If possible, aim for:
- 44100 Hz sample rate
- 16 bit bit depth
- Format preference: FLAC > WAV > OGG Vorbis > MP3

**Note:** For audio recordings, we can use a file sharing service instead of pull requests. Please contact us at [info@ankilangs.org](mailto:info@ankilangs.org).

## Systematic Deck Review

If you want to review an entire deck comprehensively (checking all translations, pronunciations, and audio), we provide two files that make this easier:

### The Two Files

1. **Excel Spreadsheet (.xlsx)** - Contains all vocabulary in a single table with columns for:
   - Source word (English)
   - Target translation (e.g., Spanish)
   - Pronunciation (IPA)
   - Audio filename
   - [Learning hints](#learning-hints) (4 columns)
   - Comment column for your notes

2. **Audio File (.mp3)** - Combined audio playing all words in order:
   - 300ms breaks between words
   - 5-second breaks every 10 words
   - Total duration: ~18 minutes for a 625-word deck
   - Matches the row order in the spreadsheet

### How to Get These Files

**Option 1 (Recommended):** Contact us at [info@ankilangs.org](mailto:info@ankilangs.org) and tell us which deck you want to review (e.g., "EN → FR 625 words"). We'll generate and send you both files.

**Option 2:** If you're comfortable with technical setup, see [technical documentation](docs/development.md#systematic-deck-review) for instructions on generating these files yourself.

### Using the Review Files

1. Open the Excel file in your spreadsheet program
2. Play the audio file in your media player (VLC, Windows Media Player, etc.)
3. Listen to each word while following along in the spreadsheet
4. Make corrections directly in the spreadsheet:
   - Fix translation errors
   - Correct IPA pronunciation guides
   - Add comments about audio quality issues in the `review_comment` column

### Understanding the Spreadsheet Columns

The Excel file contains these columns:

| Column | Purpose | Can Edit? |
|--------|---------|-----------|
| A (hidden) | GUID | ⚠️ **NO** - Don't unhide or modify |
| B | Source language (e.g. English) | No |
| C | Target translation | Yes |
| D | Target IPA pronunciation | Yes |
| E | Pronunciation hint | Yes (see [learning hints](#learning-hints)) |
| F | Spelling hint | Yes (see [learning hints](#learning-hints)) |
| G | Reading hint | Yes (see [learning hints](#learning-hints)) |
| H | Listening hint | Yes (see [learning hints](#learning-hints)) |
| I | Notes (additional nice-to-have info for the learner) | Yes, but seldomly needed |
| J | Your review comments | **Yes** - Add all your comments here |

**Why is GUID hidden?** The GUID (Globally Unique Identifier) is an internal ID that must never be modified. Changing it would break the connection between spreadsheet rows and the original data. It's hidden to prevent accidental edits.

### After Your Review

**Partial reviews welcome!** Even reviewing part of a deck is valuable. We can find someone else to continue.

Send your edited spreadsheet to [info@ankilangs.org](mailto:info@ankilangs.org) or submit it as a pull request (see below).

## Learning Hints

Many words have multiple meanings. For example, English "light" can mean:
- Brightness (opposite of dark)
- Weight (opposite of heavy)

**Learning hints** are short cues that clarify which meaning applies without revealing the translation. For example:
- "light" with hint "brightness" → you know to say "claro" (Spanish) not "ligero"

For a complete explanation with examples, see the [Learning Hints Guide](docs/learning-hints.md).

## Send a Pull Request

To integrate your changes into the project, send a pull request (PR) as documented [here](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).

**Never used Git or GitHub?** No problem! Send your edited files via [email](mailto:info@ankilangs.org) instead.

## Licensing

Any content you contribute must be licensed under a compatible open source license, such as [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.en).

Requirements:
- You must be the original author, OR
- You must clearly state the original source and licensing terms

**Copyrighted content cannot be accepted.**

Not sure what this means? Check out https://choosealicense.com/
