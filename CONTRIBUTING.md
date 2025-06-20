# How to contribute to AnkiLangs
## Error corrections
For example: The "Portuguese 625 words" deck contains a typo → edit `src/data/625_words-base-pt_pt.csv`.

Edit the CSV files under `src/data/`.
CSV files can be imported into Microsoft Excel or LibreOffice Calc in order to edit them.

See below for how to send your changes back to AnkiLangs.

## Contributing audio
For example: A German audio recording for the word "Flugzeug" is incorrect → replace the file `src/media/audio/de_DE/al_de_de_das_flugzeug.ogg`

If you want to add or modify media files (e.g. audio)
you must do so in the `src/media/` directory.

### Licencing
Any audio contributions to AnkiLangs have to be licensed as ???.
Not sure what that means? Have a look at ???

### Physical setup
- Use the best microphone you have available
- Find a noise-free environment

### Recording
- Record a bit of silence at the beginning (for removing background noise)
- Speak slowly, but pronounce words naturally.
- Leave breaks between words and sentences for (so the audio can be cut automatically etc.)

### Mastering
- Try to reserve the quality of the microphone output signal
- If possible, aim for:
	- 44100 Hz sample rate
	- 16 bit bit depth
	- Audio saved as FLAC, WAV, OGG Vorbis, MP3 (in that order of preference)

For audio recordings we can use a file sharing service.
Please get in touch info@ankilangs.org.

## Code changes
If there are any large structural changes you want to make
or anything else that involves a lot of work on your side,
please open a [new issue](https://github.com/ankilangs/ankilangs/issues/new/choose) first in order to discuss it!
Otherwise you risk investing much work only to get it rejected,
which is very frustrating.

### Send a pull request
In order for you modification to become part of the project you must send a PR (pull request) as documented
[here](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).

If you have no experience whatsoever with Git, GitHub, pull requests etc.
then you can send your edits to the CSV files via e-mail.
