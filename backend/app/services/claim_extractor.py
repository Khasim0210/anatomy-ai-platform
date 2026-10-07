import re
from typing import List, Dict


SKIP_PREFIXES = (
    "readings",
    "images",
    "think:",
    "see ",
    "nb:",
)


def clean_line(line: str) -> str:
    line = line.strip()

    # Remove bullets and common list markers
    line = re.sub(r"^[•\-–—]+\s*", "", line)

    # Remove simple sub-bullet marker such as "o "
    line = re.sub(r"^o\s+", "", line, flags=re.IGNORECASE)

    # Normalize spaces
    line = re.sub(r"\s+", " ", line)

    return line.strip()


def is_heading(text: str) -> bool:
    words = text.split()

    if len(words) > 7:
        return False

    # Short lines without sentence-like verbs are probably headings
    verbs = {
        "is",
        "are",
        "has",
        "have",
        "contains",
        "contain",
        "forms",
        "form",
        "allows",
        "allow",
        "provides",
        "provide",
        "develops",
        "develop",
        "results",
        "result",
    }

    lowered_words = {word.lower().strip(".,:;()") for word in words}

    return not bool(lowered_words.intersection(verbs))


def is_useful_claim(text: str) -> bool:
    if not text:
        return False

    lower_text = text.lower()

    # Skip page markers
    if text.startswith("--- Page"):
        return False

    # Skip reference lines and instructional notes
    if lower_text.startswith(SKIP_PREFIXES):
        return False

    # Skip very short fragments
    if len(text) < 15:
        return False

    # Skip likely headings
    if is_heading(text):
        return False

    return True


def extract_claims(text: str) -> List[Dict]:
    claims = []

    current_page = None
    claim_id = 1

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        page_match = re.match(r"--- Page (\d+) ---", line)

        if page_match:
            current_page = int(page_match.group(1))
            continue

        cleaned = clean_line(line)

        if not is_useful_claim(cleaned):
            continue

        claims.append(
            {
                "claim_id": claim_id,
                "page": current_page,
                "text": cleaned,
            }
        )

        claim_id += 1

    return claims