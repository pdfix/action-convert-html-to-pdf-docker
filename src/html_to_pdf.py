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

    if pltfm == "Windows":
        windows_exe = "../chrome/chrome-headless-shell-win64/chrome-headless-shell.exe"
        return windows_exe

    if pltfm == "Linux" or pltfm == "Darwin":
        # On minimal docker images this returns empty string
        # arch = platform.processor()

        arch = subprocess.check_output(["uname", "-m"], text=True).strip()
        uname_arch_mac_arm64 = "aarch64"
        linux_x64 = "../chrome/chrome-headless-shell-linux64/chrome-headless-shell"
        mac_arm64 = "../chrome/chrome-headless-shell-mac-arm64/chrome-headless-shell"

        chrome_path = mac_arm64 if arch == uname_arch_mac_arm64 else linux_x64
        return chrome_path

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
