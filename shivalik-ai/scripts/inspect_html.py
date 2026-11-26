
import requests
from bs4 import BeautifulSoup
from collections import Counter

URL = "https://sudoon.ac.in/"

response = requests.get(
    URL,
    headers={
        "User-Agent": "Mozilla/5.0"
    },
    timeout=20
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

print("\n========== HTML STRUCTURE ==========")

print("Page title:", soup.title.get_text(strip=True))

body = soup.body

print("\n========== BODY CHILDREN ==========")

for element in body.find_all(recursive=False):
    classes = " ".join(element.get("class", []))
    element_id = element.get("id", "")
    text = element.get_text(" ", strip=True)

    print({
        "tag": element.name,
        "id": element_id,
        "classes": classes,
        "text_length": len(text),
        "preview": text[:150]
    })

print("\n========== ELEMENTOR CLASSES ==========")

class_counts = Counter()

for element in soup.find_all(class_=True):
    for class_name in element.get("class", []):
        if "elementor" in class_name.lower():
            class_counts[class_name] += 1

for name, count in class_counts.most_common(30):
    print(f"{name}: {count}")

print("\n========== IMPORTANT CONTAINERS ==========")

for element in soup.find_all(True):
    element_id = element.get("id", "")
    classes = " ".join(element.get("class", []))

    if any(word in f"{element_id} {classes}".lower()
           for word in ["header", "footer", "content", "main"]):

        text = element.get_text(" ", strip=True)

        print({
            "tag": element.name,
            "id": element_id,
            "classes": classes,
            "text_length": len(text),
            "preview": text[:200]
        })
