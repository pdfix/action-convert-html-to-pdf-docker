# HTML to PDF

A Docker image action that converts HTML pages to PDF files using PDFix SDK and Google Headless Chrome.

## Table of Contents

- [HTML to PDF](#html-to-pdf)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
  - [Run using Command Line Interface](#run-using-command-line-interface)
  - [Exporting Configuration for Integration](#exporting-configuration-for-integration)
  - [License \& libraries used](#license--libraries-used)
  - [Help \& Support](#help--support)

## Getting Started

To use this Docker application, you'll need to have Docker installed on your system. If Docker is not installed, please follow the instructions on the [official Docker website](https://docs.docker.com/get-docker/) to install it.

## Run using Command Line Interface

To run docker container as CLI you should share the folder with html file to process using `-v` parameter. In this example it's current folder. The url can be local html file or URL address.

```bash
docker run -v $(pwd):/data/ -w /data/ pdfix/html-to-pdf:latest html-to-pdf -i index.html -o convert.pdf
```

First run will pull the docker image, which may take some time. Make your own image for more advanced use.

For more detailed information about the available command-line arguments, you can run the following command:

```bash
docker run --rm pdfix/html-to-pdf:latest --help
```

## Exporting Configuration for Integration

To export the configuration JSON file, use the following command:

```bash
docker run -v $(pwd):/data -w /data --rm pdfix/html-to-pdf:latest config -o config.json
```

## License & libraries used

- Chromium - https://www.chromium.org/Home/

## Help & Support

To obtain a PDFix SDK license or report an issue please contact us at support@pdfix.net.
For more information visit https://pdfix.net
