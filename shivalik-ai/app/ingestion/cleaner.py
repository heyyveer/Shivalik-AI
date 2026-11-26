
import json
import re
import hashlib
from pathlib import Path
from collections import Counter

RAW_DIR = Path("data/raw/pages")
PROCESSED_DIR = Path("data/processed")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

CATEGORY_RULES = {
    "fees": [
        "fee structure", "fees", "tuition"
    ],
    "placements": [
        "placement", "recruiter", "training program"
    ],
    "events": [
        "events", "event", "fest", "shivagman", "shivatech",
        "mmcitre"
    ],
    "research": [
        "research", "patent", "grants", "incubation",
        "research papers"
    ],
    "faculty": [
        "faculty", "faculty profile", "professor profile",
        "staff profile"
    ],
    "admissions": [
        "admission", "eligibility", "application"
    ],
    "campus": [
        "hostel", "library", "transport", "campus",
        "facilities", "clubs"
    ],
    "academics": [
        "course", "b.tech", "bca", "mba", "bba",
        "b.pharm", "school-of", "curriculum",
        "agriculture", "engineering"
    ],
    "news": [
        "news"
    ],
    "blogs": [
        "blog", "career guide", "career after"
    ],
    "about": [
        "overview", "vision", "mission",
        "leadership", "governance"
    ]
}


FORM_LABELS = {
    "name",
    "email",
    "phone",
    "city",
    "state",
    "school",
    "select school",
    "program",
    "select program",
    "leave blank",
    "do not check this"
}

CTA_PHRASES = [
    "ready to take the next step?",
    "connect now and begin your journey with shivalik university."
]

COUNTER_ARTIFACTS = {
    "+",
    "%",
    "lpa"
}


def is_boilerplate_line(line):
    normalized = line.strip().lower()

    if normalized in FORM_LABELS:
        return True

    if normalized in COUNTER_ARTIFACTS:
        return True

    if any(phrase in normalized for phrase in CTA_PHRASES):
        return True

    return False



def clean_text(text):
    if not isinstance(text, str):
        return ""

    text = text.replace("\xa0", " ")

    # Remove control characters while preserving newlines
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normalize spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Filter irrelevant website elements
    lines = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if is_boilerplate_line(line):
            continue

        lines.append(line)

    text = "\n".join(lines)

    # Normalize excessive line breaks
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()




def classify_document(title, url):
    title_lower = title.lower()
    url_lower = url.lower()

    # Content-type based classification
    if "/blog/" in url_lower:
        return "blogs"

    if "/news-center/events" in url_lower:
        return "events"

    if "/news-center/news/" in url_lower:
        return "news"

    # Category based on website URL structure
    if "/research/" in url_lower:
        return "research"

    if "/placements/" in url_lower:
        return "placements"

    if "/campus-life" in url_lower:
        return "campus"

    if "/aboutus/" in url_lower:
        return "about"

    if "/admissions/" in url_lower:
        if any(word in title_lower for word in ["fee", "tuition"]):
            return "fees"
        return "admissions"

    # Academic schools and individual courses
    academic_keywords = [
        "school-of",
        "b.tech",
        "bca",
        "bba",
        "mba",
        "b.pharm",
        "b.sc",
        "bachelor of",
        "master of"
    ]

    if any(word in title_lower or word in url_lower
           for word in academic_keywords):
        return "academics"

    if "news-center" in url_lower:
        return "news"

    if "contact" in url_lower:
        return "general"

    return "general"



def generate_content_hash(content):
    normalized_content = re.sub(
        r"\s+", " ", content.lower()
    ).strip()

    return hashlib.sha256(
        normalized_content.encode("utf-8")
    ).hexdigest()


def clean_source_specific_content(content, url):
    url_lower = url.lower().rstrip("/")

    if url_lower.endswith("/school-of-computing-applications"):

        # Remove incomplete animated counter labels
        invalid_counter_labels = {
            "years of academic excellence",
            "placement rocord",
            "highest package",
            "research publications"
        }

        lines = [
            line for line in content.splitlines()
            if line.strip().lower() not in invalid_counter_labels
        ]

        content = "\n".join(lines)

        # Remove the incorrect agriculture-related vision statement
        incorrect_vision = (
            "To be a premier hub for agricultural innovation, "
            "fostering sustainable farming, rural development "
            "and dynamic, career-ready arbitrageurs."
        )

        content = content.replace(incorrect_vision, "")

        # Remove the orphaned Vision heading only if followed
        # by another section heading
        content = re.sub(
            r"(?m)^Vision\s*\n(?=Partnered)",
            "",
            content
        )

    return content.strip()


def process_documents():
    files = sorted(RAW_DIR.glob("*.json"))

    processed = []
    seen_hashes = set()
    category_counts = Counter()

    duplicate_count = 0
    skipped_count = 0
    error_count = 0

    for file in files:
        try:
            with open(file, encoding="utf-8") as f:
                document = json.load(f)

            title = document.get("title", "").strip()
            url = document.get("url", "")

            content = clean_text(
                document.get("content", "")
            )

            content = clean_source_specific_content(content, url)

            # Skip documents with insufficient content
            if len(content) < 200:
                print(f"Skipping insufficient content: {url}")
                skipped_count += 1
                continue

            content_hash = generate_content_hash(content)

            # Remove exact duplicate content
            if content_hash in seen_hashes:
                print(f"Duplicate content: {url}")
                duplicate_count += 1
                continue

            seen_hashes.add(content_hash)

            category = classify_document(title, url)
            category_counts[category] += 1

            processed.append({
                "id": document.get("id", file.stem),
                "title": title,
                "source_url": url,
                "category": category,
                "content": content,
                "content_hash": content_hash,
                "document_type": "webpage"
            })

        except (json.JSONDecodeError, OSError, AttributeError) as error:
            print(f"Error processing {file.name}: {error}")
            error_count += 1

    output_file = PROCESSED_DIR / "documents.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            processed,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\n========== CLEANING REPORT ==========")
    print("Raw documents:", len(files))
    print("Processed documents:", len(processed))
    print("Duplicates removed:", duplicate_count)
    print("Insufficient documents:", skipped_count)
    print("Processing errors:", error_count)

    print("\nCategory distribution:")

    for category, count in category_counts.most_common():
        print(f"{category}: {count}")

    print("\nSaved:", output_file)


if __name__ == "__main__":
    process_documents()
