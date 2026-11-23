EC_ARG_GENERAL: int = 10
EC_ARG_OUTPUT_PDF: int = 11
EC_ARG_OUTPUT_FOLDER_NOT_EXISTS: int = 12
EC_ARG_INPUT_FILE_NOT_EXISTS: int = 13

EC_FAILED_TO_OPEN_WEBPAGE: int = 30
EC_CHROME_FAILED_TO_CONVERT: int = 31
EC_URL_NOT_WEBPAGE: int = 32

MESSAGE_ARG_GENERAL: str = "Failed to parse arguments. Please check the usage and try again."
MESSAGE_ARG_OUTPUT_PDF: str = "Output file must be PDF document."
MESSAGE_ARG_OUTPUT_FOLDER_NOT_EXISTS: str = "Output folder does not exist."
MESSAGE_ARG_INPUT_FILE_NOT_EXISTS: str = "Input file does not exist."

MESSAGE_FAILED_TO_OPEN_WEBPAGE: str = "Failed to open webpage from URL."
MESSAGE_CHROME_FAILED_TO_CONVERT: str = "Failed to convert HTML to PDF."
MESSAGE_URL_NOT_WEBPAGE: str = "URL points to a PDF document, not to a webpage."


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


class ArgumentOutputPdfException(ExpectedException):
    """Raised when the output file is not a PDF document."""

    def __init__(self) -> None:
        """Initialize with the output extension error code and message."""
        super().__init__(EC_ARG_OUTPUT_PDF)
        self._add_note(MESSAGE_ARG_OUTPUT_PDF)


class ArgumentOutputFolderNotExistsException(ExpectedException):
    """Raised when the folder of the output file does not exist."""

    def __init__(self, path: str) -> None:
        """
        Args:
            path (str): Missing output folder.
        """
        super().__init__(EC_ARG_OUTPUT_FOLDER_NOT_EXISTS)
        self._add_note(f"{MESSAGE_ARG_OUTPUT_FOLDER_NOT_EXISTS} {path}")


class ArgumentInputFileNotExistsException(ExpectedException):
    """Raised when the input is a path of a file that does not exist."""

    def __init__(self, path: str) -> None:
        """
        Args:
            path (str): Missing input file.
        """
        super().__init__(EC_ARG_INPUT_FILE_NOT_EXISTS)
        self._add_note(f"{MESSAGE_ARG_INPUT_FILE_NOT_EXISTS} {path}")


class FailedToOpenWebpageException(ExpectedException):
    """Raised when the webpage cannot be opened."""

    def __init__(self) -> None:
        """Initialize with the webpage error code and message."""
        super().__init__(EC_FAILED_TO_OPEN_WEBPAGE)
        self._add_note(MESSAGE_FAILED_TO_OPEN_WEBPAGE)


class FailedToConvertException(ExpectedException):
    """Raised when HTML cannot be converted to PDF."""

    def __init__(self) -> None:
        """Initialize with the conversion error code and message."""
        super().__init__(EC_CHROME_FAILED_TO_CONVERT)
        self._add_note(MESSAGE_CHROME_FAILED_TO_CONVERT)


class UrlNotWebpageException(ExpectedException):
    """Raised when the URL opens a PDF document instead of a webpage."""

    def __init__(self) -> None:
        """Initialize with the not a webpage error code and message."""
        super().__init__(EC_URL_NOT_WEBPAGE)
        self._add_note(MESSAGE_URL_NOT_WEBPAGE)
