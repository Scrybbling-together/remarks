import argparse
import logging
import pathlib

from remarks import run_remarks

__prog_name__ = "remarks"
__version__ = "0.3.1"


def main():
    parser = argparse.ArgumentParser(__prog_name__, add_help=False)

    parser.add_argument(
        "input_dir",
        help="xochitl-derived directory that contains *.pdf, *.content, *.metadata, *.highlights/*.json and */*.rm files",
        metavar="INPUT_DIRECTORY",
    )
    parser.add_argument(
        "output_dir",
        help="Base directory for all files created (*.pdf, *.png, *.md, and/or *.svg)",
        metavar="OUTPUT_DIRECTORY",
    )
    parser.add_argument(
        "-m",
        "--export_markdown",
        action="store_true",
        help="Export the obsidian markdown"
    )
    parser.add_argument(
        "-o",
        "--export_org",
        action="store_true",
        help="Export the org-mode file"
    )
    parser.add_argument(
        "-O",
        "--override",
        action="store_true",
        help="Override existing files (/!\\ use at your own risk!)"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="Show remarks version number",
        version="%(prog)s {version}".format(version=__version__),
    )
    parser.add_argument(
        "--log_level",
        help="Print out log messages with equal or higher severity level as specified by LOG_LEVEL. Currently supported: DEBUG < INFO < WARNING < ERROR. Choose DEBUG to print out all messages, ERROR to print out just error messages, etc. If a log level is not set, it defaults to INFO",
        default="INFO",
        metavar="LOG_LEVEL",
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message",
    )

    args = parser.parse_args()
    args_dict = vars(args)

    input_dir = pathlib.Path(args_dict.pop("input_dir"))
    output_dir = pathlib.Path(args_dict.pop("output_dir"))

    log_level = args_dict.pop("log_level")
    logging.basicConfig(
        format="%(message)s",
        level=log_level
    )

    if not input_dir.exists():
        parser.error(f'Directory "{input_dir}" does not exist')

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    run_remarks(input_dir, output_dir, override=args.override, export_markdown=args.export_markdown, export_org=args.export_org)


if __name__ == "__main__":
    main()
