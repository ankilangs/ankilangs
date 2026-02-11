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
    import_review,
)
from al_tools.registry import DeckRegistry
from al_tools.content import ContentGenerator, generate_deck_overview_page
from al_tools.deck_creator import create_625_deck
from al_tools.i18n import get_apkg_filename


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
        help="Generate audio files via Google Cloud TTS API",
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
    audio_parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between TTS requests to avoid rate limiting (default: 1.0, accepts decimals like 0.5 or 1.5)",
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
    csv2sqlite_parser.add_argument(
        "--fail-if-conflict",
        action="store_true",
        help="Exit with error if database has unsaved edits (for scripts/CI)",
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
    sqlite2csv_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite CSV files even if they are newer than the database",
    )
    sqlite2csv_parser.add_argument(
        "--fail-if-conflict",
        action="store_true",
        help="Exit with error if CSV files have changed (for scripts/CI)",
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

    import_review_parser = subparsers.add_parser(
        "import-review",
        help="Import reviewed corrections from native speakers",
        description="Import corrections from a reviewed Excel or CSV file back into the database. Updates target_text, target_ipa, and hints. When target_text changes, deletes the corresponding audio file and clears the audio reference.",
    )
    import_review_parser.add_argument(
        "file", type=str, help="Path to reviewed file (.xlsx or .csv)"
    )
    import_review_parser.add_argument(
        "-s", "--source", type=str, required=True, help="Source locale (e.g., en_us)"
    )
    import_review_parser.add_argument(
        "-t", "--target", type=str, required=True, help="Target locale (e.g., es_es)"
    )
    import_review_parser.add_argument(
        "-d", "--database", type=str, default="data.db", help="Database file path"
    )
    import_review_parser.add_argument(
        "--media-dir",
        type=str,
        default="src/media/audio",
        help="Audio media directory (default: src/media/audio)",
    )
    import_review_parser.add_argument(
        "--data-dir", type=str, default="src/data", help="Data folder with CSV files"
    )

    release_parser = subparsers.add_parser(
        "release",
        help="Release management commands",
        description="Manage deck releases and versioning. Use --list to show all registered decks with their current versions, latest release versions, and AnkiWeb upload status.",
    )
    release_parser.add_argument("deck_id", nargs="?", help="Deck ID to release")
    release_parser.add_argument(
        "--version", type=str, help="Target version (e.g., 1.0.0)"
    )
    release_parser.add_argument(
        "--dry-run", action="store_true", help="Validate without making changes"
    )
    release_parser.add_argument(
        "--finalize",
        type=str,
        metavar="APKG_PATH",
        help="Finalize release with .apkg file",
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
    release_parser.add_argument(
        "-d", "--database", type=str, default="data.db", help="Database file path"
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
        default="website/content/decks",
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
            delay=args.delay,
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
        csv2sqlite(
            Path(args.input),
            Path(args.database),
            force=args.force,
            fail_if_conflict=args.fail_if_conflict,
        )
    elif args.command == "sqlite2csv":
        sqlite2csv(
            Path(args.database),
            Path(args.output),
            force=args.force,
            fail_if_conflict=args.fail_if_conflict,
        )
    elif args.command == "export-review":
        export_review(
            Path(args.database),
            args.source,
            args.target,
            Path(args.output),
            Path(args.media_dir),
            Path(args.data_dir),
        )
    elif args.command == "import-review":
        import_review(
            Path(args.file),
            Path(args.database),
            args.source,
            args.target,
            Path(args.media_dir),
            Path(args.data_dir),
        )
    elif args.command == "release":
        if args.list:
            registry = DeckRegistry(Path(args.registry))
            print_deck_list(registry, Path(args.database))
        elif args.deck_id and args.finalize:
            registry = DeckRegistry(Path(args.registry))
            finalize_release(registry, args.deck_id, Path(args.finalize))
        elif args.deck_id:
            if not args.version:
                print("Error: --version is required when releasing a deck")
                release_parser.print_help()
                return

            registry = DeckRegistry(Path(args.registry))
            run_release(
                registry,
                args.deck_id,
                args.version,
                dry_run=args.dry_run,
            )
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


def print_deck_list(registry: DeckRegistry, db_path: Path = Path("data.db")):
    """Print a formatted list of all decks and their status."""
    import sqlite3
    from al_tools.core import _ensure_db_exists, _check_db_freshness

    decks = sorted(registry.all(), key=lambda d: d.deck_id)

    if not decks:
        print("No decks found in registry.")
        return

    # Ensure database exists and is fresh
    data_dir = Path("src/data")
    _ensure_db_exists(db_path, data_dir)
    _check_db_freshness(db_path, data_dir, force=True)

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get total vocabulary count for percentage calculations
    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    total_vocab = cursor.fetchone()[0]

    # Calculate column widths
    max_id_len = max(len(d.deck_id) for d in decks)
    max_version_len = max(len(d.version) for d in decks)

    # Print header
    print()
    print(
        f"{'DECK':<{max_id_len}}  {'VERSION':<{max_version_len}}  {'TRANSL':<7}  {'AUDIO':<6}  {'LAST RELEASE':<13}  ANKIWEB"
    )
    print("-" * (max_id_len + max_version_len + 7 + 6 + 13 + 30))

    # Print each deck
    for deck in decks:
        last_release = registry.get_latest_release_version(deck.deck_id)
        last_release_str = last_release if last_release else "-"

        ankiweb_str = f"✓ {deck.ankiweb_id}" if deck.ankiweb_id else "✗ (not uploaded)"

        # Calculate completion percentages based on deck type
        if deck.deck_type == "625":
            # For 625 decks, check if target locale has actual text
            cursor.execute(
                """
                SELECT COUNT(*) FROM base_language
                WHERE locale = ? AND text IS NOT NULL AND text <> ''
                """,
                (deck.target_locale,),
            )
            translation_count = cursor.fetchone()[0]
            translation_pct_raw = (
                int((translation_count / total_vocab) * 100) if total_vocab > 0 else 0
            )

            # Show "<1%" for partial progress, avoid showing "0%" when there's some progress
            if translation_count > 0 and translation_pct_raw == 0:
                translation_pct = "<1"
            else:
                translation_pct = translation_pct_raw

            # Check target locale audio completion
            cursor.execute(
                """
                SELECT COUNT(*) FROM base_language
                WHERE locale = ? AND audio IS NOT NULL AND audio <> ''
                """,
                (deck.target_locale,),
            )
            audio_count = cursor.fetchone()[0]
            audio_pct_raw = (
                int((audio_count / total_vocab) * 100) if total_vocab > 0 else 0
            )

            # Show "<1%" for partial progress
            if audio_count > 0 and audio_pct_raw == 0:
                audio_pct = "<1"
            else:
                audio_pct = audio_pct_raw

        elif deck.deck_type == "minimal_pairs":
            # For minimal_pairs decks, use minimal_pairs table
            cursor.execute(
                """
                SELECT COUNT(*) FROM minimal_pairs
                WHERE source_locale = ? AND target_locale = ?
                """,
                (deck.source_locale, deck.target_locale),
            )
            total_pairs = cursor.fetchone()[0]

            # Translation percentage: just show how many pairs exist (denominator is itself)
            translation_pct = 100 if total_pairs > 0 else 0

            # Audio percentage: check how many have both audio1 and audio2
            cursor.execute(
                """
                SELECT COUNT(*) FROM minimal_pairs
                WHERE source_locale = ? AND target_locale = ?
                AND audio1 IS NOT NULL AND audio1 <> ''
                AND audio2 IS NOT NULL AND audio2 <> ''
                """,
                (deck.source_locale, deck.target_locale),
            )
            audio_complete = cursor.fetchone()[0]
            audio_pct_raw = (
                int((audio_complete / total_pairs) * 100) if total_pairs > 0 else 0
            )

            # Show "<1%" for partial progress
            if audio_complete > 0 and audio_pct_raw == 0:
                audio_pct = "<1"
            else:
                audio_pct = audio_pct_raw

        else:
            # Unknown deck type
            translation_pct = 0
            audio_pct = 0

        # Format the percentage strings
        transl_str = (
            f"{translation_pct}%"
            if isinstance(translation_pct, int)
            else f"{translation_pct}%"
        )
        audio_str = f"{audio_pct}%" if isinstance(audio_pct, int) else f"{audio_pct}%"

        print(
            f"{deck.deck_id:<{max_id_len}}  {deck.version:<{max_version_len}}  {transl_str:<7}  {audio_str:<6}  {last_release_str:<13}  {ankiweb_str}"
        )

    conn.close()
    print()


def generate_website_page_for_deck(
    registry: DeckRegistry, deck_id: str, output_dir: Path
):
    """Generate website page for a specific deck and update the overview page."""
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

    # Update overview page
    overview_content = generate_deck_overview_page(registry)
    output_dir.mkdir(parents=True, exist_ok=True)
    overview_file = output_dir / "_index.md"
    overview_file.write_text(overview_content)
    print(f"✓ Updated overview page: {overview_file}")


def generate_all_website_pages(registry: DeckRegistry, output_dir: Path):
    """Generate website pages for all decks."""
    decks = sorted(registry.all(), key=lambda d: d.deck_id)

    if not decks:
        print("No decks found in registry.")
        return

    # Generate overview page
    overview_content = generate_deck_overview_page(registry)
    overview_file = output_dir / "_index.md"
    output_dir.mkdir(parents=True, exist_ok=True)
    overview_file.write_text(overview_content)
    print(f"✓ Generated overview page: {overview_file}")

    # Generate individual deck pages
    for deck in decks:
        generate_website_page_for_deck(registry, deck.deck_id, output_dir)

    print(f"\n✓ Generated {len(decks)} deck pages + overview page")


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


def run_release(
    registry: DeckRegistry,
    deck_id: str,
    target_version: str,
    dry_run: bool = False,
):
    """Run a deck release with validation.

    Args:
        registry: Deck registry
        deck_id: ID of deck to release
        target_version: Target version (e.g., "1.0.0")
        dry_run: If True, only validate without making changes
    """
    import subprocess
    from al_tools.release import (
        Version,
        validate_release,
        regenerate_description_file,
        update_decks_yaml_version,
        create_release_commit,
        create_git_tag,
        create_post_release_commit,
    )

    # Get the deck
    deck = registry.get(deck_id)
    if not deck:
        print(f"❌ Error: Deck '{deck_id}' not found in registry")
        return

    print(f"\n{'=' * 70}")
    print(f"Release: {deck.name}")
    print(f"Current version: {deck.version}")
    print(f"Target version:  {target_version}")
    if dry_run:
        print("Mode: DRY RUN (no changes will be made)")
    print(f"{'=' * 70}\n")

    # Validate the release
    print("[1/9] Validating release...\n")
    result = validate_release(deck, target_version)

    # Print validation results
    print(result.format())
    print()

    if not result.is_valid:
        print("❌ Release validation failed. Please fix the errors above.")
        return

    # Calculate next dev version
    target_ver = Version.parse(target_version)
    next_dev_version = str(target_ver.next_minor_dev())

    if dry_run:
        print("\n✓ Validation passed. Here's what would be done:\n")
        print("  1. Run pre-release checks (just check-code)")
        print(f"  2. Update versions to {target_version}")
        print(f"     • {deck.description_file} (full regeneration)")
        print("     • decks.yaml")
        print("  3. Run build (just build)")
        print("  4. Generate website page")
        print(
            f"  5. Create release commit: 'release: {deck.tag_name} {target_version}'"
        )
        print(f"  6. Create git tag: {deck.tag_name}/{target_version}")
        print(f"  7. Update versions to {next_dev_version}")
        print(f"     • {deck.description_file} (full regeneration)")
        print("     • decks.yaml")
        print(
            f"  8. Create post-release commit: 'chore: bump {deck_id} to {next_dev_version}'"
        )
        print()
        print("Run without --dry-run to perform the release.")
        return

    # Perform the release
    try:
        # Step 2: Run pre-release checks
        print("[2/9] Running pre-release checks...\n")
        print("  • Running code checks...")
        result = subprocess.run(
            ["just", "check-code"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(f"❌ Code checks failed:\n{result.stderr}")
            return
        print("  ✓ Code checks passed")
        print()

        # Step 3: Update versions to release version
        print(f"[3/9] Updating versions to {target_version}...\n")

        description_path = Path(deck.description_file)
        print(f"  • Regenerating {description_path}...")
        regenerate_description_file(deck, target_version)
        print(f"    ✓ Regenerated with version {target_version}")

        registry_path = registry.registry_path
        print(f"  • Updating {registry_path}...")
        update_decks_yaml_version(registry_path, deck_id, target_version)
        print(f"    ✓ Updated to {target_version}")
        print()

        # Step 4: Build
        print("[4/9] Running build...\n")
        print("  • Running just build...")
        result = subprocess.run(
            ["just", "build"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(f"❌ Build failed:\n{result.stdout}\n{result.stderr}")
            return
        print("  ✓ Build completed")
        print()

        # Step 5: Generate website page (reload registry to pick up updated version)
        print("[5/9] Generating website page...\n")
        registry = DeckRegistry(registry_path)
        website_output_dir = Path("website/content/decks")
        generate_website_page_for_deck(registry, deck_id, website_output_dir)
        print()

        # Step 6: Create release commit
        print("[6/9] Creating release commit...\n")
        create_release_commit(deck, target_version)
        print()

        # Step 7: Create git tag
        print("[7/9] Creating git tag...\n")
        create_git_tag(deck, target_version)
        print()

        # Step 8: Update versions to next dev version
        print(f"[8/9] Updating versions to {next_dev_version}...\n")

        print(f"  • Regenerating {description_path}...")
        regenerate_description_file(deck, next_dev_version)
        print(f"    ✓ Regenerated with version {next_dev_version}")

        print(f"  • Updating {registry_path}...")
        update_decks_yaml_version(registry_path, deck_id, next_dev_version)
        print(f"    ✓ Updated to {next_dev_version}")
        print()

        # Step 9: Create post-release commit
        print("[9/9] Creating post-release commit...\n")
        create_post_release_commit(deck, next_dev_version)
        print()

        print("=" * 70)
        print("✓ Release complete!")
        print("=" * 70)
        print()
        print("Next steps:")
        print()
        print("  1. Import deck into Anki and export as .apkg:")
        print(f"     File → Import → build/{deck.tag_name}")
        print(f"     File → Export → {deck.tag_name} - {target_version}.apkg")
        print()
        print("  2. Finalize the release:")
        print(f"     al-tools release {deck_id} --finalize <path-to-apkg>")
        print()

    except Exception as e:
        print(f"\n❌ Error during release: {e}")
        import traceback

        traceback.print_exc()
        return


def finalize_release(registry: DeckRegistry, deck_id: str, apkg_path: Path):
    """Finalize a release by creating GitHub release and AnkiWeb description.

    Args:
        registry: Deck registry
        deck_id: ID of deck to finalize
        apkg_path: Path to .apkg file
    """
    import subprocess

    # Get the deck
    deck = registry.get(deck_id)
    if not deck:
        print(f"❌ Error: Deck '{deck_id}' not found in registry")
        return

    # Find the latest tag for this deck
    latest_version = registry.get_latest_release_version(deck_id)
    if not latest_version:
        print(
            f"❌ Error: No release tag found for {deck_id}. Run 'al-tools release' first."
        )
        return

    tag_name = f"{deck.tag_name}/{latest_version}"

    print(f"\n{'=' * 70}")
    print(f"Finalize Release: {deck.name}")
    print(f"Version: {latest_version}")
    print(f"Tag: {tag_name}")
    print(f"{'=' * 70}\n")

    # Validate .apkg file
    print("[1/3] Validating .apkg file...\n")
    if not apkg_path.exists():
        print(f"❌ Error: File not found: {apkg_path}")
        return
    if not apkg_path.suffix == ".apkg":
        print(f"❌ Error: File is not an .apkg file: {apkg_path}")
        return
    print(f"  ✓ Found .apkg file: {apkg_path}")

    # Check naming convention

    expected_name = get_apkg_filename(
        source_locale=deck.source_locale,
        target_locale=deck.target_locale,
        deck_type=deck.deck_type,
        version=latest_version,
    )
    actual_name = apkg_path.name

    if actual_name != expected_name:
        print("  ⚠ Filename does not match convention:")
        print(f"    Current:  {actual_name}")
        print(f"    Expected: {expected_name}")
        response = input("  Rename for upload? [Y/n] ").strip().lower()
        if response not in ("", "y", "yes"):
            print("❌ Aborted.")
            return
        # Copy to temp dir with correct name for upload
        import shutil
        import tempfile

        original_path = apkg_path
        tmpdir = Path(tempfile.mkdtemp(prefix="ankilangs_release_"))
        apkg_path = tmpdir / expected_name
        shutil.copy2(original_path, apkg_path)
        print(f"  ✓ Copied as: {apkg_path}")
    print()

    # Generate release notes
    print("[2/3] Creating GitHub release...\n")

    try:
        # Generate release notes from changelog
        generator = ContentGenerator(deck)
        release_notes = generator.generate_github_release_notes(latest_version)

        # Create GitHub release
        print(f"  • Creating release {tag_name}...")
        result = subprocess.run(
            [
                "gh",
                "release",
                "create",
                tag_name,
                str(apkg_path),
                "--title",
                f"{deck.name} {latest_version}",
                "--notes",
                release_notes,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"  ✓ Release created: {result.stdout.strip()}")
        release_url = result.stdout.strip()
        print()

    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating GitHub release: {e.stderr}")
        return
    except FileNotFoundError:
        print("❌ Error: gh CLI not found. Install from: https://cli.github.com/")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # Generate AnkiWeb description
    print("[3/3] Generating AnkiWeb description...\n")

    output_dir = Path("build")
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = ContentGenerator(deck)
    description = generator.generate_ankiweb_description()

    output_file = output_dir / f"ankiweb_description_{deck_id}.md"
    output_file.write_text(description)

    print(f"  ✓ Written to: {output_file}")

    # Try to copy to clipboard
    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=description.encode(),
            check=True,
        )
        print("  ✓ Copied to clipboard")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ⚠ Could not copy to clipboard (xclip not available)")

    print()
    print("=" * 70)
    print("✓ Release finalized!")
    print("=" * 70)
    print()
    print("Next steps:")
    print()
    print("  1. Push to GitHub:")
    print("     jj git push")
    print("     git push --tags")
    print()
    print(f"  2. Update AnkiWeb deck (ID: {deck.ankiweb_id}):")
    print("     • Visit: https://ankiweb.net/shared/upload")
    print(f"     • Upload: {apkg_path}")
    print(f"     • Paste description from: {output_file}")
    print()
    print(f"  3. View release: {release_url}")
    print()
