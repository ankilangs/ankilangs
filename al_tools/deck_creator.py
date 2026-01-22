"""Create new 625 word deck from templates."""

import uuid
from pathlib import Path

import yaml

from al_tools.i18n import (
    LANGUAGE_NAMES,
    CARD_TYPES,
    get_language_name,
    get_card_type_name,
    get_ui_string,
)


class DeckCreator:
    """Creates a new 625 word deck from templates."""

    def __init__(
        self, source_locale: str, target_locale: str, version: str = "0.1.0-dev"
    ):
        """Initialize deck creator.

        Args:
            source_locale: Source language locale (e.g., "en_us")
            target_locale: Target language locale (e.g., "es_es")
            version: Initial version (default: "0.1.0-dev")
        """
        self.source_locale = source_locale
        self.target_locale = target_locale
        self.version = version

        # Validate locales
        self._validate_locales()

        # Generate identifiers
        self.source_code = source_locale.split("_")[0]
        self.target_code = target_locale.split("_")[0]
        self.deck_id = f"{self.source_code}_to_{self.target_code}"
        self.csv_deck_id = f"{source_locale}-to-{target_locale}"

        # Get language names
        self.source_lang_name = get_language_name(source_locale, source_locale)
        self.target_lang_name_in_source = get_language_name(
            source_locale, target_locale
        )
        self.target_lang_name_in_target = get_language_name(
            target_locale, target_locale
        )

        # Get UI strings
        self.to_word = get_ui_string(source_locale, "to")
        self.words_word = get_ui_string(source_locale, "words")

        # Get card type names (in source language)
        self.listening = get_card_type_name(source_locale, "listening")
        self.pronunciation = get_card_type_name(source_locale, "pronunciation")
        self.reading = get_card_type_name(source_locale, "reading")
        self.spelling = get_card_type_name(source_locale, "spelling")

        # Generate UUIDs
        self.note_model_uuid = str(uuid.uuid4())
        self.deck_uuid = str(uuid.uuid4())

        # Set up paths
        self.template_dir = Path(__file__).parent / "templates" / "625_deck"
        self.note_model_dir = Path("src/note_models") / f"vocabulary_{self.deck_id}"
        self.deck_content_dir = Path("src/deck_content") / f"{self.deck_id}_625"

    def _validate_locales(self):
        """Validate that both locales exist in i18n data."""
        if self.source_locale not in LANGUAGE_NAMES:
            raise ValueError(
                f"Source locale '{self.source_locale}' not found in i18n data. "
                f"Supported locales: {', '.join(LANGUAGE_NAMES.keys())}"
            )

        if self.target_locale not in LANGUAGE_NAMES:
            raise ValueError(
                f"Target locale '{self.target_locale}' not found in i18n data. "
                f"Supported locales: {', '.join(LANGUAGE_NAMES.keys())}"
            )

        if self.source_locale not in CARD_TYPES:
            raise ValueError(
                f"Source locale '{self.source_locale}' not found in card types data. "
                f"Supported locales: {', '.join(CARD_TYPES.keys())}"
            )

    def _render_template(self, template_path: Path) -> str:
        """Render a template file with variable substitution.

        Args:
            template_path: Path to template file

        Returns:
            Rendered template content
        """
        content = template_path.read_text()

        # Create deck name: always SOURCE to TARGET
        deck_name = f"{self.source_code.upper()} to {self.target_code.upper()} | Basic | AnkiLangs.org"

        replacements = {
            "{DECK_ID}": self.deck_id,
            "{DECK_NAME}": deck_name,
            "{NOTE_MODEL_UUID}": self.note_model_uuid,
            "{DECK_UUID}": self.deck_uuid,
            "{SOURCE_LANG_NAME}": self.source_lang_name,
            "{TARGET_LANG_NAME}": self.target_lang_name_in_target,
            "{TARGET_LANG_NAME_IN_SOURCE}": self.target_lang_name_in_source,
            "{LISTENING}": self.listening,
            "{PRONUNCIATION}": self.pronunciation,
            "{READING}": self.reading,
            "{SPELLING}": self.spelling,
            "{VERSION}": self.version,
        }

        for key, value in replacements.items():
            content = content.replace(key, value)

        return content

    def create_note_model(self):
        """Create note model directory and files."""
        self.note_model_dir.mkdir(parents=True, exist_ok=True)

        # Create all template files
        template_files = [
            "note.yaml",
            "style.css",
            "pronunciation.html",
            "spelling.html",
            "listening.html",
            "reading.html",
        ]

        for filename in template_files:
            template_path = self.template_dir / filename
            output_path = self.note_model_dir / filename
            content = self._render_template(template_path)
            output_path.write_text(content)

        print(f"✓ Created note model in {self.note_model_dir}")

    def create_description_file(self):
        """Create deck description HTML file."""
        description_path = (
            Path("src/headers") / f"description_{self.deck_id}-625_words.html"
        )
        template_path = self.template_dir / "description.html"
        content = self._render_template(template_path)
        description_path.write_text(content)

        print(f"✓ Created description file: {description_path}")

    def create_csv_file(self):
        """Create empty CSV file with proper headers."""
        csv_path = Path("src/data") / f"625_words-from-{self.csv_deck_id}.csv"
        headers = "key,guid,pronunciation hint,spelling hint,reading hint,listening hint,notes\n"
        csv_path.write_text(headers)

        print(f"✓ Created CSV file: {csv_path}")

    def create_deck_content(self):
        """Create deck content directory with description and changelog."""
        self.deck_content_dir.mkdir(parents=True, exist_ok=True)

        # Create screenshots directory
        (self.deck_content_dir / "screenshots").mkdir(exist_ok=True)

        # Create description.md
        desc_template = self.template_dir / "description.md"
        desc_content = self._render_template(desc_template)
        (self.deck_content_dir / "description.md").write_text(desc_content)

        # Create changelog.md
        changelog_template = self.template_dir / "changelog.md"
        changelog_content = self._render_template(changelog_template)
        (self.deck_content_dir / "changelog.md").write_text(changelog_content)

        print(f"✓ Created deck content directory: {self.deck_content_dir}")

    def update_recipe_file(self):
        """Update the recipes/source_to_anki_625_words.yaml file."""
        recipe_path = Path("recipes/source_to_anki_625_words.yaml")

        with recipe_path.open("r") as f:
            recipe = yaml.safe_load(f)

        # Add to generate_guids_in_csv
        csv_file = f"src/data/625_words-from-{self.csv_deck_id}.csv"
        if csv_file not in recipe[0]["generate_guids_in_csv"]["source"]:
            recipe[0]["generate_guids_in_csv"]["source"].append(csv_file)

        # Find the build_parts section
        build_parts = recipe[1]["build_parts"]

        # Add note_model_from_yaml_part
        note_model_part = {
            "note_model_from_yaml_part": {
                "part_id": f"vocabulary_{self.deck_id}",
                "file": f"src/note_models/vocabulary_{self.deck_id}/note.yaml",
            }
        }

        # Check if already exists
        part_ids = [
            list(part.values())[0].get("part_id")
            for part in build_parts
            if "note_model_from_yaml_part" in part
        ]
        if f"vocabulary_{self.deck_id}" not in part_ids:
            # Insert after the last note_model_from_yaml_part
            last_note_model_idx = max(
                i
                for i, part in enumerate(build_parts)
                if "note_model_from_yaml_part" in part
            )
            build_parts.insert(last_note_model_idx + 1, note_model_part)

        # Add headers_from_yaml_part
        # Find the headers_from_yaml_part section
        headers_part_idx = next(
            i for i, part in enumerate(build_parts) if "headers_from_yaml_part" in part
        )

        header_entry = {
            "part_id": f"header_{self.deck_id}",
            "file": "src/headers/default.yaml",
            "override": {
                "name": f"{self.target_lang_name_in_source} ({self.source_code.upper()} {self.to_word} {self.target_code.upper()}) | 625 {self.words_word.capitalize()} | AnkiLangs.org",
                "crowdanki_uuid": self.deck_uuid,
                "deck_description_html_file": f"src/headers/description_{self.deck_id}-625_words.html",
            },
        }

        # Check if already exists
        existing_headers = build_parts[headers_part_idx]["headers_from_yaml_part"]
        header_ids = [h["part_id"] for h in existing_headers]
        if f"header_{self.deck_id}" not in header_ids:
            existing_headers.append(header_entry)

        # Add notes_from_csvs
        notes_part = {
            "notes_from_csvs": {
                "part_id": f"notes_{self.deck_id}",
                "note_model_mappings": [
                    {
                        "note_models": [f"vocabulary_{self.deck_id}"],
                        "columns_to_fields": {
                            "guid": "guid",
                            f"text:{self.source_locale.split('_')[0]}": "Source Text",
                            f"text:{self.target_locale.split('_')[0]}": "Target Text",
                            f"ipa:{self.target_locale.split('_')[0]}": "Target IPA",
                            f"audio:{self.target_locale.split('_')[0]}": "Target Audio",
                            "picture": "Picture",
                            "notes": "Notes",
                            "pronunciation hint": "Pronunciation Hint",
                            "spelling hint": "Spelling Hint",
                            "reading hint": "Reading Hint",
                            "listening hint": "Listening Hint",
                            "source": "Source & License",
                            f"tags:{self.target_locale.split('_')[0]}": "tags",
                        },
                    }
                ],
                "file_mappings": [
                    {
                        "file": f"src/data/625_words-from-{self.csv_deck_id}.csv",
                        "note_model": f"vocabulary_{self.deck_id}",
                        "derivatives": [
                            {
                                "file": f"src/data/625_words-base-{self.source_locale}.csv"
                            },
                            {
                                "file": f"src/data/625_words-base-{self.target_locale}.csv"
                            },
                            {"file": "src/data/625_words-pictures.csv"},
                            {
                                "file": f"src/data/generated/625_words-from-{self.csv_deck_id}.csv"
                            },
                        ],
                    }
                ],
            }
        }

        # Check if already exists
        notes_part_ids = [
            list(part.values())[0].get("part_id")
            for part in build_parts
            if "notes_from_csvs" in part
        ]
        if f"notes_{self.deck_id}" not in notes_part_ids:
            # Insert after the last notes_from_csvs
            last_notes_idx = max(
                i for i, part in enumerate(build_parts) if "notes_from_csvs" in part
            )
            build_parts.insert(last_notes_idx + 1, notes_part)

        # Add generate_crowd_anki
        crowd_anki_part = {
            "generate_crowd_anki": {
                "folder": f"build/{self.source_code.upper()}_to_{self.target_code.upper()}_625_Words",
                "notes": {"part_id": f"notes_{self.deck_id}"},
                "note_models": {"parts": [{"part_id": f"vocabulary_{self.deck_id}"}]},
                "headers": f"header_{self.deck_id}",
                "media": {"parts": ["all_media"]},
            }
        }

        # Check if already exists
        crowd_anki_folders = [
            part["generate_crowd_anki"]["folder"]
            for part in recipe
            if "generate_crowd_anki" in part
        ]
        if crowd_anki_part["generate_crowd_anki"]["folder"] not in crowd_anki_folders:
            # Find the last generate_crowd_anki and insert after
            last_crowd_anki_idx = max(
                i for i, part in enumerate(recipe) if "generate_crowd_anki" in part
            )
            recipe.insert(last_crowd_anki_idx + 1, crowd_anki_part)

        # Write back to file
        with recipe_path.open("w") as f:
            yaml.dump(
                recipe, f, default_flow_style=False, sort_keys=False, allow_unicode=True
            )

        print(f"✓ Updated recipe file: {recipe_path}")

    def update_decks_registry(self):
        """Update the decks.yaml registry file."""
        decks_path = Path("decks.yaml")

        with decks_path.open("r") as f:
            registry = yaml.safe_load(f)

        # Create deck entry
        deck_entry = {
            f"{self.deck_id}_625": {
                "name": f"{self.target_lang_name_in_source} ({self.source_code.upper()} {self.to_word} {self.target_code.upper()}) | 625 {self.words_word.capitalize()} | AnkiLangs.org",
                "tag_name": f"{self.source_code.upper()}_to_{self.target_code.upper()}_625_Words",
                "description_file": f"src/headers/description_{self.deck_id}-625_words.html",
                "content_dir": f"src/deck_content/{self.deck_id}_625",
                "version": self.version,
                "ankiweb_id": None,
                "deck_type": "625",
                "source_locale": self.source_locale,
                "target_locale": self.target_locale,
            }
        }

        # Add to registry if not exists
        if f"{self.deck_id}_625" not in registry["decks"]:
            registry["decks"].update(deck_entry)

            # Write back to file
            with decks_path.open("w") as f:
                yaml.dump(
                    registry,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )

            print(f"✓ Updated decks registry: {decks_path}")
        else:
            print(f"⚠ Deck '{self.deck_id}_625' already exists in decks registry")

    def create_deck(self):
        """Create all files for a new 625 word deck."""
        print(
            f"\nCreating deck: {self.source_code.upper()} → {self.target_code.upper()}"
        )
        print(f"Source locale: {self.source_locale}")
        print(f"Target locale: {self.target_locale}")
        print(f"Deck ID: {self.deck_id}")
        print()

        self.create_note_model()
        self.create_description_file()
        self.create_csv_file()
        self.create_deck_content()
        self.update_recipe_file()
        self.update_decks_registry()

        print("\n✓ Deck creation complete!")
        print("\nNext steps:")
        print(
            f"1. Add vocabulary data to: src/data/625_words-from-{self.csv_deck_id}.csv"
        )
        print("2. Import CSV to SQLite: just csv2sqlite")
        print("3. Generate derived files: just generate")
        print("4. Build the deck: just build-625")


def create_625_deck(source_locale: str, target_locale: str, version: str = "0.1.0-dev"):
    """Create a new 625 word deck.

    Args:
        source_locale: Source language locale (e.g., "en_us")
        target_locale: Target language locale (e.g., "es_es")
        version: Initial version (default: "0.1.0-dev")
    """
    creator = DeckCreator(source_locale, target_locale, version)
    creator.create_deck()
