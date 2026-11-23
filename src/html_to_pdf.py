import logging
from pathlib import Path

from tqdm import tqdm

from chromium_pdf_printer import ChromiumPdfPrinter
from constants import CHROMIUM_EXECUTABLE
from exceptions import ExpectedException, FailedToConvertException
from logger import get_logger

logger: logging.Logger = get_logger(__name__)


def convert_to_pdf(url: str, output: str) -> None:
    """
    Converts a local HTML file or remote URL to a PDF document.

    Args:
        url (str): URL or path to a local HTML file.
        output (str): Path to output PDF document.

    Raises:
        FailedToOpenWebpageException: If the webpage cannot be opened.
        UrlNotWebpageException: If the URL opens a PDF document.
        FailedToConvertException: If Chromium is missing or conversion fails.
    """
    output_path: Path = Path(output).resolve()
    printer: ChromiumPdfPrinter = ChromiumPdfPrinter()

    with tqdm(total=100) as progress_bar:
        input_path: Path = Path(url)
        page_url: str
        # Existing file is a local HTML document, anything else is a URL (missing file is reported by arguments check)
        if input_path.is_file():
            progress_bar.set_description("Reading local file")
            page_url = input_path.resolve().as_uri()
        else:
            # Chromium opens the webpage itself, so the page is printed with its CSS, images and scripts
            progress_bar.set_description("Opening webpage")
            page_url = url if "://" in url else f"https://{url}"

        progress_bar.n = 50
        progress_bar.set_description("Converting")
        progress_bar.refresh()

        if not Path(CHROMIUM_EXECUTABLE).is_file():
            logger.error("Chromium executable was not found.")
            raise FailedToConvertException()

        # @KA:action pdfix_convert_html_to_pdf_chrome pdfix_convert_url_to_pdf_chrome
        # @KA:logic Conversion failed
        # @KA:desc When Chromium cannot print the page, the action stops and no PDF is created. The log
        # shows the reason.
        # @KA:problem "Failed to convert HTML to PDF." (error 31)
        # @KA:solution Open the page in a browser to check that it works, then run the action again.
        try:
            printer.print_html_to_pdf(page_url, output_path, progress_bar)
            logger.debug("Command executed successfully")
        except ExpectedException:
            raise
        except Exception as e:
            logger.error(f"{e}")
            raise FailedToConvertException()

        progress_bar.n = 100
        progress_bar.set_description("Done")
        progress_bar.refresh()
