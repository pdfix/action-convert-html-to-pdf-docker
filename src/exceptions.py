EC_ARG_GENERAL = 10

EC_FAILED_TO_DOWNLOAD = 30
EC_CHROME_FAILED_TO_CONVERT = 31

MESSAGE_ARG_GENERAL = "Failed to parse arguments. Please check the usage and try again."

MESSAGE_FAILED_TO_DOWNLOAD = "Failed to find input file or download webpage from URL."
MESSAGE_CHROME_FAILED_TO_CONVERT = "Failed to convert HTML to PDF."


class ExpectedException(BaseException):
    def __init__(self, error_code: int) -> None:
        self.error_code: int = error_code
        self.message: str = ""

    def _add_note(self, note: str) -> None:
        self.message = note


class FailedToDownloadException(ExpectedException):
    def __init__(self) -> None:
        super().__init__(EC_FAILED_TO_DOWNLOAD)
        self._add_note(MESSAGE_FAILED_TO_DOWNLOAD)


class FailedToConvertException(ExpectedException):
    def __init__(self) -> None:
        super().__init__(EC_CHROME_FAILED_TO_CONVERT)
        self._add_note(MESSAGE_CHROME_FAILED_TO_CONVERT)
