import os
import platform
import subprocess
import sys
import tempfile
import uuid
from typing import Optional

import requests

from exceptions import FailedToConvertException, FailedToDownloadException


def setup_chrome_cli() -> str:
    """
    Setups chrome for system.

    Returns:
        Path to proper executable for chrome.
    """
    pltfm = platform.system()
    arch = platform.processor()

    if pltfm == "Darwin":
        if arch == "arm":
            return "../chrome/chrome-headless-shell-mac-arm64/chrome-headless-shell"
        return "../chrome/chrome-headless-shell-mac-x64/chrome-headless-shell"
    if pltfm == "Linux":
        return "../chrome/chrome-headless-shell-linux64/chrome-headless-shell"
    if pltfm == "Windows":
        return "../chrome/chrome-headless-shell-win64/chrome-headless-shell.exe"
    raise Exception("Unknown platform")


def download_website(url: str) -> bytes:
    """
    Downloads content of website page into bytes.

    Args:
        url (str): URL to website.

    Returns:
        Content of website as bytes.
    """
    first_exception: Optional[Exception] = None

    for url_attempt in [url, f"https://{url}", f"http://{url}"]:
        content, exception = try_download_url(url_attempt)
        if content:
            return content
        if exception and not first_exception:
            first_exception = exception

    if first_exception:
        raise first_exception

    raise Exception("Failed to download content from all URL attempts.")


def try_download_url(url: str) -> tuple[Optional[bytes], Optional[Exception]]:
    """
    Tries to download content from URL.

    Args:
        url (str): URL to website.

    Returns:
        Tuple of content as bytes or None, and exception if occurred.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raises HTTPError for 4xx or 5xx
    except requests.exceptions.HTTPError as e:
        return (None, e)
    except requests.exceptions.ConnectionError as e:
        return (None, e)
    except requests.exceptions.Timeout as e:
        return (None, e)
    except requests.exceptions.RequestException as e:
        return (None, e)
    if isinstance(response.content, bytes):
        return (response.content, None)
    return (None, None)


def convert_to_pdf(url: str, output: str) -> None:
    """
    Converts website to PDF document.

    Args:
        url (str): URL to website.
        output (str): Path to output PDF document.
    """
    try:
        if os.path.isfile(url):
            print("Reading local file...")
            with open(url, "rb") as file:
                web_content: bytes = file.read()
        else:
            print("Webpage starting downloading...")
            web_content = download_website(url)
            print("Webpage downloaded")
    except Exception as e:
        print(e, file=sys.stderr)
        raise FailedToDownloadException()

    dir_path = os.path.dirname(os.path.realpath(__file__))

    try:
        chrome_cli: str = setup_chrome_cli()
    except Exception:
        print("Chrome cli was not found.", file=sys.stderr)
        raise FailedToConvertException()

    chrome_cli = os.path.normpath(dir_path + "/" + chrome_cli)

    with tempfile.TemporaryDirectory() as tempdir:
        file_path: str = os.path.join(tempdir, str(uuid.uuid4()) + ".html")

        with open(file_path, "wb") as f:
            f.write(web_content)

        print("Webpage saved into container")

        try:
            name: str = output
            command = [
                chrome_cli,
                "--headless",
                f"--print-to-pdf={name}",
                "--disable-gpu",
                "--no-sandbox",
                file_path,
            ]
            full_command: str = " ".join(command)
            print(f"Executing chrome command: '{full_command}'")

            result: subprocess.CompletedProcess[str] = subprocess.run(
                command,
                shell=False,
                capture_output=True,
                text=True,
                check=False,
            )

            print(f"Command ended with code {result.returncode}")

            if result.returncode == 0:
                print("Command executed successfully")
            else:
                raise Exception(f"Error: {result.stderr}")
        except Exception:
            raise FailedToConvertException()
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
