import argparse
import json
import os
import sys
import threading
import traceback
from pathlib import Path

from exceptions import EC_ARG_GENERAL, MESSAGE_ARG_GENERAL, ExpectedException
from html_to_pdf import convert_to_pdf
from image_update import DockerImageContainerUpdateChecker


def set_arguments(
    parser: argparse.ArgumentParser, names: list, required_output: bool = True, output_help: str = ""
) -> None:
    """
    Set arguments for the parser based on the provided names and options.

    Args:
        parser (argparse.ArgumentParser): The argument parser to set arguments for.
        names (list): List of argument names to set.
        required_output (bool): Whether the output argument is required. Defaults to True.
        output_help (str): Help shown for output argument. Defaults to "".
    """
    for name in names:
        match name:
            case "input":
                parser.add_argument("--input", "-i", type=str, required=True, help="The URL or input HTML file")
            case "output":
                parser.add_argument("--output", "-o", type=str, required=required_output, help=output_help)
            case "version":
                parser.add_argument("--version", "-v", help="Print version", action="store_true")


def run_config_subcommand(args) -> None:
    get_pdfix_config(args.output)


def get_pdfix_config(path: str) -> None:
    """
    If Path is not provided, output content of config.
    If Path is provided, copy config to destination path.

    Args:
        path (string): Destination path for config.json file
    """
    config_path = os.path.join(Path(__file__).parent.absolute(), "../config.json")

    with open(config_path, "r", encoding="utf-8") as file:
        if path is None:
            print(file.read())
        else:
            with open(path, "w") as out:
                out.write(file.read())


def run_html_to_pdf_subcommand(args) -> None:
    if args.version:
        print_version()
    else:
        html_to_pdf(args.input, args.output)


def print_version() -> None:
    """
    Prints version found in config.json file.
    """
    config_path = os.path.join(Path(__file__).parent.absolute(), "../config.json")
    with open(config_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        if "version" in data:
            # Skip "v:" from "version" data
            print(f"Version: {data['version'][2:]}")


def html_to_pdf(url: str, output_path: str) -> None:
    """
    Converts HTML page (found in URL or file system) to PDF document.

    Args:
        url (str): URL or path to file.
        output_path (str): Path to output PDF document
    """
    convert_to_pdf(url, output_path)


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="subparser")

    # Config subcommand
    config_parser = subparsers.add_parser("config", help="Save the default configuration file")
    set_arguments(
        config_parser,
        ["output"],
        False,
        "Output to save the config JSON file. Application output is used if not provided",
    )
    config_parser.set_defaults(func=run_config_subcommand)

    # Html to pdf subcommand
    html_to_pdf_parser = subparsers.add_parser(
        "html-to-pdf",
        help="Convert HTML to PDF document.",
    )
    set_arguments(html_to_pdf_parser, ["input", "output", "version"], True, "Output PDF file")
    html_to_pdf_parser.set_defaults(func=run_html_to_pdf_subcommand)

    # Parse arguments
    try:
        args = parser.parse_args()
    except SystemExit as e:
        if e.code != 0:
            print(MESSAGE_ARG_GENERAL, file=sys.stderr)
            sys.exit(EC_ARG_GENERAL)
        # This happens when --help is used, exit gracefully
        sys.exit(0)

    if hasattr(args, "func"):
        # Check for updates only when help is not checked
        update_checker = DockerImageContainerUpdateChecker()
        # Check it in separate thread not to be delayed when there is slow or no internet connection
        update_thread = threading.Thread(target=update_checker.check_for_image_updates)
        update_thread.start()

        # Run subcommand
        try:
            args.func(args)
        except ExpectedException as e:
            print(e.message, file=sys.stderr)
            sys.exit(e.error_code)
        except Exception as e:
            print(traceback.format_exc(), file=sys.stderr)
            print(f"Failed to run the program: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            # Make sure to let update thread finish before exiting
            update_thread.join()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
