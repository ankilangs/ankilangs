import argparse
from pathlib import Path

from al_tools.core import (
    generate_audio,
    AudioExistsAction,
    generate_joined_source_fields,
    ambiguity_detection,
    sort_csv_files,
    csv2sqlite,
    sqlite2csv,
)
from al_tools.registry import DeckRegistry


def cli():
    """Command line interface for the al_tools package."""
    parser = argparse.ArgumentParser()
    parser.set_defaults(command=None)

    subparsers = parser.add_subparsers(dest="command")

    audio_parser = subparsers.add_parser("audio")
    audio_parser.add_argument(
        "-l", "--locale", type=str, required=True, help="Locale (e.g., en_us, es_es)"
    )
    audio_parser.add_argument(
        "-o", "--output", type=str, required=True, help="Output audio folder"
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
        "--limit",
        type=int,
        default=None,
        help="Maximum number of audio files to generate (to limit API costs)",
    )

    generate_parser = subparsers.add_parser(
        "generate", help="Generate files in 'generated' folder from SQLite"
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
        "check", help="Check for ambiguous words in SQLite"
    )
    check_parser.add_argument(
        "-d", "--database", type=str, default="data.db", help="Database file path"
    )
    check_parser.add_argument(
        "--data-dir", type=str, default="src/data", help="Data folder with CSV files"
    )

    sort_csv_parser = subparsers.add_parser(
        "sort-csv", help="Sort CSV files alphabetically by key"
    )
    sort_csv_parser.add_argument(
        "-i", "--input", type=str, required=True, help="Data folder"
    )

    csv2sqlite_parser = subparsers.add_parser(
        "csv2sqlite", help="Import CSV files to SQLite"
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
        "sqlite2csv", help="Export SQLite to CSV files"
    )
    sqlite2csv_parser.add_argument(
        "-d", "--database", type=str, required=True, help="Database file path"
    )
    sqlite2csv_parser.add_argument(
        "-o", "--output", type=str, required=True, help="Output data folder"
    )

    release_parser = subparsers.add_parser(
        "release", help="Release management commands"
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

    args = parser.parse_args()

    if args.command == "audio":
        generate_audio(
            Path(args.database),
            args.locale,
            Path(args.output),
            AudioExistsAction(args.action),
            Path(args.data_dir),
            limit=args.limit,
        )
    elif args.command == "generate":
        generate_joined_source_fields(
            Path(args.database), Path(args.output), Path(args.data_dir)
        )
    elif args.command == "check":
        output = ambiguity_detection(Path(args.database), Path(args.data_dir))
        print(output)
    elif args.command == "sort-csv":
        sort_csv_files(Path(args.input))
    elif args.command == "csv2sqlite":
        csv2sqlite(Path(args.input), Path(args.database), force=args.force)
    elif args.command == "sqlite2csv":
        sqlite2csv(Path(args.database), Path(args.output))
    elif args.command == "release":
        if args.list:
            registry = DeckRegistry(Path(args.registry))
            print_deck_list(registry)
        else:
            release_parser.print_help()
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
