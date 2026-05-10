# Learning Hints

Learning hints are short, disambiguating cues that help learners when words have multiple meanings. They don't reveal the translation—they just clarify which meaning is being tested.

## The Four Hint Types

AnkiLangs uses four card types, each with its own hint column:

1. **Pronunciation hint** - You see the source word and speak the target word
2. **Reading hint** - You see the target word and recall the source meaning
3. **Spelling hint** - You see the source word, hear the target word, and spell it
4. **Listening hint** - You hear the target word and recall the source meaning

## Why Hints Are Needed

Hints are only needed when a word has multiple distinct meanings that could confuse learners. Most words don't need hints because they're unambiguous (like "cat" → "gato" or "dog" → "perro").

### Key Insight

- **Pronunciation hints** address **source language** ambiguity (which target word to produce)
- **Reading/Listening hints** address **target language** ambiguity (which source meaning to recall)
- **Spelling hints** are rarely needed—see examples below

A single vocabulary entry may need different hints for different card types!

## Examples

### Pronunciation Hint: EN → ES "light"

English "light" has multiple meanings that translate to different Spanish words:
- "light" (brightness) → "claro"
- "light" (weight) → "ligero"

The **source** word is ambiguous, so a **pronunciation hint** is needed.

```
The learner speaks English and is learning Spanish.
Now they should say out loud this word in Spanish.

┌─────────────────────────────────────┐
│ PRONUNCIATION CARD - Question       │
├─────────────────────────────────────┤
│ light                               │
│ Hint: brightness                    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ PRONUNCIATION CARD - Answer         │
├─────────────────────────────────────┤
│ light                               │
│ Hint: brightness                    │
| ----------------------------------- |
│ claro                               │
│ /ˈklaɾo/                            │
└─────────────────────────────────────┘
✓ Not "ligero" (weight)
```

Without the hint, the user wouldn't know whether to say "claro" or "ligero".

### Reading Hint: EN → ES "el cielo"

Spanish "el cielo" has multiple meanings in English:
- "el cielo" → "heaven" (religious place)
- "el cielo" → "the sky" (nature)

The **target** word is ambiguous, so a **reading hint** is needed.

```
The learner speaks English and is learning Spanish.
Now they should recall what this Spanish word means.

┌─────────────────────────────────────┐
│ READING CARD - Question             │
├─────────────────────────────────────┤
│ el cielo                            │
│ Hint: religious place               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ READING CARD - Answer               │
├─────────────────────────────────────┤
│ el cielo                            │
│ Hint: religious place               │
| ----------------------------------- |
│ heaven                              │
└─────────────────────────────────────┘
✓ Not "the sky" (nature)
```

Without the hint, the user wouldn't know whether to answer "heaven" or "sky".

### Listening Hint: EN → DE "groß"

German "groß" has multiple meanings in English:
- "groß" → "big/large" (general size)
- "groß" → "tall" (height)

The **target** word is ambiguous when heard, so a **listening hint** is needed.

```
The learner speaks English and is learning German.
Now they should recall what this German word means.

┌─────────────────────────────────────┐
│ LISTENING CARD - Question           │
├─────────────────────────────────────┤
│ 🔊 [audio plays "groß"]             │
│ Hint: general size                  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ LISTENING CARD - Answer             │
├─────────────────────────────────────┤
│ 🔊 groß                             │
│ Hint: general size                  │
| ----------------------------------- |
│ big / large                         │
└─────────────────────────────────────┘
✓ Not "tall" (height)
```

Listening hints serve the same purpose as reading hints but for audio cards.

Note that listening hints may be required even when reading hints are not, namely for homophones i.e. words that sound the same but are spelled differently. For examples the German word Wal (English: whale) sounds the same as Wahl (English: election).

### Spelling Hint

Spelling hints would theoretically be needed when:
1. Target language has homophones (same pronunciation, different spellings)
2. AND seeing the source word doesn't disambiguate which spelling

