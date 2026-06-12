"""Text cleaning and deduplication."""

import re

from backend.app.rag.data.models import Document


class TextCleaner:
    @staticmethod
    def clean(text: str) -> str:
        text = _strip_html(text)
        text = _normalize_chars(text)
        text = _normalize_whitespace(text)
        text = _remove_control_chars(text)
        return text.strip()

    def clean_documents(self, docs: list[Document]) -> list[Document]:
        cleaned = []
        for doc in docs:
            new_content = self.clean(doc.content)
            if len(new_content) >= 20:
                doc.content = new_content
                doc.char_count = len(new_content)
                cleaned.append(doc)
        return cleaned


class Deduplicator:
    def __init__(self, threshold: float = 0.9):
        self.threshold = threshold

    def deduplicate(self, docs: list[Document]) -> list[Document]:
        if len(docs) <= 1:
            return docs

        seen_fingerprints = set()
        unique_docs = []
        for doc in docs:
            norm = doc.content.strip().lower()
            fingerprint = norm if len(norm) <= 400 else norm[:200] + norm[-200:]
            fingerprint += f"|len={len(norm)}"
            if fingerprint not in seen_fingerprints:
                seen_fingerprints.add(fingerprint)
                unique_docs.append(doc)
        return unique_docs

    def filter_short(self, docs: list[Document], min_length: int = 20) -> list[Document]:
        return [doc for doc in docs if doc.char_count >= min_length]


def _strip_html(text: str) -> str:
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text()
    except ImportError:
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"&[a-zA-Z]+;", " ", text)
        return text


def _normalize_chars(text: str) -> str:
    result = []
    for ch in text:
        code = ord(ch)
        if 0xFF01 <= code <= 0xFF5E:
            result.append(chr(code - 0xFEE0))
        elif code == 0x3000:
            result.append(" ")
        else:
            result.append(ch)
    return "".join(result)


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


def _remove_control_chars(text: str) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

