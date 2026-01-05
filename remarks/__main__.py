import argparse
import logging
import pathlib

from remarks import run_remarks
from rmc.exporters.svg import DEVICE_PROFILES

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
    parser.add_argument(
        "--device",
        choices=list(DEVICE_PROFILES.keys()),
        help="Device type (overrides auto-detection)",
        metavar="DEVICE",
    )
    parser.add_argument(
        "--templates-dir",
        help="Directory containing .template files (overrides built-in templates)",
        metavar="TEMPLATES_DIR",
    )
    parser.add_argument(
        "--no-chrome",
        action="store_true",
        help="Use Cairo instead of Chrome for PDF conversion",
    )
    parser.add_argument(
        "--chrome-loc",
        help="Path to Chrome/Chromium binary",
        metavar="PATH",
    )

    args = parser.parse_args()
    args_dict = vars(args)

    input_dir = pathlib.Path(args_dict.pop("input_dir"))
    output_dir = pathlib.Path(args_dict.pop("output_dir"))
    device = args_dict.pop("device")
    templates_dir_str = args_dict.pop("templates_dir")
    templates_dir = pathlib.Path(templates_dir_str) if templates_dir_str else None
    no_chrome = args_dict.pop("no_chrome")
    chrome_loc = args_dict.pop("chrome_loc")

    log_level = args_dict.pop("log_level")
    logging.basicConfig(
        format="%(message)s",
        level=log_level
    )

    if not input_dir.exists():
        parser.error(f'Directory "{input_dir}" does not exist')

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    if templates_dir and not templates_dir.exists():
        parser.error(f'Templates directory "{templates_dir}" does not exist')

    run_remarks(input_dir, output_dir, device=device, templates_dir=templates_dir,
                no_chrome=no_chrome, chrome_loc=chrome_loc)


if __name__ == "__main__":
    main()
