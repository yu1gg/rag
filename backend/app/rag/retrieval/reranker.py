"""Cross-encoder reranker with fast local-first fallback."""

from __future__ import annotations

import logging
from typing import List

from backend.app.rag.model_loading import resolve_model_source
from backend.app.rag.retrieval.retriever import SearchResult

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", local_only: bool = True):
        self.model_name = model_name
        self.local_only = local_only
        self._model = None
        self._backend = None
        self._use_fallback = False
        self._fallback_reason = ""
        self._fallback_logged = False
        self._ready_logged = False

    def _ensure_model(self) -> None:
        if self._model is not None or self._use_fallback:
            return

        model_source = resolve_model_source(self.model_name, self.local_only)
        if model_source is None:
            self._activate_fallback("local model cache not found")
            return

        try:
            from FlagEmbedding import FlagReranker
            import torch

            use_fp16 = bool(torch.cuda.is_available())
            self._model = FlagReranker(model_source, use_fp16=use_fp16)
            test_score = self._model.compute_score(["test query", "test document"])
            if isinstance(test_score, list):
                _ = test_score[0]
            self._backend = "flagembedding"
            self._log_ready()
            return
        except Exception:
            pass

        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(model_source, local_files_only=self.local_only)
            self._backend = "sentence_transformers"
            self._log_ready()
        except Exception as exc:  # pragma: no cover - depends on local model state
            self._activate_fallback(str(exc))

    def _log_ready(self) -> None:
        if not self._ready_logged:
            logger.info(
                "Reranker ready: model=%s local_only=%s backend=%s fallback=%s",
                self.model_name,
                self.local_only,
                self._backend,
                self._use_fallback,
            )
            self._ready_logged = True

    def _activate_fallback(self, reason: str) -> None:
        self._use_fallback = True
        self._backend = "fallback"
        self._fallback_reason = reason
        if not self._fallback_logged:
            logger.warning(
                "Reranker fallback enabled: model=%s local_only=%s reason=%s",
                self.model_name,
                self.local_only,
                reason,
            )
            self._fallback_logged = True

    @property
    def is_fallback(self) -> bool:
        return self._use_fallback

    @property
    def fallback_reason(self) -> str:
        return self._fallback_reason

    @property
    def backend_name(self) -> str:
        return self._backend or "uninitialized"

    def warmup(self) -> None:
        self._ensure_model()

    def rerank(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        if not results:
            return results
        if len(results) == 1:
            results[0].score = 1.0
            return results

        self._ensure_model()
        if self._use_fallback:
            return results
        pairs = [[query, result.content] for result in results]

        if self._backend == "flagembedding":
            scores = self._model.compute_score(pairs)
            if not isinstance(scores, list):
                scores = [scores]
            scores = [float(score) for score in scores]
        else:
            scores = self._model.predict(pairs, show_progress_bar=False)
            scores = [float(score) for score in scores]

        for result, score in zip(results, scores):
            result.score = score

        results.sort(key=lambda item: item.score, reverse=True)
        return results
