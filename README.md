# HTML to PDF/UA conversion

HTML to PDF/UA conversion with Google Chrome Headless and PDFix SDK

## Table of Contents

- [HTML to PDF/UA conversion](#html-to-pdfua-conversion)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
  - [Run using Command Line Interface](#run-using-command-line-interface)
  - [Run OCR using REST API](#run-ocr-using-rest-api)
    - [Exporting Configuration for Integration](#exporting-configuration-for-integration)
  - [License \& libraries used](#license--libraries-used)
  - [Help \& Support](#help--support)

## Getting Started

To use this Docker application, you'll need to have Docker installed on your system. If Docker is not installed, please follow the instructions on the [official Docker website](https://docs.docker.com/get-docker/) to install it.



## Run using Command Line Interface

To run docker container as CLI you should share the folder with html file to process using `--url` parameter. In this example it's current folder. The url can be local html file or URL address.

```bash
docker run -v $(pwd):/data/ -w /data/ pdfix/html-to-pdf:latest html-to-pdf --url index.html -o convert.pdf
```

With PDFix License add these arguments. 
```bash
--name ${LICENSE_NAME} --key ${LICENSE_KEY}
```

First run will pull the docker image, which may take some time. Make your own image for more advanced use.

For more detailed information about the available command-line arguments, you can run the following command:

```bash
docker run --rm pdfix/html-to-pdf:latest --help
```

## Run OCR using REST API
Comming soon. Please contact us.

### Exporting Configuration for Integration
To export the configuration JSON file, use the following command:
```bash
docker run -v $(pwd):/data -w /data --rm pdfix/html-to-pdf:latest config -o config.json
```

## License & libraries used
- PDFix SDK - https://pdfix.net/terms
- Chromium - https://www.chromium.org/Home/

Trial version of the PDFix SDK may apply a watermark on the page and redact random parts of the PDF. Contact us to get an evaluation or production license.

## Help & Support
To obtain a PDFix SDK license or report an issue please contact us at support@pdfix.net.
For more information visit https://pdfix.net

