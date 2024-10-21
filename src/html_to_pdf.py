import os
import platform
import subprocess
import sys
import tempfile
import uuid

import requests


def setup_chrome_cli() -> str:
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


def download_website(url: str):
    response = requests.get(url, stream=True)
    return response.content


def convert_to_pdf(url: str, output: str) -> None:
    if url.startswith("https://"):
        web_content = download_website(url)
    else:
        with open(url, "rb") as file:
            web_content = file.read()

    dir_path = os.path.dirname(os.path.realpath(__file__))

    try:
        chrome_cli = setup_chrome_cli()
    except Exception:
        print("Chrome cli was not found.", file=sys.stderr)

    chrome_cli = os.path.normpath(dir_path + "/" + chrome_cli)

    # out_dir = os.path.normpath(dir_path + "/" + os.path.dirname(output))
    tempfile.gettempdir()
    # if not os.path.exists(out_dir):
    #     os.makedirs(out_dir)

    # file_path = os.path.join(out_dir, "temp.html")
    file_path = tempfile.gettempdir() + str(uuid.uuid4()) + ".html"
    with open(file_path, "wb") as f:
        f.write(web_content)

    # if os.path.isabs(output):
    name = output
    # else:
    #     name = os.path.join(out_dir, os.path.basename(output))

    args = [
        chrome_cli,
        "--headless",
        "--print-to-pdf=" + name,
        "--disable-gpu",
        "--no-sandbox",
        file_path,
    ]

    result = subprocess.run(
        args,
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        print("Command executed successfully")
    else:
        print("Error:", result.stderr, file=sys.stderr)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
