import argparse
from pathlib import Path

from al_tools.core import (
    generate_audio,
    AudioExistsAction,
    generate_joined_source_fields,
    ambiguity_detection,
    csv2sqlite,
    sqlite2csv,
    export_review,
)
from al_tools.registry import DeckRegistry
from al_tools.content import ContentGenerator
from al_tools.deck_creator import create_625_deck


def _locale_to_directory(locale: str) -> str:
    """Convert database locale (e.g., 'en_us') to directory format (e.g., 'en_US')."""
    lang, country = locale.split("_")
    return f"{lang}_{country.upper()}"


def cli():
    """Command line interface for the al_tools package."""
    parser = argparse.ArgumentParser()
    parser.set_defaults(command=None)

    subparsers = parser.add_subparsers(dest="command")

    audio_parser = subparsers.add_parser(
        "audio",
        description="Generate audio files via Google Cloud Text-to-Speech API. Reads vocabulary from the SQLite database and creates MP3 audio files for the specified locale. Updates the database with audio file references and source information.",
    )
    audio_parser.add_argument(
        "-l",
        "--locale",
        type=str,
        required=True,
        help="Locale (e.g., en_us, ES_ES - case insensitive)",
    )
    audio_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output audio folder (default: src/media/audio/{LOCALE})",
    )
    audio_parser.add_argument(
        "-d", "--database", type=str, default="data.db", help="Database file path"
    )
    audio_parser.add_argument(
        "--data-dir", type=str, default="src/data", help="Data folder with CSV files"
    )
    audio_parser.add_argument(
        "-a",
        "--action",
        type=str,
        default="skip",
        choices=["skip", "overwrite", "raise"],
    )
    audio_parser.add_argument(
        "--seed",
        type=str,
        default="42",
        help="Random seed for voice selection: integer for reproducibility (default: 42), or 'random' for non-deterministic",
    )
    audio_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of audio files to generate (to limit API costs)",
    )

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate files in 'generated' folder from SQLite",
        description="Generate derived CSV files with joined source and license information from the SQLite database. These files are used by Brainbrew during the deck build process. Also ensures all vocabulary keys exist in all base language files and translation pair files.",
    )
    generate_parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output folder for generated files",
    )
    generate_parser.add_argument(
        "-d", "--database", type=str, default="data.db", help="Database file path"
    )
    generate_parser.add_argument(
        "--data-dir", type=str, default="src/data", help="Data folder with CSV files"
    )

    check_parser = subparsers.add_parser(
        "check",
        help="Check for data quality issues in SQLite",
        description="Detect ambiguous words missing hints, duplicate keys in CSV files, and audio file mismatches between the database and disk. Ambiguous words are those that appear multiple times with different meanings but lack disambiguation hints (pronunciation, reading, listening, or spelling hints).",
    )
    check_parser.add_argument(
        "-d", "--database", type=str, default="data.db", help="Database file path"
    )
    check_parser.add_argument(
        "--data-dir", type=str, default="src/data", help="Data folder with CSV files"
    )
    check_parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically fix audio issues: remove DB references for missing files and delete unreferenced files from disk",
    )

    csv2sqlite_parser = subparsers.add_parser(
        "csv2sqlite",
        help="Import CSV files to SQLite",
        description="Import all CSV files from the data directory into a SQLite database. This creates a normalized schema with vocabulary, base_language, translation_pair, pictures, minimal_pairs, and tts_overrides tables. The database serves as a working cache for easier querying and editing. Warns before overwriting existing databases.",
    )
    csv2sqlite_parser.add_argument(
        "-i", "--input", type=str, required=True, help="Data folder"
    )
    csv2sqlite_parser.add_argument(
        "-d", "--database", type=str, default="data.db", help="Database file path"
    )
    csv2sqlite_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing database without confirmation",
    )

    sqlite2csv_parser = subparsers.add_parser(
        "sqlite2csv",
        help="Export SQLite to CSV files",
        description="Export the SQLite database back to CSV files with deterministic formatting. All rows are sorted case-insensitively by key, using consistent formatting (Unix line endings, minimal quoting). This ensures clean Git diffs and makes the CSV files ready to commit.",
    )
    sqlite2csv_parser.add_argument(
        "-d", "--database", type=str, required=True, help="Database file path"
    )
    sqlite2csv_parser.add_argument(
        "-o", "--output", type=str, required=True, help="Output data folder"
    )

    export_review_parser = subparsers.add_parser(
        "export-review",
        help="Export review data for native speakers",
        description="Export translation pairs, hints, and audio for native speaker review. Creates a CSV file, an Excel file with formatting and column protection, and a concatenated MP3 audio file with all target language pronunciations. The Excel file has frozen headers, auto-filters, and protects key columns from editing.",
    )
    export_review_parser.add_argument(
        "-s", "--source", type=str, required=True, help="Source locale (e.g., en_us)"
    )
    export_review_parser.add_argument(
        "-t", "--target", type=str, required=True, help="Target locale (e.g., es_es)"
    )
    export_review_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="build/review",
        help="Output directory for review files (default: build/review)",
    )
    export_review_parser.add_argument(
        "-d", "--database", type=str, default="data.db", help="Database file path"
    )
    export_review_parser.add_argument(
        "--media-dir",
        type=str,
        default="src/media/audio",
        help="Audio media directory (default: src/media/audio)",
    )
    export_review_parser.add_argument(
        "--data-dir", type=str, default="src/data", help="Data folder with CSV files"
    )

    release_parser = subparsers.add_parser(
        "release",
        help="Release management commands",
        description="Manage deck releases and versioning. Use --list to show all registered decks with their current versions, latest release versions, and AnkiWeb upload status.",
    )
    release_parser.add_argument(
        "--list", action="store_true", help="List all decks and their status"
    )
    release_parser.add_argument(
        "--registry",
        type=str,
        default="decks.yaml",
        help="Path to deck registry file",
    )

    generate_website_parser = subparsers.add_parser(
        "generate-website",
        help="Generate website pages from source content",
        description="Generate Hugo-compatible markdown pages for the AnkiLangs website. Reads deck metadata and content from the registry and creates formatted documentation pages with screenshots. Use --all to generate pages for all decks or --deck to generate a specific deck's page.",
    )
    generate_website_parser.add_argument(
        "--deck", type=str, help="Generate page for specific deck"
    )
    generate_website_parser.add_argument(
        "--all", action="store_true", help="Generate pages for all decks"
    )
    generate_website_parser.add_argument(
        "--registry",
        type=str,
        default="decks.yaml",
        help="Path to deck registry file",
    )
    generate_website_parser.add_argument(
        "--output-dir",
        type=str,
        default="website/content/docs/decks",
        help="Output directory for generated pages",
    )

    generate_ankiweb_parser = subparsers.add_parser(
        "generate-ankiweb",
        help="Generate AnkiWeb description for a deck",
        description="Generate a formatted AnkiWeb description for a specific deck. Creates HTML-formatted text suitable for pasting into AnkiWeb's deck description field. Optionally copies the output to the clipboard using xclip.",
    )
    generate_ankiweb_parser.add_argument(
        "deck_id", type=str, help="Deck ID to generate description for"
    )
    generate_ankiweb_parser.add_argument(
        "--registry",
        type=str,
        default="decks.yaml",
        help="Path to deck registry file",
    )
    generate_ankiweb_parser.add_argument(
        "--output-dir",
        type=str,
        default="build",
        help="Output directory for generated description",
    )
    generate_ankiweb_parser.add_argument(
        "--clipboard",
        action="store_true",
        help="Copy generated description to clipboard",
    )

    create_deck_parser = subparsers.add_parser(
        "create-deck",
        help="Create a new 625 word deck from templates",
        description="Bootstrap a new 625-word language pair deck from templates. Creates the necessary directory structure, note model files, Brainbrew recipes, and deck registry entry. Sets up all the scaffolding needed to start developing a new language pair.",
    )
    create_deck_parser.add_argument(
        "source_locale", type=str, help="Source locale (e.g., en_us, de_de, es_es)"
    )
    create_deck_parser.add_argument(
        "target_locale", type=str, help="Target locale (e.g., en_us, de_de, es_es)"
    )
    create_deck_parser.add_argument(
        "--version",
        type=str,
        default="0.1.0-dev",
        help="Initial version (default: 0.1.0-dev)",
    )

    args = parser.parse_args()

    if args.command == "audio":
        # Normalize locale to lowercase
        locale = args.locale.lower()

        # Deduce output directory if not provided
        if args.output is None:
            locale_dir = _locale_to_directory(locale)
            output = Path("src/media/audio") / locale_dir
        else:
            output = Path(args.output)

        seed = args.seed if args.seed == "random" else int(args.seed)
        generate_audio(
            Path(args.database),
            locale,
            output,
            AudioExistsAction(args.action),
            Path(args.data_dir),
            seed=seed,
            limit=args.limit,
        )
    elif args.command == "generate":
        generate_joined_source_fields(
            Path(args.database), Path(args.output), Path(args.data_dir)
        )
    elif args.command == "check":
        output = ambiguity_detection(
            Path(args.database), Path(args.data_dir), auto_fix=args.auto_fix
        )
        print(output)
    elif args.command == "csv2sqlite":
        csv2sqlite(Path(args.input), Path(args.database), force=args.force)
    elif args.command == "sqlite2csv":
        sqlite2csv(Path(args.database), Path(args.output))
    elif args.command == "export-review":
        export_review(
            Path(args.database),
            args.source,
            args.target,
            Path(args.output),
            Path(args.media_dir),
            Path(args.data_dir),
        )
    elif args.command == "release":
        if args.list:
            registry = DeckRegistry(Path(args.registry))
            print_deck_list(registry)
        else:
            release_parser.print_help()
    elif args.command == "generate-website":
        registry = DeckRegistry(Path(args.registry))
        output_dir = Path(args.output_dir)

        if args.all:
            generate_all_website_pages(registry, output_dir)
        elif args.deck:
            generate_website_page_for_deck(registry, args.deck, output_dir)
        else:
            generate_website_parser.print_help()
    elif args.command == "generate-ankiweb":
        registry = DeckRegistry(Path(args.registry))
        output_dir = Path(args.output_dir)
        generate_ankiweb_description(
            registry, args.deck_id, output_dir, clipboard=args.clipboard
        )
    elif args.command == "create-deck":
        create_625_deck(args.source_locale, args.target_locale, args.version)
    else:
        parser.print_help()


