"""Unit tests for KeywordRetriever."""

import pytest

from backend.app.rag.retrieval.keyword_retriever import KeywordRetriever


def make_metadata(chunks: list[str]) -> dict[int, dict]:
    return {
        i: {
            "chunk_id": f"chunk_{i:03d}",
            "doc_id": f"doc_{i // 2:03d}",
            "content": text,
        }
        for i, text in enumerate(chunks)
    }


def test_empty_metadata_returns_empty():
    retriever = KeywordRetriever({})
    assert retriever.size == 0
    assert retriever.retrieve("test", k=5) == []


def test_retrieve_returns_top_k():
    metadata = make_metadata([
        "Transformer 是一种基于自注意力机制的深度学习架构。",
        "CNN 在图像处理领域表现优异。",
        "Transformer 架构的核心是自注意力机制和多头注意力。",
        "RNN 适合处理序列数据。",
    ])
    retriever = KeywordRetriever(metadata)
    assert retriever.size == 4

    results = retriever.retrieve("Transformer 注意力机制", k=2)
    assert len(results) == 2

    # 最相关的结果应该是 chunk_0 或 chunk_2（包含 Transformer 和注意力）
    top_chunk_ids = {r.chunk_id for r in results}
    assert "chunk_000" in top_chunk_ids or "chunk_002" in top_chunk_ids


def test_retrieve_k_larger_than_corpus():
    metadata = make_metadata(["文档 A", "文档 B"])
    retriever = KeywordRetriever(metadata)
    results = retriever.retrieve("文档", k=10)
    assert len(results) == 2


def test_retrieve_empty_query_returns_empty():
    metadata = make_metadata(["文档 A", "文档 B"])
    retriever = KeywordRetriever(metadata)
    results = retriever.retrieve("   ", k=5)
    # jieba 分词后可能返回空 tokens
    assert len(results) == 0


def test_retrieve_scores_descending():
    metadata = make_metadata([
        "深度学习是机器学习的一个分支。",
        "机器学习是人工智能的核心技术。",
    ])
    retriever = KeywordRetriever(metadata)
    results = retriever.retrieve("深度学习", k=2)
    assert len(results) == 2
    # 分数应该降序排列
    assert results[0].score >= results[1].score
