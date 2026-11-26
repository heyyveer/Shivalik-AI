
import json
from pathlib import Path
from urllib.parse import urlparse

RAW_DIR = Path("data/raw/pages")
ALLOWED_DOMAINS = {"sudoon.ac.in"}

pdf_links = set()

for file in RAW_DIR.glob("*.json"):
    with open(file, encoding="utf-8") as f:
        document = json.load(f)

    for url in document.get("pdf_links", []):
        parsed = urlparse(url)

        if parsed.netloc.lower() in ALLOWED_DOMAINS:
            if parsed.path.lower().endswith(".pdf"):
                pdf_links.add(url)

print("\n========== PDF DISCOVERY REPORT ==========")
print("Total unique PDF links:", len(pdf_links))

for index, url in enumerate(sorted(pdf_links), 1):
    print(f"{index}. {url}")

Path("data/raw/pdf_links.json").write_text(
    json.dumps(sorted(pdf_links), indent=2),
    encoding="utf-8"
)

print("\nSaved: data/raw/pdf_links.json")
