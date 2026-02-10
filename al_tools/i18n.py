"""Internationalization for AnkiLangs deck content."""

from typing import Dict

# Language names in each source language
LANGUAGE_NAMES: Dict[str, Dict[str, str]] = {
    "de_de": {
        "de_de": "Deutsch",
        "en_us": "Englisch",
        "es_es": "Spanisch",
        "fr_fr": "Franzosisch",  # ASCII-safe (no umlaut)
        "it_it": "Italienisch",
        "la_la": "Latein",
        "pt_pt": "Portugiesisch",
        "sq_al": "Albanisch",
        "fa_ir": "Persisch",
        "hi_in": "Hindi",
        "kn_in": "Kannada",
        "nl_nl": "Niederländisch",
        "ta_in": "Tamil",
        "nb_no": "Norwegisch",
        "mr_in": "Marathi",
        "sv_se": "Schwedisch",
        "ru_ru": "Russisch",
        "ar_xa": "Arabisch",
    },
    "en_us": {
        "de_de": "German",
        "en_us": "English",
        "es_es": "Spanish",
        "fr_fr": "French",
        "it_it": "Italian",
        "la_la": "Latin",
        "pt_pt": "Portuguese",
        "sq_al": "Albanian",
        "fa_ir": "Farsi",
        "hi_in": "Hindi",
        "kn_in": "Kannada",
        "nl_nl": "Dutch",
        "ta_in": "Tamil",
        "nb_no": "Norwegian",
        "mr_in": "Marathi",
        "sv_se": "Swedish",
        "ru_ru": "Russian",
        "ar_xa": "Arabic",
    },
    "es_es": {
        "de_de": "Aleman",  # ASCII-safe (no accent)
        "en_us": "Ingles",  # ASCII-safe (no accent)
        "es_es": "Espanol",  # ASCII-safe (no tilde)
        "fr_fr": "Frances",  # ASCII-safe (no accent)
        "it_it": "Italiano",
        "la_la": "Latin",  # ASCII-safe (no accent)
        "pt_pt": "Portugues",  # ASCII-safe (no accent)
        "sq_al": "Albanes",  # ASCII-safe (no accent)
        "fa_ir": "Persa",
        "hi_in": "Hindi",
        "kn_in": "Kannada",
        "nl_nl": "Holandes",  # ASCII-safe (no accent)
        "ta_in": "Tamil",
        "nb_no": "Noruego",
        "mr_in": "Marathi",
        "sv_se": "Sueco",
        "ru_ru": "Ruso",
        "ar_xa": "Arabe",
    },
    "fr_fr": {
        "de_de": "Allemand",
        "en_us": "Anglais",
        "es_es": "Espagnol",
        "fr_fr": "Français",
        "it_it": "Italien",
        "la_la": "Latin",
        "pt_pt": "Portugais",
        "sq_al": "Albanais",
        "fa_ir": "Persan",
        "hi_in": "Hindi",
        "kn_in": "Kannada",
        "nl_nl": "Neerlandais",  # ASCII-safe
        "ta_in": "Tamoul",
        "nb_no": "Norvegien",  # ASCII-safe
        "mr_in": "Marathi",
        "sv_se": "Suedois",  # ASCII-safe
        "ru_ru": "Russe",
        "ar_xa": "Arabe",
    },
    "it_it": {
        "de_de": "Tedesco",
        "en_us": "Inglese",
        "es_es": "Spagnolo",
        "fr_fr": "Francese",
        "it_it": "Italiano",
        "la_la": "Latino",
        "pt_pt": "Portoghese",
        "sq_al": "Albanese",
        "fa_ir": "Persiano",
        "hi_in": "Hindi",
        "kn_in": "Kannada",
        "nl_nl": "Olandese",
        "ta_in": "Tamil",
        "nb_no": "Norvegese",
        "mr_in": "Marathi",
        "sv_se": "Svedese",
        "ru_ru": "Russo",
        "ar_xa": "Arabo",
    },
    "pt_pt": {
        "de_de": "Alemão",
        "en_us": "Inglês",
        "es_es": "Espanhol",
        "fr_fr": "Francês",
        "it_it": "Italiano",
        "la_la": "Latim",
        "pt_pt": "Português",
        "sq_al": "Albanês",
        "fa_ir": "Persa",
        "hi_in": "Hindi",
        "kn_in": "Kannada",
        "nl_nl": "Holandês",
        "ta_in": "Tâmil",
        "nb_no": "Norueguês",
        "mr_in": "Marata",
        "sv_se": "Sueco",
        "ru_ru": "Russo",
        "ar_xa": "Árabe",
    },
    "hi_in": {
        "de_de": "Jarman",  # German in Hindi (ASCII-safe)
        "en_us": "Angrezi",  # English in Hindi (ASCII-safe)
        "es_es": "Sipanish",  # Spanish in Hindi (ASCII-safe)
        "fr_fr": "Fransisi",  # French in Hindi (ASCII-safe)
        "it_it": "Italian",  # Italian in Hindi
        "la_la": "Latin",  # Latin in Hindi
        "pt_pt": "Portugisi",  # Portuguese in Hindi (ASCII-safe)
        "sq_al": "Albanian",  # Albanian in Hindi
        "fa_ir": "Farsi",  # Farsi in Hindi
        "hi_in": "Hindi",  # Hindi in Hindi
        "kn_in": "Kannada",  # Kannada in Hindi
        "nl_nl": "Dutch",  # Dutch in Hindi
        "ta_in": "Tamil",  # Tamil in Hindi
        "nb_no": "Norwegian",  # Norwegian in Hindi
        "mr_in": "Marathi",  # Marathi in Hindi
        "sv_se": "Swedish",  # Swedish in Hindi
        "ru_ru": "Russian",  # Russian in Hindi
        "ar_xa": "Arabic",  # Arabic in Hindi
    },
    "kn_in": {
        "de_de": "German",  # German in Kannada (ASCII-safe)
        "en_us": "English",  # English in Kannada (ASCII-safe)
        "es_es": "Spanish",  # Spanish in Kannada (ASCII-safe)
        "fr_fr": "French",  # French in Kannada (ASCII-safe)
        "it_it": "Italian",  # Italian in Kannada
        "la_la": "Latin",  # Latin in Kannada
        "pt_pt": "Portuguese",  # Portuguese in Kannada (ASCII-safe)
        "sq_al": "Albanian",  # Albanian in Kannada
        "fa_ir": "Farsi",  # Farsi in Kannada
        "hi_in": "Hindi",  # Hindi in Kannada
        "kn_in": "Kannada",  # Kannada in Kannada (ASCII-safe)
        "nl_nl": "Dutch",  # Dutch in Kannada
        "ta_in": "Tamil",  # Tamil in Kannada
        "nb_no": "Norwegian",  # Norwegian in Kannada
        "mr_in": "Marathi",  # Marathi in Kannada
        "sv_se": "Swedish",  # Swedish in Kannada
        "ru_ru": "Russian",  # Russian in Kannada
        "ar_xa": "Arabic",  # Arabic in Kannada
    },
    "nl_nl": {
        "de_de": "Duits",
        "en_us": "Engels",
        "es_es": "Spaans",
        "fr_fr": "Frans",
        "it_it": "Italiaans",
        "la_la": "Latijn",
        "pt_pt": "Portugees",
        "sq_al": "Albanees",
        "fa_ir": "Perzisch",
        "hi_in": "Hindi",
        "kn_in": "Kannada",
        "nl_nl": "Nederlands",
        "ta_in": "Tamil",
        "nb_no": "Noors",
        "mr_in": "Marathi",
        "sv_se": "Zweeds",
        "ru_ru": "Russisch",
        "ar_xa": "Arabisch",
    },
    "ta_in": {
        "de_de": "German",  # German in Tamil (ASCII-safe)
        "en_us": "English",  # English in Tamil
        "es_es": "Spanish",  # Spanish in Tamil
        "fr_fr": "French",  # French in Tamil
        "it_it": "Italian",  # Italian in Tamil
        "la_la": "Latin",  # Latin in Tamil
        "pt_pt": "Portuguese",  # Portuguese in Tamil
        "sq_al": "Albanian",  # Albanian in Tamil
        "fa_ir": "Farsi",  # Farsi in Tamil
        "hi_in": "Hindi",  # Hindi in Tamil
        "kn_in": "Kannada",  # Kannada in Tamil
        "nl_nl": "Dutch",  # Dutch in Tamil
        "ta_in": "Tamil",  # Tamil in Tamil
        "nb_no": "Norwegian",  # Norwegian in Tamil
        "mr_in": "Marathi",  # Marathi in Tamil
        "sv_se": "Swedish",  # Swedish in Tamil
        "ru_ru": "Russian",  # Russian in Tamil
        "ar_xa": "Arabic",  # Arabic in Tamil
    },
    "nb_no": {
        "de_de": "Tysk",
        "en_us": "Engelsk",
        "es_es": "Spansk",
        "fr_fr": "Fransk",
        "it_it": "Italiensk",
        "la_la": "Latin",
        "pt_pt": "Portugisisk",
        "sq_al": "Albansk",
        "fa_ir": "Persisk",
        "hi_in": "Hindi",
        "kn_in": "Kannada",
        "nl_nl": "Nederlandsk",
        "ta_in": "Tamil",
        "nb_no": "Norsk",
        "mr_in": "Marathi",
        "sv_se": "Svensk",
        "ru_ru": "Russisk",
        "ar_xa": "Arabisk",
    },
    "mr_in": {
        "de_de": "German",  # German in Marathi (ASCII-safe)
        "en_us": "English",  # English in Marathi
        "es_es": "Spanish",  # Spanish in Marathi
        "fr_fr": "French",  # French in Marathi
        "it_it": "Italian",  # Italian in Marathi
        "la_la": "Latin",  # Latin in Marathi
        "pt_pt": "Portuguese",  # Portuguese in Marathi
        "sq_al": "Albanian",  # Albanian in Marathi
        "fa_ir": "Farsi",  # Farsi in Marathi
        "hi_in": "Hindi",  # Hindi in Marathi
        "kn_in": "Kannada",  # Kannada in Marathi
        "nl_nl": "Dutch",  # Dutch in Marathi
        "ta_in": "Tamil",  # Tamil in Marathi
        "nb_no": "Norwegian",  # Norwegian in Marathi
        "mr_in": "Marathi",  # Marathi in Marathi
        "sv_se": "Swedish",  # Swedish in Marathi
        "ru_ru": "Russian",  # Russian in Marathi
        "ar_xa": "Arabic",  # Arabic in Marathi
    },
    "sv_se": {
        "de_de": "Tyska",
        "en_us": "Engelska",
        "es_es": "Spanska",
        "fr_fr": "Franska",
        "it_it": "Italienska",
        "la_la": "Latin",
        "pt_pt": "Portugisiska",
        "sq_al": "Albanska",
        "fa_ir": "Persiska",
        "hi_in": "Hindi",
        "kn_in": "Kannada",
        "nl_nl": "Nederlandska",
        "ta_in": "Tamil",
        "nb_no": "Norska",
        "mr_in": "Marathi",
        "sv_se": "Svenska",
        "ru_ru": "Ryska",
        "ar_xa": "Arabiska",
    },
    "ru_ru": {
        "de_de": "Nemetskiy",  # German in Russian (ASCII-safe)
        "en_us": "Angliyskiy",  # English in Russian (ASCII-safe)
        "es_es": "Ispanskiy",  # Spanish in Russian (ASCII-safe)
        "fr_fr": "Frantsuzskiy",  # French in Russian (ASCII-safe)
        "it_it": "Italyanskiy",  # Italian in Russian (ASCII-safe)
        "la_la": "Latin",  # Latin in Russian
        "pt_pt": "Portugalskiy",  # Portuguese in Russian (ASCII-safe)
        "sq_al": "Albanian",  # Albanian in Russian
        "fa_ir": "Farsi",  # Farsi in Russian
        "hi_in": "Hindi",  # Hindi in Russian
        "kn_in": "Kannada",  # Kannada in Russian
        "nl_nl": "Gollandskiy",  # Dutch in Russian (ASCII-safe)
        "ta_in": "Tamil",  # Tamil in Russian
        "nb_no": "Norvezhskiy",  # Norwegian in Russian (ASCII-safe)
        "mr_in": "Marathi",  # Marathi in Russian
        "sv_se": "Shvedskiy",  # Swedish in Russian (ASCII-safe)
        "ru_ru": "Russkiy",  # Russian in Russian (ASCII-safe)
        "ar_xa": "Arabskiy",  # Arabic in Russian (ASCII-safe)
    },
    "ar_xa": {
        "de_de": "Almaniyya",  # German in Arabic (ASCII-safe)
        "en_us": "Injiliziyya",  # English in Arabic (ASCII-safe)
        "es_es": "Isbaniyya",  # Spanish in Arabic (ASCII-safe)
        "fr_fr": "Faransiyya",  # French in Arabic (ASCII-safe)
        "it_it": "Italiyya",  # Italian in Arabic (ASCII-safe)
        "la_la": "Latiniyya",  # Latin in Arabic (ASCII-safe)
        "pt_pt": "Burtughaliyya",  # Portuguese in Arabic (ASCII-safe)
        "sq_al": "Albaniyya",  # Albanian in Arabic (ASCII-safe)
        "fa_ir": "Farisiyya",  # Farsi in Arabic (ASCII-safe)
        "hi_in": "Hindiyya",  # Hindi in Arabic (ASCII-safe)
        "kn_in": "Kannada",  # Kannada in Arabic
        "nl_nl": "Hulandiyya",  # Dutch in Arabic (ASCII-safe)
        "ta_in": "Tamil",  # Tamil in Arabic
        "nb_no": "Nurwijiyya",  # Norwegian in Arabic (ASCII-safe)
        "mr_in": "Marathi",  # Marathi in Arabic
        "sv_se": "Iswidiyya",  # Swedish in Arabic (ASCII-safe)
        "ru_ru": "Rusiyya",  # Russian in Arabic (ASCII-safe)
        "ar_xa": "Arabiyya",  # Arabic in Arabic (ASCII-safe)
    },
}

