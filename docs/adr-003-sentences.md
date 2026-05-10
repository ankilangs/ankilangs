# ADR-003: Sentences for Vocabulary Reinforcement

## Status
Draft

## Context

The project currently teaches ~629 individual vocabulary words. Learners benefit from seeing words in context — simple sentences reinforce recognition, demonstrate usage, and provide spaced repetition of known words.

Key challenge: a sentence's word composition is **language-dependent**. Consider the sentence keyed as `I am cold`:

| Locale | Text | Vocabulary keys used |
|---|---|---|
| en_us | "I am cold" | {I, **to be**, cold} |
| es_es | "tengo frío" | {**to have**, cold} |
| fr_fr | "j'ai froid" | {I, **to have**, cold} |

English uses "to be" (I **am** cold), while Spanish and French use "to have" (I **have** cold). Spanish also omits the pronoun. The same sentence links to `to be` in one language and `to have` in others — entirely different vocabulary keys. This isn't an edge case; it's pervasive across languages (age expressions, weather, emotions, etc.).

The word-sentence mapping must therefore be tracked **per locale**.

## Decision

### New Tables

```sql
-- Sentence identity (analogous to vocabulary)
CREATE TABLE sentence (
    key TEXT PRIMARY KEY,
    clarification TEXT
);

-- Sentence text per locale (analogous to base_language)
CREATE TABLE sentence_language (
    key TEXT NOT NULL,
    locale TEXT NOT NULL,
    text TEXT,
    ipa TEXT,
    audio TEXT,
    audio_source TEXT,
    PRIMARY KEY (key, locale),
    FOREIGN KEY (key) REFERENCES sentence(key)
);

-- Per-locale mapping of which vocabulary words appear in a sentence
CREATE TABLE sentence_word (
    sentence_key TEXT NOT NULL,
    vocabulary_key TEXT NOT NULL,
    locale TEXT NOT NULL,
    PRIMARY KEY (sentence_key, vocabulary_key, locale),
    FOREIGN KEY (sentence_key) REFERENCES sentence(key),
    FOREIGN KEY (vocabulary_key) REFERENCES vocabulary(key)
);

-- Translation pair metadata for sentences (hints, etc.)
CREATE TABLE sentence_translation_pair (
    key TEXT NOT NULL,
    source_locale TEXT NOT NULL,
    target_locale TEXT NOT NULL,
    guid TEXT,
    pronunciation_hint TEXT,
    spelling_hint TEXT,
    reading_hint TEXT,
    listening_hint TEXT,
    notes TEXT,
    PRIMARY KEY (key, source_locale, target_locale),
    FOREIGN KEY (key) REFERENCES sentence(key)
);
```

### CSV File Structure

| File Pattern | Purpose |
|---|---|
| `sentences.csv` | Sentence keys and clarifications |
| `sentences-base-{locale}.csv` | Sentence text/IPA/audio per locale |
| `sentences-words-{locale}.csv` | Word links per locale (sentence_key, vocabulary_key) |
| `sentences-from-{src}-to-{tgt}.csv` | Sentence translation pair metadata |

### Linking Rules

- Links connect **sentence keys** to **vocabulary keys** per locale
- Conjugations, inflections, and other surface forms count — link to the base vocabulary key (e.g., "voy" links to `to go`)
- Function words (articles, prepositions) that aren't in the vocabulary table are simply not linked
- Links are manually curated, not auto-derived — this is intentional since inflected forms can't be reliably mapped automatically

### Reusing Existing Note Types

Sentences use the same Anki note types and card templates as vocabulary words. The same four card types (reading, listening, pronunciation, spelling) apply. The hints system works identically.

## Coverage Queries

```sql
-- Words with no sentence coverage for a locale
SELECT v.key
FROM vocabulary v
LEFT JOIN sentence_word sw ON v.key = sw.vocabulary_key AND sw.locale = 'es_es'
WHERE sw.sentence_key IS NULL;

-- Least-covered words (prioritize when creating new sentences)
SELECT v.key, COUNT(sw.sentence_key) AS appearances
FROM vocabulary v
LEFT JOIN sentence_word sw ON v.key = sw.vocabulary_key AND sw.locale = 'es_es'
GROUP BY v.key
ORDER BY appearances ASC;

-- Sentences covering the most uncovered words
SELECT sw.sentence_key, COUNT(*) AS uncovered_words_hit
FROM sentence_word sw
WHERE sw.locale = 'es_es'
  AND sw.vocabulary_key IN (
    SELECT v.key FROM vocabulary v
    LEFT JOIN sentence_word sw2 ON v.key = sw2.vocabulary_key AND sw2.locale = 'es_es'
    WHERE sw2.sentence_key IS NULL
  )
GROUP BY sw.sentence_key
ORDER BY uncovered_words_hit DESC;

-- Overall coverage stats
SELECT
  (SELECT COUNT(*) FROM vocabulary) AS total_words,
  COUNT(DISTINCT sw.vocabulary_key) AS words_in_sentences,
  COUNT(DISTINCT sw.sentence_key) AS total_sentences
FROM sentence_word sw
WHERE sw.locale = 'es_es';
```

## Sentence Selection Strategy

Use a greedy set-cover approach when adding sentences:

1. Query least-covered words for the target locale pair
2. Craft sentences that maximize coverage of uncovered words
3. Re-check coverage after each addition
4. Aim for every word appearing in at least 1-2 sentences

## Alternatives Considered

### Single word-link table without locale

```sql
sentence_word (sentence_key, vocabulary_key)  -- no locale
```

Simpler, but wrong — different languages use different words for the same sentence. Would force picking one language's decomposition as canonical, losing accuracy for all others.

### Auto-derived links via stemming/lemmatization

Automatically match sentence text to vocabulary entries using NLP. Rejected because inflection-to-lemma mapping is unreliable across languages, and the vocabulary set is small enough that manual curation is practical and more accurate.

## Implementation Plan

1. Add new tables to SQLite schema in `csv2sqlite` / `sqlite2csv`
2. Add CSV import/export for the new file patterns
3. Populate initial sentences and word links
4. Generate Anki cards using existing note types
