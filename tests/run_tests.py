import datetime
import multiprocessing
import random
import string
import subprocess
import sys
from multiprocessing.pool import ThreadPool

from tqdm import tqdm

CHROME_VERSION = "122.0.6261.111"


def run_chrome(url: str) -> bool:
    """
    Run chrome to convert url webpage into pdf.

    Args:
        url (str): Webpage URL.

    Returns:
        True if converted, False otherwise.
    """
    chrome = "../dist/html_to_pdf/html_to_pdf"
    random_name = "".join(random.choices(string.ascii_lowercase + string.digits, k=10)) + ".pdf"
    args = [chrome, "--url", url, "--output", random_name]
    log_to_file(f"Running with args: {' '.join(args)}")

    result = subprocess.run(args, shell=False, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        print("Command executed successfully")
        return True
    else:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return False


def get_number_of_lines(file_path: str) -> int:
    """
    Calculate number of lines in file.

    Args:
        file_path (str): path to file.

    Returns:
        Number of lines.
    """
    try:
        with open(file_path, "r") as file:
            return sum(1 for line in file)
    except FileNotFoundError:
        return 0


def test_urls_from_file_with_chrome(file_path: str) -> None:
    """
    Takes all URLs from file. For each creates thread and try to open it using chrome.
    Calculate how many succed.

    Args:
        file_path (str): Paht to file containing URLs on each line.
    """
    total: int = get_number_of_lines(file_path)
    ok: int = 0

    try:
        with open(file_path, "r") as file:
            pool = ThreadPool(processes=1)

            with tqdm(total=total, desc="Running tests", unit="test") as pbar:
                for line in file:
                    url = line.strip()

                    async_result = pool.apply_async(run_chrome, (url,))

                    try:
                        res = async_result.get(timeout=30)
                        if res:
                            ok += 1
                    except multiprocessing.context.TimeoutError:
                        log_to_file(f"[Failed] Chrome timed out for: {url}")

                    pbar.update(1)

    except FileNotFoundError:
        print(f"File '{file_path}' not found.")

    print(f"Summary:\nTotal tests (passed): {total} ({ok})\n")


def log_to_file(message: str) -> None:
    """
    Logging message with date into file.

    Args:
        message (str): Message to log.
    """
    with open("test.log", "a") as log_file:
        now = datetime.datetime.now()
        log_file.write(f"[{now.time()}] {message}\n")


if __name__ == "__main__":
    file_path = "collected_links.txt"
    test_urls_from_file_with_chrome(file_path)
