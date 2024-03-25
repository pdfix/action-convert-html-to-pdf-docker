import argparse
import os
import platform
import random
import string
import subprocess
import sys

import requests
from tqdm import tqdm


def setup_chrome_cli() -> str:
    pltfm = platform.system()
    arch = platform.processor()

    # print(pltfm)
    # print(arch)
    if pltfm == "Darwin":
        if arch == "arm":
            return "chrome/chrome-headless-shell-mac-arm64/chrome-headless-shell"
        else:
            return "chrome/chrome-headless-shell-mac-x64/chrome-headless-shell"
    elif pltfm == "Linux":
        return "chrome/chrome-headless-shell-linux64/chrome-headless-shell"
    elif pltfm == "Windows":
        return "chrome/chrome-headless-shell-win64/chrome-headless-shell.exe"
    else:
        raise Exception("Unknown platform")


def download_website(url):
    response = requests.get(url, stream=True)
    website_content = response.content
    return website_content


def convert_to_pdf(url: str, output: str):
    web_content = download_website(url)

    dir_path = os.path.dirname(os.path.realpath(__file__))

    try:
        chrome_cli = setup_chrome_cli()
    except Exception as e:
        print("Chrome cli was not found.", file=sys.stderr)

    chrome_cli = os.path.normpath(dir_path + "/" + chrome_cli)

    out_dir = os.path.normpath(dir_path + "/" + os.path.dirname(output))
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    file_path = os.path.join(out_dir, "temp.html")

    with open(file_path, "wb") as f:
        f.write(web_content)

    if os.path.isabs(output):
        name = output
    else:
        name = os.path.join(out_dir, os.path.basename(output))

    args = [
        chrome_cli,
        "--headless",
        "--print-to-pdf=" + name,
        "--disable-gpu",
        "--no-sandbox",
        file_path,
    ]

    result = subprocess.run(args, shell=False, capture_output=True, text=True)

    if result.returncode == 0:
        print("Command executed successfully")
    else:
        print("Error:", result.stderr, file=sys.stderr)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="URL", required=True)
    parser.add_argument("--output", help="Output file", required=True)
    args = parser.parse_args()

    convert_to_pdf(args.url, args.output)


if __name__ == "__main__":
    main()
