"""FAISS-backed vector store."""

import json
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np


class VectorStore:
    def __init__(self, dim: int = 1024):
        import faiss

        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.metadata: dict = {}

    @property
    def size(self) -> int:
        return self.index.ntotal

    def add(
        self,
        chunk_ids: List[str],
        vectors: np.ndarray,
        contents: List[str],
        doc_ids: List[str],
        doc_titles: List[str] | None = None,
        sources: List[str] | None = None,
        urls: List[str] | None = None,
        dates: List[str] | None = None,
    ):
        if vectors.shape[0] == 0:
            return

        vectors = np.asarray(vectors, dtype=np.float32)
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        start_id = self.index.ntotal
        self.index.add(vectors)

        for i, (chunk_id, content, doc_id) in enumerate(zip(chunk_ids, contents, doc_ids)):
            meta = {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "content": content,
            }
            if doc_titles:
                meta["doc_title"] = doc_titles[i]
            if sources:
                meta["source"] = sources[i]
            if urls:
                meta["url"] = urls[i]
            if dates:
                meta["date"] = dates[i]
            self.metadata[start_id + i] = meta

    def search(self, query_vec: np.ndarray, k: int = 5) -> List[Tuple[int, float]]:
        if self.index.ntotal == 0:
            return []
        query_vec = np.asarray(query_vec, dtype=np.float32).reshape(1, -1)
        k = min(k, self.index.ntotal)
        scores, indices = self.index.search(query_vec, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx in self.metadata:
                results.append((int(idx), float(score)))
        return results

    def save(self, index_path: str, meta_path: str):
        import faiss

        path = Path(index_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path))

        meta = Path(meta_path)
        meta.parent.mkdir(parents=True, exist_ok=True)
        with open(meta, "w", encoding="utf-8") as handle:
            json.dump(self.metadata, handle, ensure_ascii=False, indent=2)

    def load(self, index_path: str, meta_path: str):
        import faiss

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"索引文件不存在: {index_path}")

        self.index = faiss.read_index(str(index_path))
        self.dim = self.index.d
        with open(meta_path, "r", encoding="utf-8") as handle:
            metadata = json.load(handle)
        self.metadata = {int(key): value for key, value in metadata.items()}