# UI strings for each locale
UI_STRINGS: Dict[str, Dict[str, str]] = {
    "de_de": {
        "to": "zu",
        "words": "Worter",  # ASCII-safe version (no umlaut) for filenames
        "minimal_pairs": "Minimalpaar",
        "download_deck": "Stapel herunterladen",
        "installation_instructions": "Installationsanleitung",
        "learning_tips": "Lerntipps",
        "screenshots": "Screenshots",
        "changelog": "Änderungsprotokoll",
        "notes": "Hinweise",
        "see_x_and_y": "Siehe {} und {}.",
        "version": "Version",
        "whats_new_in": "Was ist neu in {}",
        "unreleased_note": "Dieses Deck ist noch nicht veröffentlicht und befindet sich in der Entwicklung.",
        "decks": "Stapel",
        "learn_other_languages_intro": "Lerne andere Sprachen, wenn du Deutsch sprichst",
        "source_language_decks_header": "Deutsche Stapel",
        "ankiweb_also_available": "Auch auf [AnkiWeb]({}) verfügbar. Wenn dir dieser Stapel gefällt, bewerte ihn dort, um anderen Lernenden zu helfen, ihn zu finden!",
        "ankiweb_rate_review": "Wenn du diesen Stapel nützlich findest, bewerte ihn bitte und hinterlasse eine Rezension, um anderen Lernenden zu helfen!",
        "check_deck_page_html": 'Siehe <a href="{}">die Seite dieses Stapels</a> für Updates, Dokumentation und um Probleme zu melden.',
        "check_more_decks_html": 'Mehr Stapel auf <a href="https://ankilangs.org">AnkiLangs.org</a>.',
    },
    "en_us": {
        "to": "to",
        "words": "Words",
        "minimal_pairs": "Minimal Pairs",
        "download_deck": "Download deck",
        "installation_instructions": "Installation Instructions",
        "learning_tips": "Learning Tips",
        "screenshots": "Screenshots",
        "changelog": "Changelog",
        "notes": "Notes",
        "see_x_and_y": "See {} and {}.",
        "version": "Version",
        "whats_new_in": "What's New in {}",
        "unreleased_note": "This deck is not yet released and is under development.",
        "decks": "Decks",
        "learn_other_languages_intro": "Learn other languages if you speak English",
        "source_language_decks_header": "English Decks",
        "ankiweb_also_available": "Also available on [AnkiWeb]({}). If you enjoy this deck, please rate it there to help other learners find it!",
        "ankiweb_rate_review": "If you find this deck useful, please rate it and leave a review to help other learners find it!",
        "check_deck_page_html": 'Check <a href="{}">this deck\'s page</a> for updates, documentation, and to report issues.',
        "check_more_decks_html": 'Check <a href="https://ankilangs.org">AnkiLangs.org</a> for more decks.',
    },
    "es_es": {
        "to": "a",
        "words": "palabras",
        "minimal_pairs": "pares mínimos",
        "download_deck": "Descargar mazo",
        "installation_instructions": "Instrucciones de instalación",
        "learning_tips": "Consejos de aprendizaje",
        "screenshots": "Capturas de pantalla",
        "changelog": "Registro de cambios",
        "notes": "Notas",
        "see_x_and_y": "Ver {} y {}.",
        "version": "Versión",
        "whats_new_in": "Novedades en {}",
        "unreleased_note": "Este mazo aún no está publicado y está en desarrollo.",
        "decks": "Mazos",
        "learn_other_languages_intro": "Aprende otros idiomas si hablas español",
        "source_language_decks_header": "Mazos españoles",
        "ankiweb_also_available": "También disponible en [AnkiWeb]({}). Si te gusta este mazo, califícalo allí para ayudar a otros estudiantes a encontrarlo.",
        "ankiweb_rate_review": "Si este mazo te resulta útil, califícalo y deja una reseña para ayudar a otros estudiantes.",
        "check_deck_page_html": 'Consulta <a href="{}">la página de este mazo</a> para actualizaciones, documentación y para reportar problemas.',
        "check_more_decks_html": 'Más mazos en <a href="https://ankilangs.org">AnkiLangs.org</a>.',
    },
    "fr_fr": {
        "to": "à",
        "words": "mots",
        "minimal_pairs": "paires minimales",
        "download_deck": "Télécharger le paquet",
        "installation_instructions": "Instructions d'installation",
        "learning_tips": "Conseils d'apprentissage",
        "screenshots": "Captures d'écran",
        "changelog": "Journal des modifications",
        "notes": "Notes",
        "see_x_and_y": "Voir {} et {}.",
        "version": "Version",
        "whats_new_in": "Nouveautés de {}",
        "unreleased_note": "Ce paquet n'est pas encore publié et est en cours de développement.",
        "decks": "Paquets",
        "learn_other_languages_intro": "Apprenez d'autres langues si vous parlez français",
        "source_language_decks_header": "Paquets français",
        "ankiweb_also_available": "Également disponible sur [AnkiWeb]({}). Si ce paquet vous plaît, notez-le pour aider d'autres apprenants à le trouver !",
        "ankiweb_rate_review": "Si ce paquet vous est utile, notez-le et laissez un avis pour aider d'autres apprenants !",
        "check_deck_page_html": 'Consultez <a href="{}">la page de ce paquet</a> pour les mises à jour, la documentation et pour signaler des problèmes.',
        "check_more_decks_html": 'Plus de paquets sur <a href="https://ankilangs.org">AnkiLangs.org</a>.',
    },
    "it_it": {
        "to": "a",
        "words": "parole",
        "minimal_pairs": "coppie minime",
        "download_deck": "Scarica mazzo",
        "installation_instructions": "Istruzioni di installazione",
        "learning_tips": "Suggerimenti per l'apprendimento",
        "screenshots": "Screenshot",
        "changelog": "Registro delle modifiche",
        "notes": "Note",
        "see_x_and_y": "Vedi {} e {}.",
        "version": "Versione",
        "whats_new_in": "Novità in {}",
        "unreleased_note": "Questo mazzo non è ancora stato rilasciato ed è in fase di sviluppo.",
        "decks": "Mazzi",
        "learn_other_languages_intro": "Impara altre lingue se parli italiano",
        "source_language_decks_header": "Mazzi italiani",
    },
    "pt_pt": {
        "to": "para",
        "words": "palavras",
        "minimal_pairs": "pares mínimos",
        "download_deck": "Baixar baralho",
        "installation_instructions": "Instruções de instalação",
        "learning_tips": "Dicas de aprendizagem",
        "screenshots": "Capturas de tela",
        "changelog": "Registro de alterações",
        "notes": "Notas",
        "see_x_and_y": "Ver {} e {}.",
        "version": "Versão",
        "whats_new_in": "Novidades em {}",
        "unreleased_note": "Este baralho ainda não foi lançado e está em desenvolvimento.",
        "decks": "Baralhos",
        "learn_other_languages_intro": "Aprenda outras línguas se você fala português",
        "source_language_decks_header": "Baralhos portugueses",
    },
    "hi_in": {
        "to": "se",  # "to" in Hindi
        "words": "shabd",  # "words" in Hindi (ASCII-safe)
        "minimal_pairs": "minimal pairs",  # Keep in English for technical term
        "download_deck": "Deck download karen",  # "download deck" in Hindi (ASCII-safe)
        "installation_instructions": "Installation Instructions",
        "learning_tips": "Sikhne ke sujhav",  # "learning tips" in Hindi (ASCII-safe)
        "screenshots": "Screenshots",
        "changelog": "Parivartan log",  # "changelog" in Hindi (ASCII-safe)
        "notes": "Notes",
        "see_x_and_y": "{} aur {} dekhen.",  # "see X and Y" in Hindi (ASCII-safe)
        "version": "Version",
        "whats_new_in": "{} mein naya kya hai",  # "what's new in" in Hindi (ASCII-safe)
        "unreleased_note": "Yeh deck abhi release nahin hua hai aur vikas mein hai.",  # ASCII-safe
        "decks": "Decks",
        "learn_other_languages_intro": "Agar aap Hindi bolte hain to anya bhashaen seekhen",  # ASCII-safe
        "source_language_decks_header": "Hindi Decks",
    },
    "kn_in": {
        "to": "to",  # Keep in English for simplicity
        "words": "words",  # Keep in English for simplicity
        "minimal_pairs": "minimal pairs",
        "download_deck": "Download deck",
        "installation_instructions": "Installation Instructions",
        "learning_tips": "Learning Tips",
        "screenshots": "Screenshots",
        "changelog": "Changelog",
        "notes": "Notes",
        "see_x_and_y": "See {} and {}.",
        "version": "Version",
        "whats_new_in": "What's New in {}",
        "unreleased_note": "This deck is not yet released and is under development.",
        "decks": "Decks",
        "learn_other_languages_intro": "Learn other languages if you speak Kannada",
        "source_language_decks_header": "Kannada Decks",
    },
    "nl_nl": {
        "to": "naar",
        "words": "woorden",
        "minimal_pairs": "minimale paren",
        "download_deck": "Download deck",
        "installation_instructions": "Installatie-instructies",
        "learning_tips": "Leertips",
        "screenshots": "Screenshots",
        "changelog": "Wijzigingslogboek",
        "notes": "Notities",
        "see_x_and_y": "Zie {} en {}.",
        "version": "Versie",
        "whats_new_in": "Wat is nieuw in {}",
        "unreleased_note": "Dit deck is nog niet uitgebracht en is in ontwikkeling.",
        "decks": "Decks",
        "learn_other_languages_intro": "Leer andere talen als je Nederlands spreekt",
        "source_language_decks_header": "Nederlandse Decks",
    },
    "ta_in": {
        "to": "to",  # Keep in English for simplicity
        "words": "words",  # Keep in English for simplicity
        "minimal_pairs": "minimal pairs",
        "download_deck": "Download deck",
        "installation_instructions": "Installation Instructions",
        "learning_tips": "Learning Tips",
        "screenshots": "Screenshots",
        "changelog": "Changelog",
        "notes": "Notes",
        "see_x_and_y": "See {} and {}.",
        "version": "Version",
        "whats_new_in": "What's New in {}",
        "unreleased_note": "This deck is not yet released and is under development.",
        "decks": "Decks",
        "learn_other_languages_intro": "Learn other languages if you speak Tamil",
        "source_language_decks_header": "Tamil Decks",
    },
    "nb_no": {
        "to": "til",
        "words": "ord",
        "minimal_pairs": "minimale par",
        "download_deck": "Last ned deck",
        "installation_instructions": "Installasjonsinstruksjoner",
        "learning_tips": "Laeringstips",  # ASCII-safe
        "screenshots": "Skjermbilder",
        "changelog": "Endringslogg",
        "notes": "Notater",
        "see_x_and_y": "Se {} og {}.",
        "version": "Versjon",
        "whats_new_in": "Hva er nytt i {}",
        "unreleased_note": "Dette decket er ikke utgitt enda og er under utvikling.",
        "decks": "Deck",
        "learn_other_languages_intro": "Laer andre sprak hvis du snakker norsk",  # ASCII-safe
        "source_language_decks_header": "Norske Deck",
    },
    "mr_in": {
        "to": "to",  # Keep in English for simplicity
        "words": "words",  # Keep in English for simplicity
        "minimal_pairs": "minimal pairs",
        "download_deck": "Download deck",
        "installation_instructions": "Installation Instructions",
        "learning_tips": "Learning Tips",
        "screenshots": "Screenshots",
        "changelog": "Changelog",
        "notes": "Notes",
        "see_x_and_y": "See {} and {}.",
        "version": "Version",
        "whats_new_in": "What's New in {}",
        "unreleased_note": "This deck is not yet released and is under development.",
        "decks": "Decks",
        "learn_other_languages_intro": "Learn other languages if you speak Marathi",
        "source_language_decks_header": "Marathi Decks",
    },
    "sv_se": {
        "to": "till",
        "words": "ord",
        "minimal_pairs": "minimala par",
        "download_deck": "Ladda ner deck",
        "installation_instructions": "Installationsinstruktioner",
        "learning_tips": "Laeringstips",  # ASCII-safe
        "screenshots": "Skaermdumpar",  # ASCII-safe
        "changelog": "Aendringslogg",  # ASCII-safe
        "notes": "Anteckningar",
        "see_x_and_y": "Se {} och {}.",
        "version": "Version",
        "whats_new_in": "Vad ar nytt i {}",  # ASCII-safe
        "unreleased_note": "Detta deck ar aennu inte utgivet och ar under utveckling.",  # ASCII-safe
        "decks": "Deck",
        "learn_other_languages_intro": "Laer dig andra sprak om du talar svenska",  # ASCII-safe
        "source_language_decks_header": "Svenska Deck",
    },
    "ru_ru": {
        "to": "to",  # Keep in English for simplicity
        "words": "words",  # Keep in English for simplicity
        "minimal_pairs": "minimal pairs",
        "download_deck": "Download deck",
        "installation_instructions": "Installation Instructions",
        "learning_tips": "Learning Tips",
        "screenshots": "Screenshots",
        "changelog": "Changelog",
        "notes": "Notes",
        "see_x_and_y": "See {} and {}.",
        "version": "Version",
        "whats_new_in": "What's New in {}",
        "unreleased_note": "This deck is not yet released and is under development.",
        "decks": "Decks",
        "learn_other_languages_intro": "Learn other languages if you speak Russian",
        "source_language_decks_header": "Russian Decks",
    },
    "ar_xa": {
        "to": "ila",  # "to" in Arabic (ASCII-safe)
        "words": "kalimat",  # "words" in Arabic (ASCII-safe)
        "minimal_pairs": "minimal pairs",  # Keep in English for technical term
        "download_deck": "Download deck",
        "installation_instructions": "Installation Instructions",
        "learning_tips": "Learning Tips",
        "screenshots": "Screenshots",
        "changelog": "Changelog",
        "notes": "Notes",
        "see_x_and_y": "See {} and {}.",
        "version": "Version",
        "whats_new_in": "What's New in {}",
        "unreleased_note": "This deck is not yet released and is under development.",
        "decks": "Decks",
        "learn_other_languages_intro": "Learn other languages if you speak Arabic",
        "source_language_decks_header": "Arabic Decks",
    },
}

