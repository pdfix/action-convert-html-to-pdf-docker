EC_ARG_GENERAL: int = 10

EC_FAILED_TO_DOWNLOAD: int = 30
EC_CHROME_FAILED_TO_CONVERT: int = 31

MESSAGE_ARG_GENERAL: str = "Failed to parse arguments. Please check the usage and try again."

MESSAGE_FAILED_TO_DOWNLOAD: str = "Failed to find input file or download webpage from URL."
MESSAGE_CHROME_FAILED_TO_CONVERT: str = "Failed to convert HTML to PDF."


class ExpectedException(BaseException):
    """
    Base exception for expected failures surfaced to the user.

    Carries an application error code and a user-facing message printed to stderr.
    """

    def __init__(self, error_code: int) -> None:
        """
        Args:
            error_code (int): Exit code returned to the caller.
        """
        self.error_code: int = error_code
        self.message: str = ""

    def _add_note(self, note: str) -> None:
        """
        Set the user-facing error message.

        Args:
            note (str): Message shown to the user.
        """
        self.message = note


class ArgGeneralException(ExpectedException):
    """Raised when command-line arguments cannot be parsed."""

    def __init__(self) -> None:
        """Initialize with the argument parsing error code and message."""
        super().__init__(EC_ARG_GENERAL)
        self._add_note(MESSAGE_ARG_GENERAL)


class FailedToDownloadException(ExpectedException):
    """Raised when the input HTML file is missing or the webpage cannot be downloaded."""

    def __init__(self) -> None:
        """Initialize with the download error code and message."""
        super().__init__(EC_FAILED_TO_DOWNLOAD)
        self._add_note(MESSAGE_FAILED_TO_DOWNLOAD)


class FailedToConvertException(ExpectedException):
    """Raised when HTML cannot be converted to PDF."""

    def __init__(self) -> None:
        """Initialize with the conversion error code and message."""
        super().__init__(EC_CHROME_FAILED_TO_CONVERT)
        self._add_note(MESSAGE_CHROME_FAILED_TO_CONVERT)
