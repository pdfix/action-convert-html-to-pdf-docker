import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def get_links(url):
    links = set()
    try:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.content, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            link = a_tag["href"]
            # if "#" in link:
            #     continue

            if link.startswith("http"):  # Absolute URL
                links.add(link)
            else:  # Relative URL
                absolute_link = urljoin(url, link)
                links.add(absolute_link)
    except Exception as e:
        print(f"An error occurred: {e}")
    return links


def crawl_website(start_url, max_pages):
    crawled_pages = set()
    pages_to_crawl = {start_url}

    while pages_to_crawl and len(crawled_pages) < max_pages:
        url = pages_to_crawl.pop()
        if url not in crawled_pages:
            print("Crawling:", url)
            crawled_pages.add(url)
            new_links = get_links(url)
            pages_to_crawl.update(new_links - crawled_pages)

    return crawled_pages


if __name__ == "__main__":
    start_url = input("Enter the starting URL: ")
    max_pages = int(input("Enter the maximum number of pages to crawl: "))

    crawled_pages = crawl_website(start_url, max_pages)

    # print("\nCrawled Pages:")i

    with open("collected_links.txt", "w") as f:
        for page in crawled_pages:
            f.write(page + "\n")
