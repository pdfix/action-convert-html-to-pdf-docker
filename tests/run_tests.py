import platform
import random
import string
import subprocess
import sys
from tqdm import tqdm
import docker
import multiprocessing
import datetime


CHROME_VERSION = "122.0.6261.111"


def run_chrome(url: str) -> bool:
    try:
        chrome = "../dist/html_to_pdf/html_to_pdf"
    except Exception as e:
        print("Chrome cli was not found.", file=sys.stderr)
        return False

    random_name = (
        "".join(random.choices(string.ascii_lowercase + string.digits, k=10)) + ".pdf"
    )

    args = [chrome, "--url", url, "--output", random_name]
    log_to_file("Running with args: " + " ".join(args))

    result = subprocess.run(args, shell=False, capture_output=True, text=True)

    if result.returncode == 0:
        print("Command executed successfully")
        return True
    else:
        print("Error:", result.stderr, file=sys.stderr)
        return False


def read_file_line_by_line_with_progress(file_path):
    total = 0
    ok = 0

    try:
        with open(file_path, "r") as file:
            from multiprocessing.pool import ThreadPool

            pool = ThreadPool(processes=1)

            total = sum(1 for line in file)
            file.seek(0)  # Reset file pointer to the beginning
            with tqdm(total=total, desc="Running tests", unit="test") as pbar:
                for url in file:
                    url = url.strip()

                    async_result = pool.apply_async(run_chrome, (url,))

                    try:
                        res = async_result.get(timeout=30)
                        if res:
                            ok += 1
                    except multiprocessing.context.TimeoutError:
                        log_to_file("[Failed] Chrome timed out. {}".format(url))

                    pbar.update(1)

    except FileNotFoundError:
        print(f"File '{file_path}' not found.")

    print("Summary:\nTotal tests (passed): {} ({})\n".format(total, ok))


def log_to_file(msg: str):
    logf = open("test.log", "a")
    now = datetime.datetime.now()

    logf.write("[{}] {}\n".format(now.time(), msg))


if __name__ == "__main__":
    file_path = "collected_links.txt"
    read_file_line_by_line_with_progress(file_path)
