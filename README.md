# HTML to PDF

A Docker image that converts HTML pages to PDF files using headless Chrome.

## Table of Contents

- [HTML to PDF](#html-to-pdf)
  - [Getting started](#getting-started)
  - [Usage](#usage)
  - [Commands](#commands)
  - [Arguments](#arguments)
  - [Examples](#examples)
  - [Notes](#notes)
  - [Help \& support](#help--support)
  - [Licenses](#licenses)

## Getting started

You need Docker installed. The first run downloads the image and may take longer than later runs.

## Usage

Mount a folder into the container and run a subcommand:

```bash
docker run --rm -v "$(pwd)":/data -w /data pdfix/html-to-pdf:latest <command> [options]
```

## Commands

- `html-to-pdf`: Convert HTML (local file or URL) to PDF

## Arguments

### `html-to-pdf`

| Option | Required | Type / expected value | Description |
|---|:---:|---|---|
| `--input`, `-i` | yes | URL (`https://…`) or path to an existing HTML file under the mounted volume | Page to convert |
| `--output`, `-o` | yes | Path for the output `.pdf` file | Output PDF |
| `--version`, `-v` | no | Flag (no value); prints version and exits | Print version |

## Examples

Convert a local HTML file:

```bash
docker run --rm -v "$(pwd)":/data -w /data pdfix/html-to-pdf:latest html-to-pdf -i /data/index.html -o /data/convert.pdf
```

Convert a URL:

```bash
docker run --rm -v "$(pwd)":/data -w /data pdfix/html-to-pdf:latest html-to-pdf -i "https://example.com" -o /data/convert.pdf
```

## Notes

- Chrome builds follow “Chrome for Testing”.

## Help & support

To report an issue, contact `support@pdfix.net`.

## Licenses

- [Chromium](https://www.chromium.org/Home/)
- [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/)
