
import json
import time
import hashlib
from pathlib import Path
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag, urlunparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://sudoon.ac.in/"
ALLOWED_DOMAINS = {"sudoon.ac.in"}

OUTPUT_DIR = Path("data/raw")
PAGES_DIR = OUTPUT_DIR / "pages"
PAGES_DIR.mkdir(parents=True, exist_ok=True)

SKIP_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".svg",
    ".webp", ".zip", ".mp4", ".mp3", ".css", ".js"
)

SKIP_KEYWORDS = (
    "login", "logout", "register", "facebook",
    "instagram", "linkedin", "youtube", "whatsapp"
)

HEADERS = {
    "User-Agent": "ShivalikAI-ResearchBot/1.0 (College information assistant)"
}

session = requests.Session()
session.headers.update(HEADERS)


def normalize_url(url):
    url, _ = urldefrag(url)
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return None

    if parsed.netloc.lower() not in ALLOWED_DOMAINS:
        return None

    path = parsed.path or "/"

    return urlunparse((
        "https",
        parsed.netloc.lower(),
        path,
        "",
        parsed.query,
        ""
    ))


import re

NOISE_SELECTORS = [
    "header",
    "footer",
    "nav",
    "aside",
    '[role="navigation"]',
    '[role="complementary"]',
    "form",
    "script",
    "style",
    "noscript",
    "iframe",
    "button",
    ".elementor-location-header",
    ".elementor-location-footer",
    ".elementor-nav-menu",
    ".elementor-widget-nav-menu",
    ".menu",
    ".navbar",
    ".navigation",
    ".breadcrumb",
    ".breadcrumbs",
    ".social-icons",
    ".share-buttons",
    ".cookie-banner",
    ".popup",
    ".modal"
]

CONTENT_SELECTORS = [
    "main",
    "article",
    '[role="main"]',
    ".entry-content",
    ".post-content",
    ".site-main",
    ".content-area",
    ".elementor-widget-theme-post-content"
]



def remove_noise(soup):
    # Remove only clearly identifiable non-content HTML elements.
    selectors = [
        "script",
        "style",
        "noscript",
        "header",
        "footer",
        "nav",
        "iframe",
        '[role="navigation"]',
        ".elementor-location-header",
        ".elementor-location-footer",
        ".elementor-widget-nav-menu",
        ".elementor-nav-menu",
        ".breadcrumb",
        ".breadcrumbs",
        ".social-icons",
        ".share-buttons",
        ".cookie-banner"
    ]

    for selector in selectors:
        for element in list(soup.select(selector)):
            if element.parent is not None:
                element.decompose()




def find_main_content(soup):
    selectors = [
        "main",
        "article",
        '[role="main"]',
        ".elementor-location-single",
        ".elementor-widget-theme-post-content",
        ".entry-content",
        ".post-content",
        ".site-main",
        ".content-area",
        "#content",
        "#primary"
    ]

    for selector in selectors:
        element = soup.select_one(selector)

        if element:
            text_length = len(element.get_text(" ", strip=True))

            if text_length >= 200:
                return element

    return soup.body



def extract_tables(container):
    formatted_tables = []

    for table_number, table in enumerate(
        container.find_all("table"),
        start=1
    ):
        rows = []

        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"], recursive=False)

            values = [
                cell.get_text(" ", strip=True)
                for cell in cells
            ]

            if values:
                rows.append(values)

        if not rows:
            continue

        headers = rows[0]

        table_text = [f"TABLE {table_number}"]

        if any(cell.name == "th" for cell in table.find_all("tr")[0].find_all(["th", "td"], recursive=False)):
            table_text.append("Headers: " + " | ".join(headers))
            data_rows = rows[1:]
        else:
            data_rows = rows

        for row in data_rows:
            if len(headers) == len(row):
                table_text.append(
                    " | ".join(
                        f"{headers[i]}: {value}"
                        for i, value in enumerate(row)
                    )
                )
            else:
                table_text.append(" | ".join(row))

        formatted_tables.append("\n".join(table_text))

    return formatted_tables


def should_skip(url):
    parsed = urlparse(url)
    path = parsed.path.lower()

    if path.endswith(SKIP_EXTENSIONS):
        return True
    path = urlparse(url).path.strip("/")

    if re.fullmatch(r"\d{7,15}", path):
        return True
    if any(word in url.lower() for word in SKIP_KEYWORDS):
        return True

    return False



def extract_page(url):
    try:
        response = session.get(url, timeout=20)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")

        if "text/html" not in content_type.lower():
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        print("Raw HTML size:", len(response.text))

        print(
            "Text before cleaning:",
            len(soup.get_text(" ", strip=True))
        )
        title = (
            soup.title.get_text(" ", strip=True)
            if soup.title else ""
        )

        # Collect links before modifying the HTML.
        links = set()
        pdf_links = set()

        for anchor in soup.find_all("a", href=True):
            href = urljoin(url, anchor["href"])
            normalized = normalize_url(href)

            if not normalized:
                continue

            if urlparse(normalized).path.lower().endswith(".pdf"):
                pdf_links.add(normalized)
            elif not should_skip(normalized):
                links.add(normalized)

        # Remove scripts, navigation, forms and boilerplate.
        remove_noise(soup)
        print(
            "Text after cleaning:",
            len(soup.get_text(" ", strip=True))
        )
        # Find the most relevant page content.
        main = find_main_content(soup)
        if not main:
            print(f"No content container found: {url}")
            return None

        main = (
            soup.select_one("#body-main")
            or soup.find("main")
            or soup.find("article")
            or soup.body
        )

        text = main.get_text(separator="\n", strip=True)

        print(f"Title: {title}")
        print(f"Extracted characters: {len(text)}")
        print(f"Selected container: {main.name}")
        if not main:
            return None

        # Preserve tables before extracting normal text.
        tables = extract_tables(main)

        for table in main.find_all("table"):
            table.decompose()

        text = main.get_text(separator="\n", strip=True)

        if tables:
            text += "\n\n" + "\n\n".join(tables)

        page_id = hashlib.sha256(
            url.encode("utf-8")
        ).hexdigest()[:16]

        if len(text.strip()) < 200:
            print(f"Insufficient content ({len(text.strip())} chars): {url}")
            return None

        return {
            "id": page_id,
            "url": url,
            "title": title,
            "content": text,
            "links": sorted(links),
            "pdf_links": sorted(pdf_links)
        }

    except requests.RequestException as error:
        print(f"Failed: {url} | {error}")
        return None



def crawl_website(max_pages=100):
    queue = deque([BASE_URL])
    visited = set()
    documents = []

    while queue and len(visited) < max_pages:
        url = normalize_url(queue.popleft())

        if not url or url in visited or should_skip(url):
            continue

        visited.add(url)
        print(f"Crawling [{len(visited)}]: {url}")

        page = extract_page(url)

        if page:
            documents.append(page)

            output_file = PAGES_DIR / f"{page['id']}.json"

            with open(output_file, "w", encoding="utf-8") as file:
                json.dump(page, file, ensure_ascii=False, indent=2)

            for link in page["links"]:
                if link not in visited:
                    queue.append(link)

        time.sleep(1)

    print(f"\nTotal pages visited: {len(visited)}")
    print(f"Successfully extracted: {len(documents)}")

    return documents

if __name__ == "__main__":
    crawl_website(max_pages=100)
