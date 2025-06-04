import os
import platform
import subprocess
import tempfile
import uuid
from typing import Any

import requests


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


def download_website(url: str) -> bytes | Any:
    """
    Downloads content of website page into bytes.

    Args:
        url (str): URL to website.

    Returns:
        Content of website as bytes.
    """
    response = requests.get(url, stream=True)
    return response.content


def convert_to_pdf(url: str, output: str) -> None:
    """
    Converts website to PDF document.

    Args:
        url (str): URL to website.
        output (str): Path to output PDF document.
    """
    if url.startswith("https://"):
        web_content = download_website(url)
    else:
        with open(url, "rb") as file:
            web_content = file.read()

    dir_path = os.path.dirname(os.path.realpath(__file__))

    try:
        chrome_cli = setup_chrome_cli()
    except Exception:
        raise Exception("Chrome cli was not found.")

    chrome_cli = os.path.normpath(dir_path + "/" + chrome_cli)

    with tempfile.TemporaryDirectory() as tempdir:
        file_path = os.path.join(tempdir, str(uuid.uuid4()) + ".html")

        with open(file_path, "wb") as f:
            f.write(web_content)

        try:
            name = output
            command = [
                chrome_cli,
                "--headless",
                "--print-to-pdf=" + name,
                "--disable-gpu",
                "--no-sandbox",
                file_path,
            ]

            result = subprocess.run(
                command,
                shell=False,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                print("Command executed successfully")
            else:
                raise Exception(f"Error: {result.stderr}")
        except Exception:
            raise
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
