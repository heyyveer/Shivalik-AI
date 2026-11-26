
import json
import hashlib
import fitz

from pathlib import Path
from datetime import datetime, timezone

PDF_DIR = Path("data/raw/pdfs")
OUTPUT_DIR = Path("data/processed/pdfs")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)

        if doc.is_encrypted:
            print(f"Encrypted PDF skipped: {pdf_path.name}")
            doc.close()
            return None

        metadata = doc.metadata or {}

        pages = []

        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text", sort=True).strip()

            if not text:
                continue

            pages.append({
                "page_number": page_number,
                "content": text
            })

        if not pages:
            print(f"No extractable text: {pdf_path.name}")
            doc.close()
            return None

        source_hash = hashlib.sha256(
            pdf_path.read_bytes()
        ).hexdigest()

        result = {
            "id": source_hash[:16],
            "filename": pdf_path.name,
            "title": metadata.get("title") or pdf_path.stem,
            "author": metadata.get("author"),
            "source_url": None,
            "source_type": "pdf",
            "total_pages": doc.page_count,
            "extracted_pages": len(pages),
            "pages": pages,
            "content_hash": source_hash,
            "extracted_at": datetime.now(timezone.utc).isoformat()
        }

        doc.close()
        return result

    except Exception as error:
        print(f"Extraction failed: {pdf_path.name} | {error}")
        return None


def process_pdfs():
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    extracted_documents = []

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")

        document = extract_pdf(pdf_path)

        if document:
            output_path = OUTPUT_DIR / f"{document['id']}.json"

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    document,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            extracted_documents.append(document)
            print(
                f"Extracted {document['extracted_pages']} "
                f"pages from {pdf_path.name}"
            )

    print("\n========== PDF EXTRACTION REPORT ==========")
    print("PDF files found:", len(pdf_files))
    print("Successfully extracted:", len(extracted_documents))
    print("Output directory:", OUTPUT_DIR)

    return extracted_documents


if __name__ == "__main__":
    process_pdfs()