def print_deck_list(registry: DeckRegistry):
    """Print a formatted list of all decks and their status."""
    decks = sorted(registry.all(), key=lambda d: d.deck_id)

    if not decks:
        print("No decks found in registry.")
        return

    # Calculate column widths
    max_id_len = max(len(d.deck_id) for d in decks)
    max_version_len = max(len(d.version) for d in decks)

    # Print header
    print()
    print(
        f"{'DECK':<{max_id_len}}  {'VERSION':<{max_version_len}}  {'LAST RELEASE':<13}  ANKIWEB"
    )
    print("-" * (max_id_len + max_version_len + 13 + 20))

    # Print each deck
    for deck in decks:
        last_release = registry.get_latest_release_version(deck.deck_id)
        last_release_str = last_release if last_release else "-"

        ankiweb_str = f"✓ {deck.ankiweb_id}" if deck.ankiweb_id else "✗ (not uploaded)"

        print(
            f"{deck.deck_id:<{max_id_len}}  {deck.version:<{max_version_len}}  {last_release_str:<13}  {ankiweb_str}"
        )

    print()


def generate_website_page_for_deck(
    registry: DeckRegistry, deck_id: str, output_dir: Path
):
    """Generate website page for a specific deck."""
    deck = registry.get(deck_id)
    if not deck:
        print(f"Error: Deck '{deck_id}' not found in registry")
        return

    generator = ContentGenerator(deck)
    page_content = generator.generate_website_page()

    # Create output directory for deck
    deck_output_dir = output_dir / deck.website_slug
    deck_output_dir.mkdir(parents=True, exist_ok=True)

    # Write page content
    output_file = deck_output_dir / "_index.md"
    output_file.write_text(page_content)

    # Copy screenshots if they exist
    screenshot_src = Path(deck.content_dir) / "screenshots"
    screenshot_dst = deck_output_dir / "screenshots"

    if screenshot_src.exists():
        # Remove existing screenshots directory if it exists
        import shutil

        if screenshot_dst.exists():
            shutil.rmtree(screenshot_dst)

        # Copy all screenshots
        shutil.copytree(screenshot_src, screenshot_dst)

        print(f"✓ Generated {output_file}")
        print(f"✓ Copied screenshots to {screenshot_dst}")
    else:
        print(f"✓ Generated {output_file}")
        print(f"⚠ No screenshots found in {screenshot_src}")


def generate_all_website_pages(registry: DeckRegistry, output_dir: Path):
    """Generate website pages for all decks."""
    decks = sorted(registry.all(), key=lambda d: d.deck_id)

    if not decks:
        print("No decks found in registry.")
        return

    for deck in decks:
        generate_website_page_for_deck(registry, deck.deck_id, output_dir)

    print(f"\n✓ Generated {len(decks)} deck pages")


def generate_ankiweb_description(
    registry: DeckRegistry, deck_id: str, output_dir: Path, clipboard: bool = False
):
    """Generate AnkiWeb description for a deck."""
    deck = registry.get(deck_id)
    if not deck:
        print(f"Error: Deck '{deck_id}' not found in registry")
        return

    generator = ContentGenerator(deck)
    description = generator.generate_ankiweb_description()

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write description
    output_file = output_dir / f"ankiweb_description_{deck_id}.md"
    output_file.write_text(description)

    print(f"✓ Written to: {output_file}")

    # Copy to clipboard if requested
    if clipboard:
        try:
            import subprocess

            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=description.encode(),
                check=True,
            )
            print("✓ Copied to clipboard")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠ Could not copy to clipboard (xclip not available)")
