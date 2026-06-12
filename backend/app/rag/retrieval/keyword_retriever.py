"""BM25 keyword retriever."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

import jieba
from rank_bm25 import BM25Okapi

from backend.app.rag.retrieval.retriever import SearchResult

logger = logging.getLogger(__name__)


@dataclass
class _ChunkRecord:
    internal_id: int
    chunk_id: str
    doc_id: str
    content: str


class KeywordRetriever:
    """基于 BM25 的关键词检索器。

    从 VectorStore.metadata 读取全量 chunk，用 jieba 分词后构建 BM25 索引。
    返回类型与 Retriever 一致（List[SearchResult]），可无缝接入 QA 链路。
    """

    def __init__(self, metadata: Dict[int, dict]):
        self._records: List[_ChunkRecord] = []
        self._bm25: BM25Okapi | None = None
        self._corpus: List[List[str]] = []

        if not metadata:
            logger.warning("KeywordRetriever: metadata 为空，BM25 索引将不会构建")
            return

        for internal_id, meta in metadata.items():
            content = meta.get("content", "")
            if not content or not content.strip():
                continue
            self._records.append(
                _ChunkRecord(
                    internal_id=int(internal_id),
                    chunk_id=meta.get("chunk_id", ""),
                    doc_id=meta.get("doc_id", ""),
                    content=content,
                )
            )

        if self._records:
            self._corpus = [_tokenize(record.content) for record in self._records]
            self._bm25 = BM25Okapi(self._corpus)
            logger.info(
                "KeywordRetriever ready: chunks=%d vocab_size=unknown",
                len(self._records),
            )
        else:
            logger.warning("KeywordRetriever: 没有有效的 chunk，BM25 索引为空")

    @property
    def size(self) -> int:
        return len(self._records)

    def retrieve(self, query: str, k: int = 5) -> List[SearchResult]:
        if self._bm25 is None or not self._records:
            return []

        tokens = _tokenize(query)
        if not tokens:
            return []

        scores = self._bm25.get_scores(tokens)
        k = min(k, len(scores))
        if k == 0:
            return []

        top_indices = scores.argsort()[::-1][:k]

        results: List[SearchResult] = []
        for idx in top_indices:
            score = float(scores[idx])
            rec = self._records[idx]
            results.append(
                SearchResult(
                    chunk_id=rec.chunk_id,
                    doc_id=rec.doc_id,
                    content=rec.content,
                    score=round(score, 4),
                )
            )
        return results


def _tokenize(text: str) -> List[str]:
    """中文用 jieba 分词，英文保留原词，过滤空白 token。"""
    tokens: List[str] = []
    for token in jieba.cut(text):
        stripped = token.strip()
        if stripped:
            tokens.append(stripped)
    return tokens
