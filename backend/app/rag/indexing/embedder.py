"""BGE-M3 embedder with fast local-first fallback."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import List

import numpy as np

from backend.app.rag.model_loading import resolve_model_source

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "auto", local_only: bool = True):
        self.model_name = model_name
        self.device = device
        self.local_only = local_only
        self.dim = 1024
        self._model = None
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
            from sentence_transformers import SentenceTransformer

            device = self.device
            if device == "auto":
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"

            self._model = SentenceTransformer(
                model_source,
                device=device,
                local_files_only=self.local_only,
            )
            self.dim = self._model.get_sentence_embedding_dimension()
            if not self._ready_logged:
                logger.info(
                    "Embedder ready: model=%s local_only=%s fallback=%s device=%s",
                    self.model_name,
                    self.local_only,
                    self._use_fallback,
                    device,
                )
                self._ready_logged = True
        except Exception as exc:  # pragma: no cover - depends on local model state
            self._activate_fallback(str(exc))

    def _activate_fallback(self, reason: str) -> None:
        self._use_fallback = True
        self.dim = 1024
        self._fallback_reason = reason
        if not self._fallback_logged:
            logger.warning(
                "Embedder fallback enabled: model=%s local_only=%s reason=%s",
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

    def warmup(self) -> None:
        self._ensure_model()

    def _encode_fallback(self, texts: List[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            tokens = re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text.lower())
            if not tokens:
                vectors[row, 0] = 1.0
                continue

            for token in tokens:
                digest = hashlib.md5(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "little") % self.dim
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vectors[row, index] += sign

            norm = np.linalg.norm(vectors[row])
            if norm > 0:
                vectors[row] /= norm
            else:
                vectors[row, 0] = 1.0
        return vectors

    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        self._ensure_model()
        if self._use_fallback:
            return self._encode_fallback(texts)
        vectors = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=(len(texts) > 100),
        )
        return np.asarray(vectors, dtype=np.float32)

    def encode_query(self, query: str) -> np.ndarray:
        self._ensure_model()
        if self._use_fallback:
            return self._encode_fallback([query]).flatten()
        vec = self._model.encode(
            [query],
            normalize_embeddings=True,
        )
        return np.asarray(vec, dtype=np.float32).flatten()
