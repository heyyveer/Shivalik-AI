
import json

from pathlib import Path
from langchain_core.documents import Document

HTML_DIR = Path("data/processed")
PDF_DIR = Path("data/processed/pdfs")


def load_html_documents():
    file_path = HTML_DIR / "documents.json"

    if not file_path.exists():
        return []

    with open(file_path, encoding="utf-8") as f:
        documents = json.load(f)

    results = []

    for item in documents:
        results.append(
            Document(
                page_content=item["content"],
                metadata={
                    "document_id": item["id"],
                    "title": item["title"],
                    "source": item["source_url"],
                    "category": item["category"],
                    "document_type": "webpage"
                }
            )
        )

    return results


def load_pdf_documents():
    results = []

    if not PDF_DIR.exists():
        return results

    for file_path in PDF_DIR.glob("*.json"):
        with open(file_path, encoding="utf-8") as f:
            item = json.load(f)

        for page in item.get("pages", []):
            results.append(
                Document(
                    page_content=page["content"],
                    metadata={
                        "document_id": item["id"],
                        "title": item["title"],
                        "source": item.get("source_url") or item["filename"],
                        "category": "general",
                        "document_type": "pdf",
                        "page_number": page["page_number"]
                    }
                )
            )

    return results


def load_all_documents():
    html_documents = load_html_documents()
    pdf_documents = load_pdf_documents()

    documents = html_documents + pdf_documents

    print("\n========== DOCUMENT LOADER REPORT ==========")
    print("HTML documents:", len(html_documents))
    print("PDF pages:", len(pdf_documents))
    print("Total documents:", len(documents))

    return documents


if __name__ == "__main__":
    load_all_documents()
