"""Chunk text with sliding window strategy."""

import re

from backend.app.rag.data.models import Chunk, Document


class Chunker:
    CHARS_PER_TOKEN = 1.5

    def __init__(self, chunk_size: int = 512, overlap: int = 128):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._chunk_chars = int(chunk_size * self.CHARS_PER_TOKEN)
        self._overlap_chars = int(overlap * self.CHARS_PER_TOKEN)

    def _count_tokens(self, text: str) -> int:
        try:
            import tiktoken

            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception:
            return int(len(text) / self.CHARS_PER_TOKEN)

    def chunk(self, doc: Document) -> list[Chunk]:
        paragraphs = _split_paragraphs(doc.content, min_len=10)
        if not paragraphs:
            return []

        chunks = []
        current_text = ""
        current_char_start = 0
        chunk_idx = 0

        for para_text, para_start in paragraphs:
            tentative = current_text + ("\n\n" if current_text else "") + para_text

            if self._count_tokens(tentative) <= self.chunk_size:
                current_text = tentative
                continue

            if current_text.strip():
                token_count = self._count_tokens(current_text)
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc.id}_chunk_{chunk_idx:04d}",
                        doc_id=doc.id,
                        content=current_text.strip(),
                        char_start=current_char_start,
                        char_end=current_char_start + len(current_text),
                        token_count=token_count,
                    )
                )
                chunk_idx += 1

            if self._overlap_chars > 0 and current_text:
                overlap_text = current_text[-self._overlap_chars :]
                cut_idx = overlap_text.find("\n\n")
                if cut_idx > 0:
                    overlap_text = overlap_text[cut_idx + 2 :]
                current_text = overlap_text + "\n\n" + para_text if overlap_text else para_text
                current_char_start = para_start
            else:
                current_text = para_text
                current_char_start = para_start

        if current_text.strip():
            token_count = self._count_tokens(current_text)
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.id}_chunk_{chunk_idx:04d}",
                    doc_id=doc.id,
                    content=current_text.strip(),
                    char_start=current_char_start,
                    char_end=current_char_start + len(current_text),
                    token_count=token_count,
                )
            )

        return chunks

    def chunk_all(self, docs: list[Document]) -> list[Chunk]:
        all_chunks = []
        global_idx = 0
        for doc in docs:
            doc_chunks = self.chunk(doc)
            for chunk in doc_chunks:
                chunk.chunk_id = f"chunk_{global_idx:06d}"
                global_idx += 1
            all_chunks.extend(doc_chunks)
        return all_chunks


def _split_paragraphs(text: str, min_len: int = 10) -> list[tuple[str, int]]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = []
    pos = 0
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if len(para) >= min_len:
            start = text.find(para, pos) if pos < len(text) else pos
            paragraphs.append((para, max(start, pos)))
            pos = start + len(para)
    return paragraphs