# Card type names for each locale
CARD_TYPES: Dict[str, Dict[str, str]] = {
    "de_de": {
        "listening": "Hörverständnis",
        "pronunciation": "Aussprache",
        "reading": "Leseverständnis",
        "spelling": "Rechtschreibung",
    },
    "en_us": {
        "listening": "Listening",
        "pronunciation": "Pronunciation",
        "reading": "Reading",
        "spelling": "Spelling",
    },
    "es_es": {
        "listening": "Comprensión oral",
        "pronunciation": "Pronunciación",
        "reading": "Comprensión escrita",
        "spelling": "Ortografía",
    },
    "fr_fr": {
        "listening": "Compréhension orale",
        "pronunciation": "Prononciation",
        "reading": "Compréhension écrite",
        "spelling": "Orthographe",
    },
    "it_it": {
        "listening": "Ascolto",
        "pronunciation": "Pronuncia",
        "reading": "Lettura",
        "spelling": "Ortografia",
    },
    "pt_pt": {
        "listening": "Compreensão oral",
        "pronunciation": "Pronúncia",
        "reading": "Compreensão escrita",
        "spelling": "Ortografia",
    },
    "hi_in": {
        "listening": "Sunna",  # "Listening" in Hindi (ASCII-safe)
        "pronunciation": "Ucharan",  # "Pronunciation" in Hindi (ASCII-safe)
        "reading": "Padhna",  # "Reading" in Hindi (ASCII-safe)
        "spelling": "Spelling",  # "Spelling" in Hindi (keeping English as commonly used)
    },
    "kn_in": {
        "listening": "Listening",  # Keep in English
        "pronunciation": "Pronunciation",  # Keep in English
        "reading": "Reading",  # Keep in English
        "spelling": "Spelling",  # Keep in English
    },
    "nl_nl": {
        "listening": "Luisteren",
        "pronunciation": "Uitspraak",
        "reading": "Lezen",
        "spelling": "Spelling",
    },
    "ta_in": {
        "listening": "Listening",  # Keep in English
        "pronunciation": "Pronunciation",  # Keep in English
        "reading": "Reading",  # Keep in English
        "spelling": "Spelling",  # Keep in English
    },
    "nb_no": {
        "listening": "Lytting",
        "pronunciation": "Uttale",
        "reading": "Lesing",
        "spelling": "Stavemåte",
    },
    "mr_in": {
        "listening": "Listening",  # Keep in English
        "pronunciation": "Pronunciation",  # Keep in English
        "reading": "Reading",  # Keep in English
        "spelling": "Spelling",  # Keep in English
    },
    "sv_se": {
        "listening": "Lyssnande",
        "pronunciation": "Uttal",
        "reading": "Laesning",  # ASCII-safe
        "spelling": "Stavning",
    },
    "ru_ru": {
        "listening": "Listening",  # Keep in English
        "pronunciation": "Pronunciation",  # Keep in English
        "reading": "Reading",  # Keep in English
        "spelling": "Spelling",  # Keep in English
    },
    "ar_xa": {
        "listening": "Listening",  # Keep in English for simplicity
        "pronunciation": "Pronunciation",  # Keep in English
        "reading": "Reading",  # Keep in English
        "spelling": "Spelling",  # Keep in English
    },
}


