
import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path("data/raw/pages")

files = list(DATA_DIR.glob("*.json"))
total_chars = 0
empty_pages = []
short_pages = []
titles = []
domains = Counter()

for file in files:
    with open(file, encoding="utf-8") as f:
        data = json.load(f)

    content = data.get("content", "").strip()
    title = data.get("title", "").strip()
    url = data.get("url", "")

    total_chars += len(content)

    if not content:
        empty_pages.append(url)

    if len(content) < 200:
        short_pages.append(url)

    titles.append(title)
    domains[url.split("/")[2] if "://" in url else "unknown"] += 1

print("\n========== CRAWLER REPORT ==========")
print("Total JSON files:", len(files))
print("Total extracted characters:", total_chars)
print("Average characters per page:", total_chars // max(len(files), 1))
print("Empty pages:", len(empty_pages))
print("Short pages (<200 chars):", len(short_pages))

print("\n========== PAGE TITLES ==========")
for title in titles:
    print("-", title or "Missing title")

print("\n========== EMPTY PAGES ==========")
for url in empty_pages:
    print(url)

print("\n========== SHORT PAGES ==========")
for url in short_pages:
    print(url)
