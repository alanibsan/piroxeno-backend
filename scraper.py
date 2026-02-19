import requests
import json
import hashlib
from bs4 import BeautifulSoup


def save_page_as_json(url):
    print("👉 save_page_as_json CALLED:", url)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; IOFTBot/1.0)"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
    except requests.RequestException:
        print("❌ REQUEST FAILED:", url)
        return

    soup = BeautifulSoup(r.text, "lxml")
    text = soup.get_text(separator=" ", strip=True)

    if len(text) < 150:
        print("❌ TOO SHORT:", url)
        return

    h = hashlib.md5(text.encode("utf-8")).hexdigest()

    data = {
        "url": url,
        "content": text,
        "hash": h,
        "source": "ioft.es"
    }

    with open(f"data/{h}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ SAVED:", url)

