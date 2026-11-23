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

from cdp_session import CdpSession
from constants import (
    CDP_IO_READ_SIZE,
    CHROMIUM_EXECUTABLE,
    PAGE_HEIGHT_A4_INCHES,
    PAGE_WIDTH_A4_INCHES,
)
from exceptions import FailedToDownloadException, UrlNotWebpageException
from logger import get_logger


class ChromiumPdfPrinter:
    """
    Renders an HTML document or webpage to a tagged PDF using headless Chromium.

    The whole document is printed in one pass, so the PDF keeps the tag tree generated
    by Chromium.
    """

    def __init__(self) -> None:
        """Creates the printer logger."""
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
    def wait_for_devtools(port: int, process: subprocess.Popen[str]) -> None:
        """
        Poll Chromium until its DevTools HTTP endpoint responds.

        Args:
            port (int): Remote debugging port Chromium was started with.
            process (subprocess.Popen[str]): Running Chromium process.

        Raises:
            RuntimeError: If Chromium exits before DevTools is available.
        """
        while process.poll() is None:
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
        raise RuntimeError(f"Chromium exited with return code {process.returncode} before DevTools was available")

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
        )

    def open_page(self, session: CdpSession, page_url: str) -> None:
        """
        Open the page in Chromium and check that it is a webpage that can be printed.

        Chromium loads the page itself, so CSS, images and scripts linked from the page are loaded too.

        Args:
            session (CdpSession): Active CDP session for the page target.
            page_url (str): URL of the webpage or file URI of the HTML document.

        Raises:
            FailedToDownloadException: If the page cannot be opened or the server returns an error status.
            UrlNotWebpageException: If the URL opens a PDF document.
        """
        navigation: dict[str, Any] = session.call("Page.navigate", {"url": page_url})
        if navigation.get("errorText"):
            self._logger.error(f"Failed to open '{page_url}': {navigation['errorText']}")
            raise FailedToDownloadException()

        self.wait_for_page_ready(session)

        evaluation: dict[str, Any] = session.call(
            "Runtime.evaluate",
            {
                "expression": """
                    ({
                        contentType: document.contentType,
                        status: performance.getEntriesByType('navigation')[0]?.responseStatus ?? 0,
                    })
                """,
                "returnByValue": True,
            },
        )
        page_info: dict[str, Any] = evaluation.get("result", {}).get("value", {})
        status: int = int(page_info.get("status", 0))
        if status >= 400:
            self._logger.error(f"Failed to open '{page_url}': HTTP status {status}")
            raise FailedToDownloadException()
        if page_info.get("contentType") == "application/pdf":
            raise UrlNotWebpageException()

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
    ) -> None:
        """
        Print the loaded document to a PDF file.

        Args:
            session (CdpSession): Active CDP session for the page target.
            destination (Path): Path to write the PDF data.
        """
        params: dict[str, Any] = {
            "printBackground": True,
            "paperWidth": PAGE_WIDTH_A4_INCHES,
            "paperHeight": PAGE_HEIGHT_A4_INCHES,
            "preferCSSPageSize": True,
            "generateTaggedPDF": True,
            "transferMode": "ReturnAsStream",
        }

        result: dict[str, Any] = session.call(
            "Page.printToPDF",
            params,
        )
        ChromiumPdfPrinter.write_pdf_stream(session, result["stream"], destination)

    def print_html_to_pdf(
        self,
        page_url: str,
        output_path: Path,
        progress_bar: tqdm.tqdm,
    ) -> None:
        """
        Render an HTML document or webpage to a PDF file using headless Chromium.

        Args:
            page_url (str): URL of the webpage or file URI of the HTML document to print.
            output_path (Path): Path to write the final PDF.
            progress_bar (tqdm.tqdm): Progress bar to update.
        """
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

        try:
            self.wait_for_devtools(port, process)
            session: CdpSession = CdpSession(self.create_page_target(port))
            try:
                self.open_page(session, page_url)
                progress_bar.set_description("Printing PDF")
                self._logger.debug("Printing PDF")
                self.print_to_pdf(session, output_path)
                self._logger.debug("PDF printed successfully")

            finally:
                session.close()
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            if user_data_dir.is_dir():
                shutil.rmtree(user_data_dir, ignore_errors=True)

            if process.returncode not in (0, None, -15):
                stderr: str = process.stderr.read() if process.stderr else ""
                if stderr:
                    self._logger.error(stderr)
