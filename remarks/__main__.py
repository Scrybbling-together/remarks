import logging
import pathlib
import argparse

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
        "--file_path",
        help="Work only on files whose (meaningful) path contains this string",
        metavar="FILEPATH_STRING",
    )
    parser.add_argument(
        "--ann_type",
        help="Force remarks to handle only a specific type of annotation: highlights or scribbles. If none is specified, remarks will handle both by default",
        default=["scribbles", "highlights"],
        metavar="ANNOTATION_TYPE",
    )
    parser.add_argument(
        "--skip_combined_pdf",
        dest="combined_pdf",
        action="store_false",
        help="Skip the creation of the default '*_remarks.pdf' file that contains all annotated pages merged into the original PDF file",
    )
    parser.add_argument(
        "--modified_pdf",
        dest="modified_pdf",
        action="store_true",
        help="Create a '*_remarks-only.pdf' file with annotated pages only (unannotated ones will be out)",
    )
    parser.add_argument(
        "--per_page_targets",
        nargs="+",
        help="Target specific file formats per page. Choose at least one of the following extensions: md pdf png svg. This is empty by default",
        default=[],
        metavar="FILE_EXTENSION",
    )
    parser.add_argument(
        "--assume_malformed_pdfs",
        dest="assume_malformed_pdfs",
        action="store_true",
        help="Assume PDF files are malformed, i.e. words are NOT in their natural reading order and/or fonts are obfuscated. By default, we're optimists and assume your PDFs are well-formed",
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

    parser.set_defaults(
        combined_pdf=True,
        modified_pdf=False,
        assume_malformed_pdfs=False,
    )

    args = parser.parse_args()
    args_dict = vars(args)

    input_dir = args_dict.pop("input_dir")
    output_dir = args_dict.pop("output_dir")

    log_level = args_dict.pop("log_level")
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
    )

    if not pathlib.Path(input_dir).exists():
        parser.error(f'Directory "{input_dir}" does not exist')

    if not pathlib.Path(output_dir).is_dir():
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    run_remarks(input_dir, output_dir, **args_dict)


if __name__ == "__main__":
    main()
