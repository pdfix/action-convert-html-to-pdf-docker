import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import requests
from tqdm import tqdm

from chromium_pdf_printer import ChromiumPdfPrinter
from constants import CHROMIUM_EXECUTABLE, DOWNLOAD_STREAM_CHUNK_SIZE, HTTP_REQUEST_TIMEOUT
from exceptions import ExpectedException, FailedToConvertException, FailedToDownloadException
from logger import get_logger

logger: logging.Logger = get_logger(__name__)


def download_website_to_file(url: str, destination: Path) -> None:
    """
    Downloads content of website page to a file without loading it into memory.

    Tries the URL as given, then with ``https://`` and ``http://`` prefixes.

    Args:
        url (str): URL to website.
        destination (Path): Path to write downloaded HTML.

    Raises:
        FailedToDownloadException: If all download attempts fail.
    """
    first_exception: Optional[Exception] = None

    for url_attempt in [url, f"https://{url}", f"http://{url}"]:
        exception: Optional[Exception] = try_download_url_to_file(url_attempt, destination)
        if exception is None:
            return
        if first_exception is None:
            first_exception = exception

    if first_exception is not None:
        logger.error("%s", first_exception)

    raise FailedToDownloadException()


def try_download_url_to_file(url: str, destination: Path) -> Optional[Exception]:
    """
    Tries to download content from URL into a file.

    Args:
        url (str): URL to website.
        destination (Path): Path to write downloaded HTML.

    Returns:
        None on success, or the exception that occurred.
    """
    try:
        with requests.get(url, stream=True, timeout=HTTP_REQUEST_TIMEOUT) as response:
            response.raise_for_status()
            with open(destination, "wb") as file:
                for chunk in response.iter_content(chunk_size=DOWNLOAD_STREAM_CHUNK_SIZE):
                    if chunk:
                        file.write(chunk)
    except requests.exceptions.HTTPError as e:
        logger.warning("For '%s' I got HTTPError", url)
        return e
    except requests.exceptions.ConnectionError as e:
        logger.warning("For '%s' I got ConnectionError", url)
        return e
    except requests.exceptions.Timeout as e:
        logger.warning("For '%s' I got Timeout", url)
        return e
    except requests.exceptions.RequestException as e:
        logger.warning("For '%s' I got RequestException", url)
        return e

    logger.info("For '%s' download completed", url)
    return None


def convert_to_pdf(url: str, output: str) -> None:
    """
    Converts a local HTML file or remote URL to a PDF document.

    Args:
        url (str): URL or path to a local HTML file.
        output (str): Path to output PDF document.

    Raises:
        FailedToDownloadException: If the input cannot be read or downloaded.
        FailedToConvertException: If Chromium is missing or conversion fails.
    """
    output_path: Path = Path(output).resolve()
    printer: ChromiumPdfPrinter = ChromiumPdfPrinter()

    with tqdm(total=100) as progress_bar:
        tempdir: Optional[tempfile.TemporaryDirectory[str]] = None
        html_path: Optional[Path] = None

        try:
            input_path: Path = Path(url)
            if input_path.is_file():
                progress_bar.set_description("Reading local file")
                html_path = input_path.resolve()
            else:
                progress_bar.set_description("Downloading webpage")
                tempdir = tempfile.TemporaryDirectory()
                html_path = Path(tempdir.name).joinpath(f"{uuid.uuid4()}.html")
                download_website_to_file(url, html_path)
        except ExpectedException:
            raise
        except Exception as e:
            logger.error("%s", e)
            raise FailedToDownloadException()

        if html_path is None:
            raise FailedToDownloadException()

        progress_bar.n = 50
        progress_bar.set_description("Converting")
        progress_bar.refresh()

        if not Path(CHROMIUM_EXECUTABLE).is_file():
            logger.error("Chromium executable was not found.")
            raise FailedToConvertException()

        if tempdir is None:
            logger.info("Using local HTML file")
        else:
            logger.info("Webpage saved into container")

        try:
            printer.print_html_to_pdf(html_path, output_path, progress_bar)
            logger.info("Command executed successfully")
        except ExpectedException:
            raise
        except Exception as e:
            logger.error("%s", e)
            raise FailedToConvertException()
        finally:
            if tempdir is not None:
                tempdir.cleanup()

        progress_bar.n = 100
        progress_bar.set_description("Done")
        progress_bar.refresh()
