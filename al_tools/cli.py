import argparse
from pathlib import Path

from al_tools.core import generate_audio, AudioExistsAction


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

    args = parser.parse_args()

    if args.command == "audio":
        generate_audio(
            Path(args.input),
            Path(args.output),
            AudioExistsAction(args.action),
        )
    else:
        parser.print_help()
