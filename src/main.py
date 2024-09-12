import argparse
import os
import json
import sys
import shutil
from pathlib import Path

from html_to_pdf import convert_to_pdf

def get_config(path) -> None:    
    if path is None:
        with open(os.path.join(Path(__file__).parent.absolute(), "../config.json"), 'r') as f:
            print(f.read())    
    else:
        src = os.path.join(Path(__file__).parent.absolute(), "../config.json")
        dst = path
        shutil.copyfile(src, dst)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, default="", help="license name")
    parser.add_argument("--key", type=str, default="", help="license key")

    subparsers = parser.add_subparsers(dest="subparser")

    # config subparser
    pars_config = subparsers.add_parser("config", help="Extract config file for integration")
    pars_config.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output to save the config JSON file. Application output is used if not provided",
    )    

    # html-to-pdf subparser
    pars_html = subparsers.add_parser("html-to-pdf", help="Convert HTML to PDF document.")
    pars_html.add_argument("--url", help="URL address or local path to HTML")
    pars_html.add_argument("-o", "--output", help="Output PDF file")
    pars_html.add_argument("--verbose", help="Print debug info", action="store_true")
    pars_html.add_argument("-v", "--version", help="Print version", action="store_true")
    args = parser.parse_args()

    if args.subparser == "config":
        get_config(args.output)
        sys.exit(0)

    elif args.subparser == "html-to-pdf":    
        if args.version:
            try:
                config_path = "config.json"
                with open(config_path, "r") as f:
                    data = json.load(f)

                    if "version" in data:
                        version_info = data["version"]
                        MAJOR = version_info.get("major")
                        MINOR = version_info.get("minor")
                        PATCH = version_info.get("patch")

                    print("Version: {}.{}.{}".format(MAJOR, MINOR, PATCH))
                sys.exit(0)
            except FileNotFoundError as err:
                print(
                    "Failed to get version information. Missing {} file.".format(
                        config_path
                    ),
                    file=sys.stderr,
                )
                sys.exit(1)

        if args.verbose:
            print("Running in verbose mode. Debug messages enabled.")

        if args.url is None:
            print("Missing required argument --url")
            sys.exit(1)
        if args.output is None:
            print("Missing required argument --output")
            sys.exit(1)

        convert_to_pdf(args.url, args.output)


if __name__ == "__main__":
    main()
