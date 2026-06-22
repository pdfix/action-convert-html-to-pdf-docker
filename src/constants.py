import re

CONFIG_FILE: str = "config.json"
DOCKER_NAMESPACE: str = "pdfix"
DOCKER_REPOSITORY: str = "convert-html-to-pdf"
DOCKER_IMAGE: str = f"{DOCKER_NAMESPACE}/{DOCKER_REPOSITORY}"

CHROMIUM_EXECUTABLE: str = "/usr/bin/chromium"
PDF_PAGE_CHUNK_SIZE: int = 15
CDP_IO_READ_SIZE: int = 65536

CHROMIUM_DEVTOOLS_TIMEOUT: float = 30
CHROMIUM_PAGE_READY_TIMEOUT: float = 120
CHROMIUM_PRINT_TIMEOUT: float = 600

HTTP_REQUEST_TIMEOUT: float = 60
DOWNLOAD_STREAM_CHUNK_SIZE: int = 1024 * 1024

PAGE_RANGE_EXCEEDED_MESSAGE: str = "Page range exceeds page count"

HTML_SUFFIX: str = "</body>\n</html>\n"

# Fixed-layout HTML exports often mark each page block with data-page-num.
PAGE_SECTION_START: re.Pattern[str] = re.compile(
    r'<div\b[^>]*\bdata-page-num="(\d+)"[^>]*>',
)
DOCUMENT_PAGE_COUNT: re.Pattern[str] = re.compile(r'data-num-pages="\d+"')
