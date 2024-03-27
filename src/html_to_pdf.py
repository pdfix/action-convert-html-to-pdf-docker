import argparse
import os
import platform
import subprocess
import sys

import requests

DEBUG = False


def setup_chrome_cli() -> str:
    pltfm = platform.system()
    arch = platform.processor()

    if DEBUG:
        print("Platform: {}".format(pltfm))
        print("Architecture: {}".format(arch))

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
    if url.startswith("https://"):
        if DEBUG:
            print("Downloading html from url: {}".format(url))

        web_content = download_website(url)
    else:
        if DEBUG:
            print("Using local html from path: {}".format(url))

        with open(url, "rb") as file:
            web_content = file.read()

    dir_path = os.path.dirname(os.path.realpath(__file__))

    try:
        chrome_cli = setup_chrome_cli()
    except Exception as e:
        print("Chrome cli was not found.", file=sys.stderr)

    chrome_cli = os.path.normpath(dir_path + "/" + chrome_cli)

    if DEBUG:
        print("Path to chrome CLI: {}".format(chrome_cli))

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

    if DEBUG:
        print("Running chrome cli with args: {}".format(" ".join(args)))

    result = subprocess.run(args, shell=False, capture_output=True, text=True)

    if result.returncode == 0:
        if DEBUG:
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
    parser.add_argument(
        "--url", help="URL address or local path to HTML", required=True
    )
    parser.add_argument("--output", help="Output file", required=True)
    parser.add_argument(
        "--verbose", help="Print debug info", required=False, action="store_true"
    )
    args = parser.parse_args()

    if args.verbose:
        print("Running in verbose mode. Debug messages enabled.")
        global DEBUG
        DEBUG = True

    convert_to_pdf(args.url, args.output)


if __name__ == "__main__":
    main()
