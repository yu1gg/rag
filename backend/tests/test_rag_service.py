"""Tests for RAG service caching and QA context limiting behavior."""

from __future__ import annotations

import time
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.services import rag_service as rag_service_module
from backend.app.services.rag_service import RagService


class DummyEmbedder:
    def __init__(self, *args, **kwargs):
        pass


class FakeVectorStore:
    load_calls: list[str] = []

    def __init__(self):
        self.loaded_marker = ""

    def load(self, index_path: str, meta_path: str) -> None:
        self.loaded_marker = Path(meta_path).read_text(encoding="utf-8")
        self.__class__.load_calls.append(self.loaded_marker)


class FakeRetriever:
    def __init__(self, embedder, store):
        self.store = store

    def encode_query(self, question: str):
        return question

    def search_vector(self, query_vec, k: int = 5):
        return [(0, 1.0)]

    def hydrate_results(self, raw_results):
        return [
            rag_service_module.SearchResult(
                chunk_id=self.store.loaded_marker,
                doc_id="doc_001",
                content="content",
                score=1.0,
            )
        ]


class FakePromptTemplate:
    def __init__(self):
        self.last_context = ""
        self.last_mode = ""
        self.last_question = ""

    def format_context(self, results):
        self.last_context = "||".join(result.content for result in results)
        return self.last_context

    def format_prompt(self, mode: str, question: str, context: str) -> str:
        self.last_mode = mode
        self.last_question = question
        self.last_context = context
        return f"{mode}:{question}:{context}"


class FakeLLM:
    def __init__(self):
        self.calls: list[dict] = []

    def answer(self, prompt: str, **kwargs) -> str:
        self.calls.append({"prompt": prompt, **kwargs})
        return "mock-answer"

    def summarize_long_text(self, text: str) -> str:
        return "mock-summary"


def test_rag_service_reloads_index_when_files_change(tmp_path, monkeypatch):
    settings = Settings()
    settings.storage_dir = tmp_path
    settings.rerank_enabled = False

    settings.index_dir.mkdir(parents=True, exist_ok=True)
    settings.faiss_index_path.write_text("index-v1", encoding="utf-8")
    settings.chunk_meta_path.write_text("meta-v1", encoding="utf-8")

    FakeVectorStore.load_calls = []
    monkeypatch.setattr(rag_service_module, "VectorStore", FakeVectorStore)
    monkeypatch.setattr(rag_service_module, "Retriever", FakeRetriever)
    monkeypatch.setattr(rag_service_module, "Embedder", DummyEmbedder)

    service = RagService(settings)

    first = service.retrieve_results("question", top_k=1)
    time.sleep(0.02)
    settings.faiss_index_path.write_text("index-v2-updated", encoding="utf-8")
    settings.chunk_meta_path.write_text("meta-v2-updated", encoding="utf-8")
    second = service.retrieve_results("question", top_k=1)

    assert first[0].chunk_id == "meta-v1"
    assert second[0].chunk_id == "meta-v2-updated"
    assert FakeVectorStore.load_calls == ["meta-v1", "meta-v2-updated"]


def test_qa_uses_limited_context_but_returns_full_references():
    settings = Settings()
    settings.rerank_enabled = False
    settings.qa_context_top_k = 3
    settings.qa_context_max_chars = 1600
    settings.qa_max_tokens = 512

    service = RagService(settings)
    prompt_template = FakePromptTemplate()
    llm = FakeLLM()
    service._prompts = prompt_template
    service._llm = llm

    results = [
        rag_service_module.SearchResult(
            chunk_id=f"chunk_{index}",
            doc_id=f"doc_{index}",
            content=f"content-{index}-" + ("x" * 600),
            score=1.0 - index * 0.1,
        )
        for index in range(5)
    ]

    service._retrieve_results_with_metrics = lambda question, top_k: (results, {})  # type: ignore[method-assign]

    response = service.answer_question("什么是RAG", top_k=5, temperature=0.7)

    assert response["answer"] == "mock-answer"
    assert len(response["references"]) == 5
    assert "content-0-" in prompt_template.last_context
    assert "content-1-" in prompt_template.last_context
    assert "content-2-" in prompt_template.last_context
    assert "content-3-" not in prompt_template.last_context
    assert len(prompt_template.last_context) <= settings.qa_context_max_chars + 16
    assert llm.calls[0]["max_tokens"] == settings.qa_max_tokens
