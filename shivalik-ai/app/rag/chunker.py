
import hashlib
import json
import re
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.ingestion.loader import load_all_documents

OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "chunks.json"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def generate_chunk_id(document_id, content):
    normalized = re.sub(r"\s+", " ", content).strip()
    raw = f"{document_id}:{normalized}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
        add_start_index=True
    )

    chunks = []
    seen = set()
    document_chunk_counts = {}

    for document in documents:
        document_id = document.metadata.get("document_id", "unknown")

        split_docs = splitter.split_documents([document])

        for doc in split_docs:
            content = doc.page_content.strip()

            if not content:
                continue

            chunk_id = generate_chunk_id(document_id, content)

            if chunk_id in seen:
                continue

            seen.add(chunk_id)

            chunk_index = document_chunk_counts.get(document_id, 0)

            metadata = dict(doc.metadata)
            metadata["chunk_id"] = chunk_id
            metadata["chunk_index"] = chunk_index
            metadata["chunk_size"] = len(content)
            metadata["start_index"] = doc.metadata.get("start_index", 0)

            chunks.append({
                "chunk_id": chunk_id,
                "content": content,
                "metadata": metadata
            })

            document_chunk_counts[document_id] = chunk_index + 1

    return chunks


def save_chunks(chunks):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)


def main():
    print("\n========== DOCUMENT CHUNKING ==========")

    documents = load_all_documents()
    print(f"Documents received: {len(documents)}")

    chunks = chunk_documents(documents)
    save_chunks(chunks)

    sizes = [chunk["metadata"]["chunk_size"] for chunk in chunks]

    print(f"Total chunks generated: {len(chunks)}")
    print(f"Average chunk size: {sum(sizes) / len(sizes):.0f}" if sizes else "Average chunk size: 0")
    print(f"Smallest chunk: {min(sizes) if sizes else 0}")
    print(f"Largest chunk: {max(sizes) if sizes else 0}")
    print(f"Unique chunk IDs: {len({c['chunk_id'] for c in chunks})}")


    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
