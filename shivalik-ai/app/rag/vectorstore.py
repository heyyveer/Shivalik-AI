
import json
from pathlib import Path

import chromadb

from app.rag.embeddings import get_embeddings


CHUNKS_FILE = Path("data/processed/chunks.json")
CHROMA_DIR = Path("data/chroma_db")
COLLECTION_NAME = "shivalik_knowledge"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_collection():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": EMBEDDING_MODEL,
        },
    )

    return collection


STRUCTURED_FILE = Path("data/processed/structured_chunks.json")


def load_chunks():
    all_chunks = []

    for file_path in [CHUNKS_FILE, STRUCTURED_FILE]:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required dataset not found: {file_path}"
            )

        with open(file_path, "r", encoding="utf-8") as file:
            chunks = json.load(file)

        all_chunks.extend(chunks)

    ids = [chunk["chunk_id"] for chunk in all_chunks]

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate chunk IDs detected")

    return all_chunks

def prepare_metadata(metadata):
    cleaned = {}

    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value

    return cleaned


def ingest_chunks(batch_size=32):
    chunks = load_chunks()

    if not chunks:
        print("No chunks available for ingestion.")
        return

    collection = get_collection()
    embeddings = get_embeddings()

    print("\n========== CHROMADB INGESTION ==========")
    print(f"Chunks loaded: {len(chunks)}")
    print(f"Existing vectors: {collection.count()}")

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]

        ids = [chunk["chunk_id"] for chunk in batch]
        documents = [chunk["content"] for chunk in batch]

        metadatas = [
            prepare_metadata(chunk["metadata"])
            for chunk in batch
        ]

        vectors = embeddings.embed_documents(documents)

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=vectors,
            metadatas=metadatas,
        )

        print(
            f"Processed {min(start + batch_size, len(chunks))}"
            f"/{len(chunks)} chunks"
        )

    print("\n========== INGESTION COMPLETE ==========")
    print(f"Total vectors in ChromaDB: {collection.count()}")


if __name__ == "__main__":
    ingest_chunks()
