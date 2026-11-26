
import hashlib
import json
import re
from pathlib import Path


DOCUMENTS_FILE = Path("data/processed/documents.json")
OUTPUT_FILE = Path("data/processed/structured_chunks.json")


def generate_id(source, record_type, content):
    raw = f"{source}:{record_type}:{content}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def extract_fee_records(document):
    content = document["content"]
    source = document["source_url"]
    title = document["title"]

    session_match = re.search(
        r"Academic Session\s+(\d{4}[–-]\d{2,4})",
        content
    )

    session = (
        session_match.group(1)
        if session_match
        else "Not specified"
    )

    records = []

    for line in content.splitlines():
        line = line.strip()

        if line.startswith("Programme:"):
            record_type = "programme_fee"
            label = line.split("|")[0].replace("Programme:", "").strip()

        elif line.startswith("Charge:"):
            record_type = "additional_charge"
            label = line.split("|")[0].replace("Charge:", "").strip()

        else:
            continue

        structured_content = (
            f"Shivalik University Fee Structure\n"
            f"Academic Session: {session}\n"
            f"{line}"
        )

        record_id = generate_id(
            source,
            record_type,
            structured_content
        )

        metadata = {
            "chunk_id": record_id,
            "document_id": document["id"],
            "title": title,
            "source": source,
            "category": "fees",
            "document_type": "structured_record",
            "record_type": record_type,
            "record_label": label,
            "academic_session": session,
            "chunk_size": len(structured_content),
        }

        records.append({
            "chunk_id": record_id,
            "content": structured_content,
            "metadata": metadata,
        })

    return records


def main():
    with open(DOCUMENTS_FILE, "r", encoding="utf-8") as file:
        documents = json.load(file)

    records = []

    for document in documents:
        if document.get("category") == "fees":
            records.extend(extract_fee_records(document))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)

    print("\n========== STRUCTURED DATA REPORT ==========")
    print(f"Total structured records: {len(records)}")
    print(
        "Programme fee records:",
        sum(r["metadata"]["record_type"] == "programme_fee" for r in records)
    )
    print(
        "Additional charge records:",
        sum(r["metadata"]["record_type"] == "additional_charge" for r in records)
    )
    print(f"Unique record IDs: {len({r['chunk_id'] for r in records})}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
