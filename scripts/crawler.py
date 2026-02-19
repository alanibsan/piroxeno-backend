print("📡 CRAWLER STARTING")

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE_URL = "https://www.ioft.es"
visited = set()
to_visit = [BASE_URL]

def is_internal(url):
    return urlparse(url).netloc == urlparse(BASE_URL).netloc

while to_visit:
    url = to_visit.pop()
    if url in visited:
        continue

    visited.add(url)

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            continue
    except requests.RequestException:
        continue

    soup = BeautifulSoup(response.text, "lxml")

    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(BASE_URL, href)

        parsed = urlparse(full_url)
        full_url = parsed.scheme + "://" + parsed.netloc + parsed.path
        full_url = full_url.rstrip("/")

        if "page=" in full_url.lower():
            continue

        if is_internal(full_url) and full_url not in visited:
            if not any(ext in full_url.lower() for ext in [".pdf", ".jpg", ".png", "#"]):
                to_visit.append(full_url)

if __name__ == "__main__":
    print(f"Total URLs descubiertas: {len(visited)}")
    for u in list(visited)[:10]:
        print(u)
