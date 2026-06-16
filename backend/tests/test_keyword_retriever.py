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
    # 需要足够多的文档让 BM25 的 IDF 有意义（ATIRE 公式下，词频=文档数/2 时 idf=0）
    docs = []
    for i in range(20):
        docs.append(f"这是第{i}号无关文档，包含一些通用词汇。")
    docs[0] = "Transformer 是一种基于自注意力机制的深度学习架构。"
    docs[1] = "CNN 在图像处理领域表现优异。"
    docs[2] = "Transformer 架构的核心是自注意力机制和多头注意力。"
    metadata = make_metadata(docs)
    retriever = KeywordRetriever(metadata)
    assert retriever.size == 20

    results = retriever.retrieve("Transformer 注意力机制", k=2)
    assert len(results) >= 1
    top_chunk_ids = {r.chunk_id for r in results}
    assert "chunk_000" in top_chunk_ids or "chunk_002" in top_chunk_ids


def test_retrieve_k_larger_than_corpus():
    docs = [f"文档内容{i}" for i in range(15)]
    docs[3] = "包含关键词的特殊文档"
    docs[7] = "另一个包含关键词的文档"
    metadata = make_metadata(docs)
    retriever = KeywordRetriever(metadata)
    results = retriever.retrieve("关键词", k=10)
    assert 1 <= len(results) <= 2  # 只有 2 个文档含有关键词


def test_retrieve_empty_query_returns_empty():
    metadata = make_metadata(["文档 A", "文档 B"])
    retriever = KeywordRetriever(metadata)
    results = retriever.retrieve("   ", k=5)
    # jieba 分词后可能返回空 tokens
    assert len(results) == 0


def test_retrieve_scores_normalized():
    docs = [f"无关文档{i}" for i in range(20)]
    docs[3] = "深度学习是机器学习的一个分支。"
    docs[7] = "机器学习是人工智能的核心技术，也涉及深度学习。"
    metadata = make_metadata(docs)
    retriever = KeywordRetriever(metadata)
    results = retriever.retrieve("深度学习", k=5)
    assert len(results) >= 1
    # 最高分归一化为 1.0
    assert results[0].score == 1.0
