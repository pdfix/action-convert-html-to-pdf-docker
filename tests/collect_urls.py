import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def get_links(url: str) -> set[str]:
    """
    Extracts from webpage all URLs.

    Args:
        url (str): Webpage URL.

    Returns:
        Set containing all URLs from webpage.
    """
    links: set[str] = set()
    try:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.content, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            link: str = a_tag["href"]

            if link.startswith("http"):  # Absolute URL
                links.add(link)
            else:  # Relative URL
                absolute_link: str = urljoin(url, link)
                links.add(absolute_link)
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
    return links


def crawl_website(start_url: str, max_pages: int) -> set[str]:
    """
    Starts website crawler at start_url and stops either when all
    webpages are crawled or when max_pages limit is reached.

    Args:
        start_url (str): URL to start crawling from.
        max_pages (int): Limit when crawler stops processing webpages.

    Returns:
        Set of webpage URLs (can be more then max_pages).
    """
    crawled_pages: set[str] = set()
    pages_to_crawl: set[str] = {start_url}

    while pages_to_crawl and len(crawled_pages) < max_pages:
        url = pages_to_crawl.pop()
        if url not in crawled_pages:
            print(f"Crawling: {url}")
            crawled_pages.add(url)
            new_links: set[str] = get_links(url)
            pages_to_crawl.update(new_links - crawled_pages)

    return crawled_pages


if __name__ == "__main__":
    start_url: str = input("Enter the starting URL: ")
    max_pages: int = int(input("Enter the maximum number of pages to crawl: "))

    crawled_pages: set[str] = crawl_website(start_url, max_pages)

    with open("collected_links.txt", "w") as file:
        for page in crawled_pages:
            file.write(page + "\n")
