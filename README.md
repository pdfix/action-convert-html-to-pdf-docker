# HTML to PDF

A Docker image that converts HTML pages to PDF files using headless Chromium.

## Table of Contents

- [HTML to PDF](#html-to-pdf)
  - [Getting started](#getting-started)
  - [Usage](#usage)
  - [Commands](#commands)
  - [Arguments](#arguments)
  - [How it works](#how-it-works)
  - [Exit codes](#exit-codes)
  - [Examples](#examples)
  - [Notes](#notes)
  - [Help \& support](#help--support)
  - [Licenses](#licenses)

## Getting started

You need Docker installed. The first run downloads the image and may take longer than later runs.

## Usage

Mount a folder into the container and run a subcommand:

```bash
docker run --rm -v "$(pwd)":/data -w /data pdfix/convert-html-to-pdf:latest <command> [options]
```

## Commands

- `html-to-pdf`: Convert HTML (local file or URL) to PDF

## Arguments

### `html-to-pdf`

| Option | Required | Type / expected value | Description |
|---|:---:|---|---|
| `--input`, `-i` | yes | URL (`https://…`) or path to an existing HTML file under the mounted volume | Page to convert |
| `--output`, `-o` | yes | Path for the output `.pdf` file | Output PDF |

## How it works

- Headless Chromium opens the HTML file or URL, waits until the page is loaded (at most 2 minutes, error 30) and prints it in one pass to a tagged PDF (A4 unless CSS `@page` says otherwise).
- Tags, document language and title come from the HTML (`lang`, `<title>`, `alt`); accessibility problems of the HTML stay in the PDF.
- **Checks before processing:** output extension (11) and folder (12), input file (13), then the conversion.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Unexpected error (`Failed to run the program:` + traceback) |
| 10 | Failed to parse arguments. Please check the usage and try again |
| 11 | Output file must be PDF document |
| 12 | Output folder does not exist |
| 13 | Input file does not exist |
| 30 | Failed to open webpage from URL |
| 31 | Failed to convert HTML to PDF |
| 32 | URL points to a PDF document, not to a webpage |

## Examples

Convert a local HTML file:

```bash
docker run --rm -v "$(pwd)":/data -w /data pdfix/convert-html-to-pdf:latest html-to-pdf -i /data/index.html -o /data/convert.pdf
```

Convert a URL:

```bash
docker run --rm -v "$(pwd)":/data -w /data pdfix/convert-html-to-pdf:latest html-to-pdf -i "https://example.com" -o /data/convert.pdf
```

## Notes

- The Docker image uses the open-source [Chromium](https://www.chromium.org/Home/) package from Debian stable.
- Output PDFs are tagged. Chromium builds the tag tree from the page's accessibility tree, so its quality depends on the semantic structure of the HTML.
- Pages are A4 unless the HTML sets its own page size with CSS `@page`.
- The whole document is printed in one pass to keep the tag tree, so very large HTML files need more container memory.

## Help & support

To report an issue, contact `support@pdfix.net`.

## Licenses

- [Chromium](https://www.chromium.org/Home/) (BSD-style license)

