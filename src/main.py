import argparse
import logging
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from constants import CONFIG_FILE
from exceptions import (
    EC_ARG_GENERAL,
    MESSAGE_ARG_GENERAL,
    ArgumentInputFileNotExistsException,
    ArgumentOutputFolderNotExistsException,
    ArgumentOutputPdfException,
    ExpectedException,
)
from html_to_pdf import convert_to_pdf
from image_update import DockerImageContainerUpdateChecker
from logger import get_logger

logger: logging.Logger = get_logger(__name__)


def set_arguments(
    parser: argparse.ArgumentParser,
    names: list[str],
    required_output: bool = True,
    output_help: str = "",
) -> None:
    """
    Set arguments for the parser based on the provided names and options.

    Args:
        parser (argparse.ArgumentParser): The argument parser to set arguments for.
        names (list[str]): List of argument names to set.
        required_output (bool): Whether the output argument is required. Defaults to True.
        output_help (str): Help shown for output argument. Defaults to "".
    """
    for name in names:
        match name:
            case "input":
                parser.add_argument("--input", "-i", type=str, required=True, help="The URL or input HTML file")
            case "output":
                parser.add_argument("--output", "-o", type=str, required=required_output, help=output_help)


def run_config_subcommand(args) -> None:
    get_pdfix_config(args.output)


def get_pdfix_config(path: str) -> None:
    """
    If Path is not provided, output content of config.
    If Path is provided, copy config to destination path.

    Args:
        path (string): Destination path for config.json file
    """
    config_path: Path = Path(__file__).parent.parent.joinpath(CONFIG_FILE).resolve()

    with open(config_path, "r", encoding="utf-8") as file:
        if path is None:
            print(file.read())
        else:
            with open(path, "w") as out:
                out.write(file.read())


def run_html_to_pdf_subcommand(args) -> None:
    html_to_pdf(args.input, args.output)


# @KA:action pdfix_convert_html_to_pdf_chrome
# @KA:desc Converts an HTML file to a tagged PDF using the Chromium web browser. The page is opened
# like in a browser, with its CSS, images and scripts from the same folder, and printed to PDF. The
# tags come from the structure of the HTML. The input file is not changed, the PDF is saved as the
# output file.
# @KA:context Run when you have a webpage saved as an HTML file and need an accessible PDF of it. The
# result is only as accessible as the HTML: use headings, lists, tables, `alt` on images, `lang` and a
# `<title>`. Runs locally in Docker, no PDFix license is needed; the first run downloads the image and
# takes longer.
#
# @KA:action pdfix_convert_url_to_pdf_chrome
# @KA:desc Converts a webpage to a tagged PDF using the Chromium web browser. Chromium opens the
# address like a browser, loads the page with its CSS, images and scripts, and prints it to PDF. The
# tags come from the structure of the page. The PDF is saved as the output file.
# @KA:context Run when you need an accessible PDF of a public webpage. Needs an internet connection;
# the page is opened from your computer. The result is only as accessible as the page: headings,
# lists, tables, `alt` on images, `lang` and a `<title>`. Runs locally in Docker, no PDFix license is
# needed; the first run downloads the image and takes longer.
def html_to_pdf(url: str, output_path: str) -> None:
    """
    Converts HTML page (found in URL or file system) to PDF document.

    Args:
        url (str): URL or path to file.
        output_path (str): Path to output PDF document
    """
    # The action always runs in a Linux Docker container, so a local HTML file is an absolute path that starts
    # with "/" (PDFix Desktop passes "/data/<file>"). Input that is not an existing file and does not start with "/"
    # is a URL, there is no other way to tell a file name from a URL without scheme (e.g. "example.com").
    # @KA:action pdfix_convert_html_to_pdf_chrome
    # @KA:param input_html
    # @KA:desc HTML file to convert. CSS, images and scripts that the page links with relative paths
    # must be in the same folder (or its subfolders), otherwise they are missing in the PDF.
    # @KA:problem "Input file does not exist." (error 13)
    # @KA:solution The file shown in the message was not found. Check the path.
    if url.startswith("/") and not Path(url).is_file():
        raise ArgumentInputFileNotExistsException(url)

    # @KA:action pdfix_convert_html_to_pdf_chrome pdfix_convert_url_to_pdf_chrome
    # @KA:param output_pdf
    # @KA:desc Where the PDF is saved. It must have the `.pdf` extension and the folder must already
    # exist; an existing file with the same name is overwritten.
    # @KA:problem "Output file must be PDF document." (error 11)
    # @KA:solution Use an output file name with the `.pdf` extension.
    # @KA:problem "Output folder does not exist." (error 12)
    # @KA:solution Create the folder shown in the message or select another output file.
    if not output_path.lower().endswith(".pdf"):
        raise ArgumentOutputPdfException()

    output_folder: Path = Path(output_path).resolve().parent
    if not output_folder.is_dir():
        raise ArgumentOutputFolderNotExistsException(output_folder.as_posix())

    convert_to_pdf(url, output_path)


def main() -> None:
    """Parse CLI arguments and run the selected subcommand."""
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="Commands", dest="command", required=True)

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
    set_arguments(html_to_pdf_parser, ["input", "output"], True, "Output PDF file")
    html_to_pdf_parser.set_defaults(func=run_html_to_pdf_subcommand)

    # Parse arguments
    try:
        args = parser.parse_args()
    except ExpectedException as e:
        logger.error(e.message)
        sys.exit(e.error_code)
    except SystemExit as e:
        if e.code != 0:
            logger.error(MESSAGE_ARG_GENERAL)
            sys.exit(EC_ARG_GENERAL)
        # This happens when --help is used, exit gracefully
        sys.exit(0)
    except Exception as e:
        logger.error("Failed to run the program:")
        logger.exception(e)
        sys.exit(1)

    if hasattr(args, "func"):
        # Check for updates only when help is not checked
        update_checker = DockerImageContainerUpdateChecker()
        # Check it in separate thread not to be delayed when there is slow or no internet connection
        update_thread = threading.Thread(target=update_checker.check_for_image_updates)
        update_thread.start()

        # Measure the time it takes to make all requests
        start_time = time.time()  # Record the start time
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logger.info(f"Processing started at: {current_time}")

        # Run subcommand
        try:
            args.func(args)
        except ExpectedException as e:
            logger.error(e.message)
            sys.exit(e.error_code)
        except Exception as e:
            # not expected exception -> print stack trace and what exception happened
            logger.error("Failed to run the program:")
            logger.exception(e)
            sys.exit(1)
        finally:
            end_time = time.time()  # Record the end time
            elapsed_time = end_time - start_time  # Calculate the elapsed time
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            logger.info(f"Processing finished at: {current_time}. Elapsed time: {elapsed_time:.2f} seconds")

            # Make sure to let update thread finish before exiting
            update_thread.join()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