In practice, this situation almost never occurs. The user sees the source meaning AND hears the target pronunciation—this combination removes nearly all ambiguity. No real-world examples have been found, but the field exists in case an edge case arises.

### Combined Example: EN → DE "sie"

German "sie" means both "she" (singular) and "they" (plural). These are spelled and pronounced identically.

| Card Type | Hint Needed? | Why |
|-----------|--------------|-----|
| Pronunciation | No | EN "she" and "they" are different words—no source ambiguity |
| Reading | Yes | DE "sie" could mean either—needs hint "feminine, singular" or "plural" |
| Listening | Yes | Same reason as reading |
| Spelling | No | User sees EN "she" → knows it's singular "sie", not ambiguous |

### Combined Example: EN → ES "old"

English "old" maps to different Spanish words:
- "old" (not new) → "viejo"
- "old" (age of person) → "mayor"

| Card Type | Hint Needed? | Why |
|-----------|--------------|-----|
| Pronunciation | Yes | EN "old" is ambiguous—hint "not recently made" vs "age of person" |
| Reading | No | ES "viejo" and "mayor" are different words—no target ambiguity |
| Listening | No | Same reason as reading |
| Spelling | No | Pronunciation hint already clarifies; hearing "viejo" vs "mayor" removes any remaining doubt |

## When NOT to Use Hints

### Unambiguous Words
```
❌ DON'T add hints to:
- cat → gato
- dog → perro
- house → casa
- water → agua
```

These words have clear, single meanings in both languages.

### Common Mistakes to Avoid

**DON'T reveal the translation:**
```
❌ Hint: banco (reveals the Spanish word!)
✓ Hint: for money (disambiguates without revealing)
```

**DON'T be too vague:**
```
❌ Hint: one meaning of bank (useless!)
✓ Hint: financial institution (clear and specific)
```

**DON'T give away the meaning:**
```
❌ Hint: where you put your savings (too revealing!)
✓ Hint: for money (subtle but effective)
```

## Editing Hints

### For Non-Technical Contributors

If you're reviewing a deck using the Excel spreadsheet (from the [systematic deck review](../CONTRIBUTING.md#systematic-deck-review)), you'll find hint columns:
- Column F: `pronunciation_hint`
- Column G: `spelling_hint`
- Column H: `reading_hint`
- Column I: `listening_hint`

Simply type your hint in the appropriate column. Keep them short but clear.

### For Technical Contributors

Hints are stored in the database in the `translation_pair` table with the same column names as above. You can:

1. Import CSV to SQLite: `just csv2sqlite`
2. Edit via SQL:
   ```sql
   UPDATE translation_pair
   SET pronunciation_hint = 'financial institution'
   WHERE key = 'the bank'
     AND source_locale = 'en_us'
     AND target_locale = 'es_es';
   ```
3. Export back to CSV: `just sqlite2csv`

Alternatively, edit the CSV files in `src/data/` directly (though the SQLite workflow is recommended for complex edits).

## Finding Words That Need Hints

The `just check-data` command detects potentially ambiguous words missing hints. For example:

```
Checking for ambiguous translations...
Checking en_us → de_de...
  ⚠️  2 ambiguous words found missing hints
    - "light": 2 entries, no pronunciation hints
    - "race": 2 entries, no pronunciation hints
```

This helps identify words where hints should be added.

## Summary

| Hint Type | Card Shows | User Produces | Addresses | Example |
|-----------|------------|---------------|-----------|---------|
| Pronunciation | Source word | Target speech | Source ambiguity | EN "light" → hint clarifies brightness vs weight |
| Reading | Target word | Source meaning | Target ambiguity | ES "el cielo" → hint clarifies heaven vs sky |
| Listening | Target audio | Source meaning | Target ambiguity | DE "groß" → hint clarifies big vs tall |
| Spelling | Source word + target audio | Target spelling | Theoretically: target homophones | No known examples; kept for edge cases |

The goal: **disambiguate without revealing**. Hints should be just enough to point learners to the right meaning without giving away the answer.
