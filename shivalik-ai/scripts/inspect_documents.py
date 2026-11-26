
import json
from pathlib import Path
from collections import Counter

FILE = Path("data/processed/documents.json")

with open(FILE, encoding="utf-8") as f:
    documents = json.load(f)

print("\n========== DOCUMENT QUALITY AUDIT ==========")
print("Total documents:", len(documents))

category_counts = Counter(
    doc.get("category", "missing") for doc in documents
)

print("\nCATEGORY DISTRIBUTION")
for category, count in category_counts.most_common():
    print(f"{category}: {count}")

print("\nDOCUMENT DETAILS")

for index, doc in enumerate(documents, start=1):
    content = doc.get("content", "")

    print(f"\n{index}. {doc.get('title')}")
    print("Category:", doc.get("category"))
    print("Characters:", len(content))
    print("Source:", doc.get("source_url"))
    print("Preview:", content[:250].replace("\n", " "))

print("\n========== VALIDATION ==========")

missing_titles = sum(not doc.get("title") for doc in documents)
missing_urls = sum(not doc.get("source_url") for doc in documents)
missing_content = sum(not doc.get("content", "").strip() for doc in documents)
missing_ids = sum(not doc.get("id") for doc in documents)

print("Missing titles:", missing_titles)
print("Missing URLs:", missing_urls)
print("Missing content:", missing_content)
print("Missing IDs:", missing_ids)
