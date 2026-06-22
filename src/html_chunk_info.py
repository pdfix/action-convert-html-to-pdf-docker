from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HtmlChunkInfo:
    """Metadata for one HTML chunk passed to the PDF printer."""

    path: Path
    index: int
    total: int
    first_page: int
    last_page: int
    use_page_ranges: bool
