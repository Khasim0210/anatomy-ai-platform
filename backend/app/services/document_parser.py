from pathlib import Path

import fitz
from docx import Document


def extract_docx_text(file_path: str) -> str:
    document = Document(file_path)

    paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def extract_pdf_text(file_path: str) -> str:
    document = fitz.open(file_path)

    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text("text").strip()

        if text:
            pages.append(
                f"--- Page {page_number} ---\n{text}"
            )

    document.close()

    return "\n\n".join(pages)


def extract_document_text(file_path: str) -> str:
    extension = Path(file_path).suffix.lower()

    if extension == ".docx":
        return extract_docx_text(file_path)

    if extension == ".pdf":
        return extract_pdf_text(file_path)

    raise ValueError("Unsupported document type")