def get_language_name(locale: str, target_locale: str) -> str:
    """Get the name of target language in the source language.

    Args:
        locale: Source language locale (e.g., "en_us")
        target_locale: Target language locale (e.g., "es_es")

    Returns:
        Language name in source language (e.g., "Spanish" for en_us -> es_es)
    """
    if locale not in LANGUAGE_NAMES:
        # Fallback to English
        locale = "en_us"

    return LANGUAGE_NAMES[locale].get(target_locale, target_locale)


def get_ui_string(locale: str, key: str, *args) -> str:
    """Get a UI string in the specified locale.

    Args:
        locale: Language locale (e.g., "en_us")
        key: UI string key (e.g., "download_deck")
        *args: Format arguments for strings with placeholders

    Returns:
        Localized UI string
    """
    if locale not in UI_STRINGS:
        # Fallback to English
        locale = "en_us"

    string = UI_STRINGS[locale].get(key, key)

    if args:
        return string.format(*args)

    return string


def get_card_type_name(locale: str, card_type: str) -> str:
    """Get the name of a card type in the specified locale.

    Args:
        locale: Language locale (e.g., "en_us")
        card_type: Card type key (e.g., "listening", "pronunciation")

    Returns:
        Localized card type name
    """
    if locale not in CARD_TYPES:
        # Fallback to English
        locale = "en_us"

    return CARD_TYPES[locale].get(card_type, card_type.capitalize())


