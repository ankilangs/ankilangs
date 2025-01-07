# Design decisions

## Language-specific note types

Decision: Yes, use language-specific note types instead of generic types.

Some note types could be made generic, for example the one for learning
vocabulary. Every card contains two pieces of text that are specific to the
source language and to the target language, namely the name of the target
language in the source language (for example when learning English as a Spanish
speaker this would be "Inglés") and the type of card (e.g. Spelling, which
would be "Ortografía" in Spanish).

Both these pieces of text could be added as fields of the notes, allowing to
have one generic "Vocabulary" note type and the templates just using those
fields.

This disadvantage is that it requires that those fields are never modified by
end users. The potential for mistakes is just too big. People might
accidentally edit "Inglés" to something else and then be confused because their
cards make no sense any more.

An additional argument is that with language-specific note types it's easier to
take into account language specifics such as right-to-left writing systems.
This could be solved by having language-specific note types only for the
affected languages, but it highlights the fact that it's probably unavoidable
to have _some_ specific note types.
