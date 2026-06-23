import base64
import logging
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import requests
import tqdm
from pypdf import PdfWriter

from cdp_session import CdpSession
from constants import (
    CDP_IO_READ_SIZE,
    CHROMIUM_DEVTOOLS_TIMEOUT,
    CHROMIUM_EXECUTABLE,
    CHROMIUM_PAGE_READY_TIMEOUT,
    CHROMIUM_PRINT_TIMEOUT,
    PAGE_RANGE_EXCEEDED_MESSAGE,
    PDF_PAGE_CHUNK_SIZE,
)
from html_chunk_info import HtmlChunkInfo
from html_document_chunker import HtmlDocumentChunker
from logger import get_logger


class ChromiumPdfPrinter:
    """
    Renders an HTML document or webpage to PDF using headless Chromium.

    Large multi-section HTML is split into file chunks first. Continuous HTML
    uses CDP page-range batching on a single loaded document.
    """

    def __init__(
        self,
        page_chunk_size: int = PDF_PAGE_CHUNK_SIZE,
        chunker: HtmlDocumentChunker | None = None,
    ) -> None:
        """
        Args:
            page_chunk_size (int): Maximum PDF pages printed per batch or file chunk.
            chunker (HtmlDocumentChunker | None): HTML splitter for multi-section documents.
        """
        self._page_chunk_size: int = page_chunk_size
        self._chunker: HtmlDocumentChunker = chunker or HtmlDocumentChunker(page_chunk_size)
        self._logger: logging.Logger = get_logger(__name__)

    @staticmethod
    def pick_free_port() -> int:
        """
        Bind to an ephemeral port on localhost and return its number.

        Returns:
            int: A free TCP port on ``127.0.0.1``.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]

    @staticmethod
    def wait_for_devtools(port: int, timeout: float = CHROMIUM_DEVTOOLS_TIMEOUT) -> None:
        """
        Poll Chromium until its DevTools HTTP endpoint responds.

        Args:
            port (int): Remote debugging port Chromium was started with.
            timeout (float): Maximum seconds to wait.

        Raises:
            TimeoutError: If DevTools is not available before ``timeout``.
        """
        deadline: float = time.time() + timeout
        while time.time() < deadline:
            try:
                response: requests.Response = requests.get(
                    f"http://127.0.0.1:{port}/json/version",
                    timeout=1,
                )
                if response.ok:
                    return
            except requests.RequestException:
                pass
            time.sleep(0.2)
        raise TimeoutError("Chromium did not expose DevTools in time")

    @staticmethod
    def create_page_target(port: int) -> str:
        """
        Open a blank page target and return its WebSocket debugger URL.

        Args:
            port (int): Remote debugging port Chromium was started with.

        Returns:
            str: WebSocket URL for the new DevTools target.
        """
        response: requests.Response = requests.put(
            f"http://127.0.0.1:{port}/json/new?about:blank",
            timeout=5,
        )
        response.raise_for_status()
        return response.json()["webSocketDebuggerUrl"]

    @staticmethod
    def wait_for_page_ready(session: CdpSession) -> None:
        """
        Wait until the loaded page is ready for PDF printing.

        Args:
            session (CdpSession): Active CDP session for the page target.
        """
        session.call("Page.enable")
        session.call(
            "Runtime.evaluate",
            {
                "expression": """
                    new Promise((resolve) => {
                        const done = () => {
                            requestAnimationFrame(() => requestAnimationFrame(resolve));
                        };
                        if (document.readyState === 'complete') {
                            done();
                        } else {
                            window.addEventListener('load', done, { once: true });
                        }
                    })
                """,
                "awaitPromise": True,
            },
            timeout=CHROMIUM_PAGE_READY_TIMEOUT,
        )

    @staticmethod
    def write_pdf_stream(session: CdpSession, stream_handle: str, destination: Path) -> None:
        """
        Read a CDP IO stream and write its contents to a PDF file.

        Args:
            session (CdpSession): Active CDP session for the page target.
            stream_handle (str): Handle returned by ``Page.printToPDF``.
            destination (Path): Path to write the PDF data.
        """
        with open(destination, "wb") as pdf_file:
            while True:
                chunk: dict[str, Any] = session.call(
                    "IO.read",
                    {"handle": stream_handle, "size": CDP_IO_READ_SIZE},
                )
                data: str = chunk["data"]
                if chunk.get("base64Encoded"):
                    pdf_file.write(base64.b64decode(data))
                else:
                    pdf_file.write(data.encode("latin-1"))
                if chunk.get("eof"):
                    break
        session.call("IO.close", {"handle": stream_handle})

    @staticmethod
    def print_to_pdf(
        session: CdpSession,
        destination: Path,
        page_ranges: str | None = None,
    ) -> None:
        """
        Print the loaded document, or a page range, to a PDF file.

        Args:
            session (CdpSession): Active CDP session for the page target.
            destination (Path): Path to write the PDF data.
            page_ranges (str | None): One-based page range string, for example ``"1-15"``.
        """
        params: dict[str, Any] = {
            "printBackground": True,
            "preferCSSPageSize": True,
            "transferMode": "ReturnAsStream",
        }
        if page_ranges is not None:
            params["pageRanges"] = page_ranges

        result: dict[str, Any] = session.call(
            "Page.printToPDF",
            params,
            timeout=CHROMIUM_PRINT_TIMEOUT,
        )
        ChromiumPdfPrinter.write_pdf_stream(session, result["stream"], destination)

    @staticmethod
    def merge_pdf_parts(part_paths: list[Path], output_path: Path) -> None:
        """
        Merge multiple PDF files into a single output document.

        Args:
            part_paths (list[Path]): Paths to PDF parts in merge order.
            output_path (Path): Path to write the merged PDF.
        """
        writer: PdfWriter = PdfWriter()
        for part_path in part_paths:
            writer.append(part_path)
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

    @staticmethod
    def is_page_range_exceeded(error: BaseException) -> bool:
        """
        Return whether a CDP error means the requested page range is past the document end.

        Args:
            error (BaseException): Exception raised by :class:`CdpSession`.

        Returns:
            bool: ``True`` when no further batches should be printed.
        """
        if not isinstance(error, RuntimeError) or not error.args:
            return False
        cdp_error: Any = error.args[0]
        if not isinstance(cdp_error, dict):
            return False
        return cdp_error.get("message") == PAGE_RANGE_EXCEEDED_MESSAGE

    @staticmethod
    def chunk_progress_message(chunk_info: HtmlChunkInfo) -> str:
        """
        Build the progress log line for one file chunk print step.

        Args:
            chunk_info (HtmlChunkInfo): Chunk being printed.

        Returns:
            str: Message for progress logging.
        """
        if chunk_info.first_page > 0:
            return (
                f"Printing chunk {chunk_info.index}/{chunk_info.total} "
                f"(pages {chunk_info.first_page}-{chunk_info.last_page})"
            )
        return f"Printing chunk {chunk_info.index}/{chunk_info.total}"

    def print_page_range_batches(
        self,
        session: CdpSession,
        part_dir: Path,
        part_index_offset: int = 0,
    ) -> list[Path]:
        """
        Print the loaded document in PDF page-range batches.

        Used for continuous HTML/webpages where the full document stays in one tab.

        Args:
            session (CdpSession): Active CDP session with the document loaded.
            part_dir (Path): Directory for temporary PDF part files.
            part_index_offset (int): Starting index for part file names.

        Returns:
            list[Path]: Paths to PDF parts in print order.

        Raises:
            RuntimeError: If the first batch cannot be printed.
        """
        part_paths: list[Path] = []
        start_page: int = 1
        batch_index: int = 0

        while True:
            end_page: int = start_page + self._page_chunk_size - 1
            page_ranges: str = f"{start_page}-{end_page}"
            batch_index += 1
            part_path: Path = part_dir.joinpath(f"part-{part_index_offset + batch_index:04d}.pdf")

            try:
                self.print_to_pdf(session, part_path, page_ranges)
            except RuntimeError as error:
                if part_paths and self.is_page_range_exceeded(error):
                    break
                raise

            part_paths.append(part_path)
            start_page = end_page + 1

        return part_paths

    def print_html_to_pdf(
        self,
        html_path: Path,
        output_path: Path,
        progress_bar: tqdm.tqdm,
    ) -> None:
        """
        Render an HTML document or webpage to a PDF file using headless Chromium.

        Args:
            html_path (Path): Path to the HTML document to print.
            output_path (Path): Path to write the final PDF.
            progress_bar (tqdm.tqdm): Progress bar to update.
        """
        chunk_dir: Path = Path(tempfile.mkdtemp(prefix="html-chunks-"))
        part_dir: Path = Path(tempfile.mkdtemp(prefix="pdf-parts-"))
        resolved_html_path: Path = html_path.resolve()
        chunk_infos: list[HtmlChunkInfo] = self._chunker.split(resolved_html_path, chunk_dir)

        port: int = self.pick_free_port()
        user_data_dir: Path = Path(tempfile.mkdtemp(prefix="chromium-profile-"))
        process: subprocess.Popen[str] = subprocess.Popen(
            [
                CHROMIUM_EXECUTABLE,
                "--headless",
                f"--remote-debugging-port={port}",
                "--remote-allow-origins=*",
                f"--user-data-dir={user_data_dir}",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        part_paths: list[Path] = []
        created_chunk_paths: set[Path] = {
            chunk.path for chunk in chunk_infos if chunk.path.resolve() != resolved_html_path
        }

        try:
            self.wait_for_devtools(port)
            session: CdpSession = CdpSession(self.create_page_target(port))
            try:
                part_index_offset: int = 0
                progress_bar_step: float = 50 / len(chunk_infos)
                for chunk_info in chunk_infos:
                    html_uri: str = chunk_info.path.resolve().as_uri()
                    session.call("Page.navigate", {"url": html_uri})
                    self.wait_for_page_ready(session)

                    chunk_parts: list[Path]
                    if chunk_info.use_page_ranges:
                        chunk_parts = self.print_page_range_batches(
                            session,
                            part_dir,
                            part_index_offset=part_index_offset,
                        )
                    else:
                        progress_bar.set_description(self.chunk_progress_message(chunk_info))
                        progress_bar.update(progress_bar_step)
                        self._logger.debug(self.chunk_progress_message(chunk_info))
                        part_path: Path = part_dir.joinpath(
                            f"part-{part_index_offset + 1:04d}.pdf",
                        )
                        self.print_to_pdf(session, part_path)
                        chunk_parts = [part_path]

                    part_paths.extend(chunk_parts)
                    part_index_offset += len(chunk_parts)

                self._logger.debug("Merging %s PDF part(s)", len(part_paths))
                self.merge_pdf_parts(part_paths, output_path)
                self._logger.debug("PDF parts merged successfully")
            finally:
                session.close()
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            for part_path in part_paths:
                if part_path.exists():
                    part_path.unlink()
            if part_dir.is_dir():
                shutil.rmtree(part_dir, ignore_errors=True)
            for chunk_path in created_chunk_paths:
                if chunk_path.is_file():
                    chunk_path.unlink()
            if chunk_dir.is_dir():
                shutil.rmtree(chunk_dir, ignore_errors=True)
            if user_data_dir.is_dir():
                shutil.rmtree(user_data_dir, ignore_errors=True)

            if process.returncode not in (0, None, -15):
                stderr: str = process.stderr.read() if process.stderr else ""
                if stderr:
                    self._logger.error(stderr)
