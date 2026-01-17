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

    args = parser.parse_args()

    if args.command == "audio":
        generate_audio(
            Path(args.database),
            args.locale,
            Path(args.output),
            AudioExistsAction(args.action),
            Path(args.data_dir),
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
    else:
        parser.print_help()
