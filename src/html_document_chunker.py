import logging
import re
from pathlib import Path
from typing import Optional

from constants import (
    DOCUMENT_PAGE_COUNT,
    HTML_SUFFIX,
    PAGE_SECTION_START,
    PDF_PAGE_CHUNK_SIZE,
)
from html_chunk_info import HtmlChunkInfo
from logger import get_logger


class HtmlDocumentChunker:
    """
    Splits large multi-page HTML documents into smaller files for low-memory printing.

    Page boundaries are detected from ``data-page-num`` markers on top-level page
    blocks (common in fixed-layout HTML exports). Documents without those markers
    are returned as a single chunk and printed with CDP page-range batching instead.
    """

    def __init__(self, chunk_size: int = PDF_PAGE_CHUNK_SIZE) -> None:
        """
        Args:
            chunk_size (int): Maximum HTML page sections per chunk file.
        """
        self._chunk_size: int = chunk_size
        self._logger: logging.Logger = get_logger(__name__)

    @staticmethod
    def is_page_section_start(line: str) -> bool:
        """
        Return whether ``line`` opens an HTML page section block.

        Args:
            line (str): A single line from an HTML file.

        Returns:
            bool: ``True`` when the line opens a page section block.
        """
        return PAGE_SECTION_START.search(line) is not None

    @staticmethod
    def page_number_from_line(line: str) -> int:
        """
        Extract the one-based page number from a page section opening line.

        Args:
            line (str): Line matched by :meth:`is_page_section_start`.

        Returns:
            int: Value of ``data-page-num``.
        """
        match: Optional[re.Match[str]] = PAGE_SECTION_START.search(line)
        if match is None:
            raise ValueError("Line is not a page section start marker")
        return int(match.group(1))

    def count_page_sections(self, html_path: Path) -> int:
        """
        Count HTML page sections by scanning ``data-page-num`` open tags.

        Args:
            html_path (Path): Path to the HTML file.

        Returns:
            int: Number of page section blocks, or 0 for continuous HTML.
        """
        count: int = 0
        with open(html_path, "r", encoding="utf-8", errors="replace") as html_file:
            for line in html_file:
                if self.is_page_section_start(line):
                    count += 1
        return count

    @staticmethod
    def write_chunk(
        chunk_dir: Path,
        chunk_index: int,
        total_chunks: int,
        prefix_lines: list[str],
        page_lines: list[list[str]],
        first_page: int,
        last_page: int,
    ) -> HtmlChunkInfo:
        """
        Write one chunk HTML file, updating ``data-num-pages`` when present.

        Args:
            chunk_dir (Path): Directory for chunk files.
            chunk_index (int): One-based chunk index.
            total_chunks (int): Total number of chunks in this split.
            prefix_lines (list[str]): Shared document prefix before page sections.
            page_lines (list[list[str]]): Lines for each page section in this chunk.
            first_page (int): First page number in the chunk.
            last_page (int): Last page number in the chunk.

        Returns:
            HtmlChunkInfo: Metadata for the written chunk.
        """
        section_count: int = len(page_lines)
        chunk_name: str = f"chunk-{chunk_index:04d}-pages-{first_page}-{last_page}.html"
        chunk_path: Path = chunk_dir.joinpath(chunk_name)

        with open(chunk_path, "w", encoding="utf-8", errors="replace") as chunk_file:
            for prefix_line in prefix_lines:
                line_to_write: str = prefix_line
                if "data-num-pages=" in prefix_line:
                    line_to_write = DOCUMENT_PAGE_COUNT.sub(
                        f'data-num-pages="{section_count}"',
                        prefix_line,
                    )
                chunk_file.write(line_to_write)
            for lines in page_lines:
                chunk_file.writelines(lines)
            chunk_file.write(HTML_SUFFIX)

        return HtmlChunkInfo(
            path=chunk_path,
            index=chunk_index,
            total=total_chunks,
            first_page=first_page,
            last_page=last_page,
            use_page_ranges=False,
        )

    def split(self, html_path: Path, chunk_dir: Path) -> list[HtmlChunkInfo]:
        """
        Prepare HTML chunks for printing.

        Continuous HTML (no page sections) is returned as one chunk that should
        be printed with CDP ``pageRanges``. Multi-section HTML is split into files
        of at most ``chunk_size`` sections when needed.

        Args:
            html_path (Path): Path to the source HTML file.
            chunk_dir (Path): Directory where chunk files are written.

        Returns:
            list[HtmlChunkInfo]: Chunk descriptors in document order.
        """
        section_count: int = self.count_page_sections(html_path)
        if section_count == 0:
            self._logger.debug("Continuous HTML; will print with page-range batching")
            return [
                HtmlChunkInfo(
                    path=html_path,
                    index=1,
                    total=1,
                    first_page=0,
                    last_page=0,
                    use_page_ranges=True,
                )
            ]

        if section_count <= self._chunk_size:
            self._logger.debug(
                "Found %s HTML page section(s); fits in one chunk (max %s)",
                section_count,
                self._chunk_size,
            )
            return [
                HtmlChunkInfo(
                    path=html_path,
                    index=1,
                    total=1,
                    first_page=1,
                    last_page=section_count,
                    use_page_ranges=False,
                )
            ]

        total_chunks: int = (section_count + self._chunk_size - 1) // self._chunk_size
        self._logger.debug(
            "Found %s HTML page section(s); splitting into %s file chunk(s) of up to %s pages",
            section_count,
            total_chunks,
            self._chunk_size,
        )

        prefix_lines: list[str] = []
        current_page_lines: list[str] = []
        current_page_num: int = 0
        pages_in_chunk: list[list[str]] = []
        page_numbers_in_chunk: list[int] = []
        chunk_paths: list[HtmlChunkInfo] = []
        chunk_index: int = 0

        def flush_chunk() -> None:
            nonlocal chunk_index, pages_in_chunk, page_numbers_in_chunk
            if not pages_in_chunk:
                return
            chunk_index += 1
            chunk_paths.append(
                self.write_chunk(
                    chunk_dir,
                    chunk_index,
                    total_chunks,
                    prefix_lines,
                    pages_in_chunk,
                    page_numbers_in_chunk[0],
                    page_numbers_in_chunk[-1],
                )
            )
            self._logger.debug(
                "Wrote file chunk %s/%s (pages %s-%s)",
                chunk_index,
                total_chunks,
                page_numbers_in_chunk[0],
                page_numbers_in_chunk[-1],
            )
            pages_in_chunk = []
            page_numbers_in_chunk = []

        with open(html_path, "r", encoding="utf-8", errors="replace") as html_file:
            for line in html_file:
                if not self.is_page_section_start(line):
                    if current_page_lines:
                        current_page_lines.append(line)
                    else:
                        prefix_lines.append(line)
                    continue

                page_num: int = self.page_number_from_line(line)
                if current_page_lines:
                    pages_in_chunk.append(current_page_lines)
                    page_numbers_in_chunk.append(current_page_num)
                    if len(pages_in_chunk) >= self._chunk_size:
                        flush_chunk()

                current_page_num = page_num
                current_page_lines = [line]

            if current_page_lines:
                pages_in_chunk.append(current_page_lines)
                page_numbers_in_chunk.append(current_page_num)
                flush_chunk()

        return chunk_paths
