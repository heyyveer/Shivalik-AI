
import json
import hashlib
import requests

from pathlib import Path
from urllib.parse import urlparse, unquote
from datetime import datetime, timezone

URL_FILE = Path("data/raw/pdf_links.json")
OUTPUT_DIR = Path("data/raw/pdfs")
METADATA_FILE = OUTPUT_DIR / "metadata.json"

ALLOWED_DOMAINS = {"sudoon.ac.in"}
MAX_SIZE = 25 * 1024 * 1024

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with open(URL_FILE, encoding="utf-8") as f:
    urls = json.load(f)

metadata = []

for url in urls:
    parsed = urlparse(url)

    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOMAINS:
        print("Skipped unsafe URL:", url)
        continue

    if not parsed.path.lower().endswith(".pdf"):
        continue

    try:
        response = requests.get(
            url,
            timeout=30,
            stream=True,
            headers={"User-Agent": "ShivalikAI-ResearchBot/1.0"}
        )

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()

        if "pdf" not in content_type and "octet-stream" not in content_type:
            print("Not a PDF response:", url)
            continue

        chunks = []
        total_size = 0

        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue

            total_size += len(chunk)

            if total_size > MAX_SIZE:
                raise ValueError("PDF exceeds maximum allowed size")

            chunks.append(chunk)

        content = b"".join(chunks)

        if not content.startswith(b"%PDF-"):
            print("Invalid PDF file:", url)
            continue

        file_hash = hashlib.sha256(content).hexdigest()
        filename = file_hash[:16] + ".pdf"
        output_path = OUTPUT_DIR / filename

        output_path.write_bytes(content)

        metadata.append({
            "filename": filename,
            "source_url": url,
            "sha256": file_hash,
            "size_bytes": len(content),
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "document_type": "pdf"
        })

        print("Downloaded:", filename)

    except Exception as error:
        print(f"Failed: {url} | {error}")

with open(METADATA_FILE, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print("\n========== DOWNLOAD REPORT ==========")
print("Successfully downloaded:", len(metadata))
print("Saved metadata:", METADATA_FILE)
