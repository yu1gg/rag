"""Shared dataclasses for backend RAG data pipeline."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Document:
    id: str
    title: str
    content: str
    source: str
    url: Optional[str] = None
    date: Optional[str] = None
    char_count: int = 0

    def __post_init__(self):
        self.char_count = len(self.content)


@dataclass
class QAPair:
    id: str
    question: str
    answer: str
    source: str = "manual"

    def to_document(self) -> Document:
        content = f"问题：{self.question}\n答案：{self.answer}"
        return Document(
            id=self.id,
            title=self.question[:50],
            content=content,
            source="qa",
            char_count=len(content),
        )


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    content: str
    char_start: int
    char_end: int
    token_count: int

