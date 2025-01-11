import argparse
from pathlib import Path

from al_tools.core import (
    generate_audio,
    AudioExistsAction,
    generate_joined_source_fields,
)


def cli():
    """Command line interface for the al_tools package."""
    parser = argparse.ArgumentParser()
    parser.set_defaults(command=None)

    subparsers = parser.add_subparsers(dest="command")

    audio_parser = subparsers.add_parser("audio")
    audio_parser.add_argument(
        "-i", "--input", type=str, required=True, help="Input CSV file"
    )
    audio_parser.add_argument(
        "-o", "--output", type=str, required=True, help="Output audio folder"
    )
    audio_parser.add_argument(
        "-a",
        "--action",
        type=str,
        default="skip",
        choices=["skip", "overwrite", "raise"],
    )

    generate_parser = subparsers.add_parser(
        "generate", help="Generate files in 'generated' folder"
    )
    generate_parser.add_argument(
        "-i", "--input", type=str, required=True, help="Input folder"
    )

    args = parser.parse_args()

    if args.command == "audio":
        generate_audio(
            Path(args.input),
            Path(args.output),
            AudioExistsAction(args.action),
        )
    elif args.command == "generate":
        generate_joined_source_fields(Path(args.input))
    else:
        parser.print_help()
