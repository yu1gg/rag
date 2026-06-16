"""Dense retriever."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from backend.app.rag.indexing.embedder import Embedder
from backend.app.rag.indexing.vector_store import VectorStore


@dataclass
class SearchResult:
    chunk_id: str
    doc_id: str
    content: str
    score: float
    doc_title: str = ""
    source: str = ""
    url: str = ""
    date: str = ""


class Retriever:
    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        self.embedder = embedder
        self.store = vector_store

    def encode_query(self, query: str):
        return self.embedder.encode_query(query)

    def search_vector(self, query_vec, k: int = 5):
        return self.store.search(query_vec, k=k)

    def hydrate_results(self, raw_results) -> List[SearchResult]:
        results = []
        for internal_id, score in raw_results:
            meta = self.store.metadata.get(internal_id, {})
            results.append(
                SearchResult(
                    chunk_id=meta.get("chunk_id", ""),
                    doc_id=meta.get("doc_id", ""),
                    content=meta.get("content", ""),
                    score=score,
                    doc_title=meta.get("doc_title", ""),
                    source=meta.get("source", ""),
                    url=meta.get("url", ""),
                    date=meta.get("date", ""),
                )
            )
        return results

    def retrieve(self, query: str, k: int = 5) -> List[SearchResult]:
        query_vec = self.encode_query(query)
        raw_results = self.search_vector(query_vec, k=k)
        return self.hydrate_results(raw_results)