def get_apkg_filename(
    source_locale: str,
    target_locale: str,
    deck_type: str,
    version: str,
) -> str:
    """Generate the .apkg filename following the project convention.

    Args:
        source_locale: Source language locale (e.g., "en_us")
        target_locale: Target language locale (e.g., "es_es")
        deck_type: Deck type ("625" or "minimal_pairs")
        version: Version string (e.g., "0.2.0")

    Returns:
        Filename (e.g., "Spanish.EN.to.ES.-.625.Words.-.AnkiLangs.org.-.v0.2.0.apkg")
    """
    # Get target language name in source language
    target_lang_name = get_language_name(source_locale, target_locale)

    # Get localized "to"
    to_word = get_ui_string(source_locale, "to")

    # Convert locales to uppercase for filename
    source_upper = source_locale.split("_")[0].upper()
    target_upper = target_locale.split("_")[0].upper()

    # Get deck type suffix
    if deck_type == "625":
        words = get_ui_string(source_locale, "words")
        type_suffix = f"625.{words}"
    elif deck_type == "minimal_pairs":
        minimal_pairs = get_ui_string(source_locale, "minimal_pairs")
        # Capitalize each word
        minimal_pairs_title = ".".join(
            word.capitalize() for word in minimal_pairs.split()
        )
        type_suffix = minimal_pairs_title
    else:
        type_suffix = deck_type

    filename = f"{target_lang_name}.{source_upper}.{to_word}.{target_upper}.-.{type_suffix}.-.AnkiLangs.org.-.v{version}.apkg"

    return filename
