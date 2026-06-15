import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import requests
from pypdf import PdfWriter
from tqdm import tqdm
from websocket import WebSocketTimeoutException, create_connection

from exceptions import FailedToConvertException, FailedToDownloadException

CHROMIUM_EXECUTABLE = "/usr/bin/chromium"
PDF_PAGE_BATCH_SIZE = 25
CDP_IO_READ_SIZE = 65536


def download_website_to_file(url: str, destination: str) -> None:
    """
    Downloads content of website page to a file without loading it into memory.

    Args:
        url (str): URL to website.
        destination (str): Path to write downloaded HTML.
    """
    first_exception: Optional[Exception] = None

    for url_attempt in [url, f"https://{url}", f"http://{url}"]:
        exception = try_download_url_to_file(url_attempt, destination)
        if exception is None:
            return
        if not first_exception:
            first_exception = exception

    if first_exception:
        raise first_exception

    raise Exception("Failed to download content from all URL attempts.")


def try_download_url_to_file(url: str, destination: str) -> Optional[Exception]:
    """
    Tries to download content from URL into a file.

    Args:
        url (str): URL to website.
        destination (str): Path to write downloaded HTML.

    Returns:
        None on success, or the exception that occurred.
    """
    try:
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with open(destination, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)
    except requests.exceptions.HTTPError as e:
        print(f"For '{url}' I got HTTPError")
        return e
    except requests.exceptions.ConnectionError as e:
        print(f"For '{url}' I got ConnectionError")
        return e
    except requests.exceptions.Timeout as e:
        print(f"For '{url}' I got Timeout")
        return e
    except requests.exceptions.RequestException as e:
        print(f"For '{url}' I got RequestException")
        return e

    print(f"For '{url}' download completed")
    return None


class CdpSession:
    def __init__(self, ws_url: str) -> None:
        self._ws = create_connection(ws_url, timeout=300)
        self._next_id = 0

    def close(self) -> None:
        self._ws.close()

    def call(self, method: str, params: Optional[dict[str, Any]] = None, timeout: float = 300) -> dict[str, Any]:
        self._next_id += 1
        message_id = self._next_id
        self._ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))

        deadline = time.time() + timeout
        while time.time() < deadline:
            self._ws.settimeout(max(0.1, deadline - time.time()))
            try:
                raw = self._ws.recv()
            except WebSocketTimeoutException:
                continue

            response = json.loads(raw)
            if response.get("id") != message_id:
                continue
            if "error" in response:
                raise RuntimeError(response["error"])
            return response.get("result", {})

        raise TimeoutError(f"Timed out waiting for CDP response to {method}")


def pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_devtools(port: int, timeout: float = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(f"http://127.0.0.1:{port}/json/version", timeout=1)
            if response.ok:
                return
        except requests.RequestException:
            pass
        time.sleep(0.2)
    raise TimeoutError("Chromium did not expose DevTools in time")


def create_page_target(port: int) -> str:
    response = requests.put(f"http://127.0.0.1:{port}/json/new?about:blank", timeout=5)
    response.raise_for_status()
    return response.json()["webSocketDebuggerUrl"]


def wait_for_page_ready(session: CdpSession) -> None:
    session.call("Page.enable")
    session.call(
        "Runtime.evaluate",
        {
            "expression": """
                new Promise((resolve) => {
                    const done = () => {
                        if (typeof pdfixUpdateLayout === 'function') {
                            pdfixUpdateLayout();
                        }
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
        timeout=120,
    )


def get_page_count(session: CdpSession) -> int:
    result = session.call(
        "Runtime.evaluate",
        {
            "expression": """
                (() => {
                    const pdfixPages = document.querySelectorAll('[data-type="pdf-page"]').length;
                    if (pdfixPages > 0) {
                        return pdfixPages;
                    }
                    const pageHeight = 1056;
                    return Math.max(1, Math.ceil(document.body.scrollHeight / pageHeight));
                })()
            """,
            "returnByValue": True,
        },
    )
    page_count = result.get("result", {}).get("value", 1)
    return max(1, int(page_count))


def write_pdf_stream(session: CdpSession, stream_handle: str, destination: str) -> None:
    with open(destination, "wb") as pdf_file:
        while True:
            chunk = session.call(
                "IO.read",
                {"handle": stream_handle, "size": CDP_IO_READ_SIZE},
            )
            data = chunk["data"]
            if chunk.get("base64Encoded"):
                pdf_file.write(base64.b64decode(data))
            else:
                pdf_file.write(data.encode("latin-1"))
            if chunk.get("eof"):
                break
    session.call("IO.close", {"handle": stream_handle})


def print_page_range(session: CdpSession, page_ranges: str, destination: str) -> None:
    result = session.call(
        "Page.printToPDF",
        {
            "printBackground": True,
            "preferCSSPageSize": True,
            "pageRanges": page_ranges,
            "transferMode": "ReturnAsStream",
        },
        timeout=600,
    )
    write_pdf_stream(session, result["stream"], destination)


def merge_pdf_parts(part_paths: list[str], output_path: str) -> None:
    writer = PdfWriter()
    for part_path in part_paths:
        writer.append(part_path)
    with open(output_path, "wb") as output_file:
        writer.write(output_file)


def print_html_to_pdf(html_uri: str, output_path: str) -> None:
    port = pick_free_port()
    user_data_dir = tempfile.mkdtemp(prefix="chromium-profile-")
    process = subprocess.Popen(
        [
            CHROMIUM_EXECUTABLE,
            "--headless",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={user_data_dir}",
            "--remote-allow-origins=*",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    part_paths: list[str] = []
    part_dir = tempfile.mkdtemp(prefix="pdf-parts-")

    try:
        wait_for_devtools(port)
        session = CdpSession(create_page_target(port))
        try:
            session.call("Page.navigate", {"url": html_uri})
            wait_for_page_ready(session)

            page_count = get_page_count(session)
            print(f"Printing {page_count} page(s) in batches of {PDF_PAGE_BATCH_SIZE}")

            for start_page in range(1, page_count + 1, PDF_PAGE_BATCH_SIZE):
                end_page = min(start_page + PDF_PAGE_BATCH_SIZE - 1, page_count)
                page_ranges = f"{start_page}-{end_page}"
                part_path = os.path.join(part_dir, f"part-{start_page}-{end_page}.pdf")
                print(f"Printing pages {page_ranges}")
                print_page_range(session, page_ranges, part_path)
                part_paths.append(part_path)

            merge_pdf_parts(part_paths, output_path)
            print("PDF parts merged successfully")
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
            if os.path.exists(part_path):
                os.remove(part_path)
        if os.path.isdir(part_dir):
            shutil.rmtree(part_dir, ignore_errors=True)
        if os.path.isdir(user_data_dir):
            shutil.rmtree(user_data_dir, ignore_errors=True)

        if process.returncode not in (0, None, -15):
            stderr = process.stderr.read() if process.stderr else ""
            if stderr:
                print(stderr, file=sys.stderr)


def convert_to_pdf(url: str, output: str) -> None:
    """
    Converts website to PDF document.

    Args:
        url (str): URL to website.
        output (str): Path to output PDF document.
    """
    output_path = os.path.abspath(output)

    with tqdm(total=100) as progress_bar:
        tempdir: Optional[tempfile.TemporaryDirectory[str]] = None
        html_path: str

        try:
            if os.path.isfile(url):
                progress_bar.set_description("Reading local file")
                html_path = os.path.abspath(url)
            else:
                progress_bar.set_description("Downloading webpage")
                tempdir = tempfile.TemporaryDirectory()
                html_path = os.path.join(tempdir.name, f"{uuid.uuid4()}.html")
                download_website_to_file(url, html_path)
        except Exception as e:
            print(e, file=sys.stderr)
            raise FailedToDownloadException()

        progress_bar.update(50)
        progress_bar.set_description("Converting")

        if not os.path.isfile(CHROMIUM_EXECUTABLE):
            print("Chromium executable was not found.", file=sys.stderr)
            raise FailedToConvertException()

        html_source = Path(html_path).as_uri()
        if tempdir is None:
            print("Using local HTML file")
        else:
            print("Webpage saved into container")

        try:
            print_html_to_pdf(html_source, output_path)
            print("Command executed successfully")
        except Exception as e:
            print(e, file=sys.stderr)
            raise FailedToConvertException()
        finally:
            if tempdir is not None:
                tempdir.cleanup()

        progress_bar.set_description("Done")
        progress_bar.update(50)
