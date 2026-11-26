
import json
from collections import Counter
from pathlib import Path

FILE = Path("data/processed/chunks.json")

with open(FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print("\n========== CHUNK QUALITY REPORT ==========")

categories = Counter(
    chunk["metadata"].get("category", "unknown")
    for chunk in chunks
)

documents = Counter(
    chunk["metadata"].get("document_id", "unknown")
    for chunk in chunks
)

missing_metadata = [
    chunk["chunk_id"]
    for chunk in chunks
    if not chunk["metadata"].get("source")
    or not chunk["metadata"].get("title")
]

print(f"Total chunks: {len(chunks)}")
print(f"Unique source documents: {len(documents)}")
print(f"Missing source/title metadata: {len(missing_metadata)}")

print("\nChunks by category:")
for category, count in categories.most_common():
    print(f"{category}: {count}")

print("\nChunks per source document:")
print(f"Minimum: {min(documents.values())}")
print(f"Maximum: {max(documents.values())}")
print(f"Average: {sum(documents.values()) / len(documents):.2f}")

print("\n========== SAMPLE CHUNKS ==========")

for i, chunk in enumerate(chunks[:5], start=1):
    metadata = chunk["metadata"]

    print(f"\n--- SAMPLE {i} ---")
    print(f"Title: {metadata.get('title')}")
    print(f"Category: {metadata.get('category')}")
    print(f"Source: {metadata.get('source')}")
    print(f"Chunk ID: {chunk['chunk_id']}")
    print(f"Start index: {metadata.get('start_index')}")
    print(f"Content:\n{chunk['content'][:700]}")

print("\n========== VALIDATION ==========")
print("All chunks have source metadata:", not missing_metadata)
print("All chunk IDs unique:", len({c["chunk_id"] for c in chunks}) == len(chunks))
