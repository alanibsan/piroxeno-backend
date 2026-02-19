print("🚨 INGEST FILE EXECUTED 🚨")

from crawler import visited
from scraper import save_page_as_json
import time

print("🔥 INGEST STARTED 🔥")
print(f"Total URLs a procesar: {len(visited)}")

for url in visited:
    save_page_as_json(url)
    time.sleep(0.5)
