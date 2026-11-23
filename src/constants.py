CONFIG_FILE: str = "config.json"
DOCKER_NAMESPACE: str = "pdfix"
DOCKER_REPOSITORY: str = "convert-html-to-pdf"
DOCKER_IMAGE: str = f"{DOCKER_NAMESPACE}/{DOCKER_REPOSITORY}"

CHROMIUM_EXECUTABLE: str = "/usr/bin/chromium"
CDP_IO_READ_SIZE: int = 65536
# Default page size A4 (210 x 297 mm) in inches, CSS @page size of the HTML has priority
PAGE_WIDTH_A4_INCHES: float = 210 / 25.4
PAGE_HEIGHT_A4_INCHES: float = 297 / 25.4
