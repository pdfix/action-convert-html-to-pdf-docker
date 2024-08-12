import argparse
import json
import sys


from html_to_pdf import convert_to_pdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="URL address or local path to HTML")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument("--verbose", help="Print debug info", action="store_true")
    parser.add_argument("-v", "--version", help="Print version", action="store_true")
    args = parser.parse_args()

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
