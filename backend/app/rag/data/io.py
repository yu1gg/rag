"""JSON I/O helpers for backend storage artifacts."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from backend.app.rag.data.models import Chunk, Document, QAPair


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_documents(docs: Iterable[Document], filepath: str | Path) -> None:
    path = Path(filepath)
    _ensure_parent(path)
    data = [asdict(doc) for doc in docs]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_documents(filepath: str | Path) -> list[Document]:
    path = Path(filepath)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Document(**item) for item in data]


def save_qa_pairs(pairs: Iterable[QAPair], filepath: str | Path) -> None:
    path = Path(filepath)
    _ensure_parent(path)
    data = [asdict(pair) for pair in pairs]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_qa_pairs(filepath: str | Path) -> list[QAPair]:
    path = Path(filepath)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [QAPair(**item) for item in data]


def save_chunks(chunks: Iterable[Chunk], filepath: str | Path) -> None:
    path = Path(filepath)
    _ensure_parent(path)
    data = [asdict(chunk) for chunk in chunks]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_chunks(filepath: str | Path) -> list[Chunk]:
    path = Path(filepath)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Chunk(**item) for item in data]

