"""Resilience tests for offline-friendly fallback paths."""

import sys
import types
from types import SimpleNamespace

import numpy as np
import pytest

from backend.app.core.config import Settings
from backend.app.core.exceptions import ServiceUnavailableError
from backend.app.rag.indexing.embedder import Embedder
from backend.app.rag.retrieval.reranker import Reranker
from backend.app.rag.retrieval.retriever import SearchResult
from backend.app.services.evaluation_service import DEFAULT_TEST_QUESTIONS, EvaluationService


def test_embedder_falls_back_when_model_load_fails(monkeypatch):
    fake_module = types.ModuleType("sentence_transformers")

    class BrokenSentenceTransformer:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("offline")

    fake_module.SentenceTransformer = BrokenSentenceTransformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)

    embedder = Embedder(model_name="broken-model", device="cpu")
    vectors = embedder.encode(["RAG test", "RAG test", "another test"])

    assert vectors.shape == (3, 1024)
    assert np.allclose(vectors[0], vectors[1])
    assert not np.allclose(vectors[0], vectors[2])


def test_evaluation_service_uses_local_fallback_without_api_key(tmp_path):
    settings = Settings()
    settings.storage_dir = tmp_path
    settings.openai_api_key = ""
    settings.human_scores_path.parent.mkdir(parents=True, exist_ok=True)
    settings.human_scores_path.write_text(
        '[{"question_id":"eval_999","question":"old","answer":"old","correctness":1,"completeness":1,"fluency":1}]',
        encoding="utf-8",
    )

    class FakeRagService:
        index_ready = True

        @staticmethod
        def retrieve_results(question: str, top_k: int):
            return [SimpleNamespace(chunk_id=f"{question}-{top_k}")]

        @staticmethod
        def build_context(results):
            return "RAG 是检索增强生成技术，用于结合检索结果与大模型回答。"

    service = EvaluationService(settings, FakeRagService())
    reports = service.run_evaluation()

    assert reports["auto_report"].startswith("生成模式: fallback-local")
    assert reports["human_score_count"] == len(DEFAULT_TEST_QUESTIONS)
    assert settings.auto_eval_report_path.exists()
    assert settings.human_eval_report_path.exists()
    assert "eval_999" not in settings.human_scores_path.read_text(encoding="utf-8")


def test_evaluation_service_raises_when_llm_call_fails_with_api_key(tmp_path):
    settings = Settings()
    settings.storage_dir = tmp_path
    settings.openai_api_key = "dummy-key"

    class FakeRagService:
        index_ready = True

        @staticmethod
        def retrieve_results(question: str, top_k: int):
            return [SimpleNamespace(chunk_id=f"{question}-{top_k}")]

        @staticmethod
        def build_context(results):
            return "可用上下文"

        @staticmethod
        def generate_answer(mode: str, question: str, context: str, temperature: float):
            raise RuntimeError("provider down")

    service = EvaluationService(settings, FakeRagService())

    with pytest.raises(ServiceUnavailableError) as exc_info:
        service.run_evaluation()

    assert "模型调用失败" in str(exc_info.value)


def test_reranker_falls_back_to_original_order(monkeypatch):
    flag_module = types.ModuleType("FlagEmbedding")
    sentence_module = types.ModuleType("sentence_transformers")

    class BrokenFlagReranker:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("offline")

    class BrokenCrossEncoder:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("offline")

    flag_module.FlagReranker = BrokenFlagReranker
    sentence_module.CrossEncoder = BrokenCrossEncoder
    monkeypatch.setitem(sys.modules, "FlagEmbedding", flag_module)
    monkeypatch.setitem(sys.modules, "sentence_transformers", sentence_module)

    results = [
        SearchResult(chunk_id="c1", doc_id="d1", content="one", score=0.8),
        SearchResult(chunk_id="c2", doc_id="d2", content="two", score=0.6),
    ]
    reranker = Reranker(model_name="broken-reranker")
    reranked = reranker.rerank("test", results)

    assert [item.chunk_id for item in reranked] == ["c1", "c2"]
    assert reranked[0].score == 0.8
