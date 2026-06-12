"""RAG 主服务编排层。

这一层不关心 HTTP，也不直接处理前端页面，而是把"索引加载、检索、重排、提示词构造、
LLM 调用、结果格式化"这些步骤串成统一服务，供路由层直接调用。
"""

from __future__ import annotations

import logging
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from time import perf_counter

from backend.app.core.config import Settings, settings
from backend.app.core.exceptions import ConfigError, ServiceUnavailableError
from backend.app.rag.generation.llm_client import LLMClient
from backend.app.rag.generation.prompts import PromptTemplate
from backend.app.rag.indexing.embedder import Embedder
from backend.app.rag.indexing.vector_store import VectorStore
from backend.app.rag.retrieval.keyword_retriever import KeywordRetriever
from backend.app.rag.retrieval.reranker import Reranker
from backend.app.rag.retrieval.retriever import Retriever, SearchResult

logger = logging.getLogger(__name__)


class RagService:
    """封装 RAG 检索与生成链路。

    这里把重量级组件都做成懒加载缓存，原因是：
    1. 启动阶段不必一次性加载全部模型，避免无谓的冷启动开销。
    2. 同一进程内后续请求可以复用实例，减少重复初始化成本。
    """

    def __init__(self, app_settings: Settings):
        self.settings = app_settings
        self._store: VectorStore | None = None
        self._embedder: Embedder | None = None
        self._retriever: Retriever | None = None
        self._keyword_retriever: KeywordRetriever | None = None
        self._reranker: Reranker | None = None
        self._prompts: PromptTemplate | None = None
        self._llm: LLMClient | None = None
        self._loaded_index_signature: tuple | None = None
        self._prewarm_summary: dict | None = None

    @property
    def index_ready(self) -> bool:
        return self.settings.index_ready

    def _ensure_index(self) -> None:
        # 索引是检索链路的基础依赖。缺失时直接抛服务不可用，而不是继续往下走。
        if not self.index_ready:
            raise ServiceUnavailableError("索引尚未就绪，请先准备 backend/storage/index 下的索引文件")

        current_signature = self._get_index_signature()
        # 当索引文件发生变化时自动重新加载，避免服务重启前一直拿旧索引回答。
        if self._store is None or self._loaded_index_signature != current_signature:
            store = VectorStore()
            store.load(
                str(self.settings.faiss_index_path),
                str(self.settings.chunk_meta_path),
            )
            self._store = store
            self._retriever = None
            self._loaded_index_signature = current_signature

    def _get_index_signature(self) -> tuple:
        # 用"路径 + 修改时间 + 文件大小"作为轻量签名，足够判断索引是否已经更新。
        def stat_key(path: Path) -> tuple:
            stat = path.stat()
            return (str(path), stat.st_mtime_ns, stat.st_size)

        return (
            stat_key(self.settings.faiss_index_path),
            stat_key(self.settings.chunk_meta_path),
        )

    def _get_embedder(self) -> Embedder:
        if self._embedder is None:
            # `local_only` 默认开启，优先避免首问卡在 Hugging Face 远程探测上。
            self._embedder = Embedder(
                model_name=self.settings.embedding_model,
                device=self.settings.embedding_device,
                local_only=self.settings.model_local_only,
            )
        return self._embedder

    def _get_retriever(self) -> Retriever:
        self._ensure_index()
        if self._retriever is None:
            self._retriever = Retriever(self._get_embedder(), self._store)
        return self._retriever

    def _get_keyword_retriever(self) -> KeywordRetriever:
        self._ensure_index()
        if self._keyword_retriever is None:
            self._keyword_retriever = KeywordRetriever(self._store.metadata)
        return self._keyword_retriever

    def _get_reranker(self) -> Reranker | None:
        # 当前默认关闭 rerank，优先换取响应速度；需要更高排序质量时可再开启。
        if not self.settings.rerank_enabled:
            return None
        if self._reranker is None:
            self._reranker = Reranker(
                model_name=self.settings.reranker_model,
                local_only=self.settings.model_local_only,
            )
        return self._reranker

    def _get_prompts(self) -> PromptTemplate:
        if self._prompts is None:
            self._prompts = PromptTemplate()
        return self._prompts

    def _get_llm(self) -> LLMClient:
        # LLM 相关能力允许晚一点失败，这样纯检索接口在没有 API Key 时仍可工作。
        if not self.settings.openai_api_key:
            raise ConfigError("缺少 OPENAI_API_KEY，无法调用问答或摘要服务")
        if self._llm is None:
            config = {
                "llm": {
                    "api_key": self.settings.openai_api_key,
                    "base_url": self.settings.openai_base_url,
                    "model": self.settings.openai_model,
                    "timeout": self.settings.openai_timeout,
                    "retries": self.settings.openai_retries,
                    "temperature": self.settings.openai_temperature,
                    "max_tokens": self.settings.openai_max_tokens,
                }
            }
            self._llm = LLMClient(config)
        return self._llm

    def prewarm_for_serving(self) -> dict:
        """在服务启动阶段预热检索链路。

        这里故意不预热外部 LLM：
        - 预热索引 / embedding / reranker 可以明显降低首问冷启动成本。
        - 但如果启动时就探测外部 LLM，会把网络抖动变成"服务起不来"的问题。
        """

        if self._prewarm_summary is not None:
            return self._prewarm_summary

        summary = {
            "index_ready": self.index_ready,
            "index_load_s": 0.0,
            "embedder_warmup_s": 0.0,
            "embedding_fallback": None,
            "rerank_enabled": self.settings.rerank_enabled,
            "reranker_warmup_s": 0.0,
            "reranker_backend": "disabled",
            "reranker_fallback": None,
            "status": "ok",
        }

        if not self.index_ready:
            summary["status"] = "skipped:index_missing"
            return summary

        t0 = perf_counter()
        self._ensure_index()
        summary["index_load_s"] = round(perf_counter() - t0, 4)

        embedder = self._get_embedder()
        t0 = perf_counter()
        embedder.warmup()
        summary["embedder_warmup_s"] = round(perf_counter() - t0, 4)
        summary["embedding_fallback"] = embedder.is_fallback

        reranker = self._get_reranker()
        if reranker is not None:
            t0 = perf_counter()
            reranker.warmup()
            summary["reranker_warmup_s"] = round(perf_counter() - t0, 4)
            summary["reranker_backend"] = reranker.backend_name
            summary["reranker_fallback"] = reranker.is_fallback

        self._prewarm_summary = summary
        return summary

    def _retrieve_results_with_metrics(
        self, question: str, top_k: int, method: str = "vector"
    ) -> tuple[list[SearchResult], dict]:
        """执行检索并收集阶段耗时。

        这些 metrics 主要用于区分"慢在索引/嵌入/重排/LLM 哪一段"，
        后续排查性能问题时，日志能直接告诉我们瓶颈在哪。
        """

        metrics: dict[str, float | int | bool | str] = {"retrieval_method": method}

        t0 = perf_counter()
        self._ensure_index()
        metrics["index_load_s"] = round(perf_counter() - t0, 4)

        if method == "keyword":
            t0 = perf_counter()
            keyword_retriever = self._get_keyword_retriever()
            results = keyword_retriever.retrieve(question, k=top_k)
            metrics["retrieve_s"] = round(perf_counter() - t0, 4)
            metrics["embed_s"] = 0.0
        else:
            retriever = self._get_retriever()
            t0 = perf_counter()
            query_vec = retriever.encode_query(question)
            metrics["embed_s"] = round(perf_counter() - t0, 4)

            t0 = perf_counter()
            raw_results = retriever.search_vector(query_vec, k=top_k)
            metrics["retrieve_s"] = round(perf_counter() - t0, 4)
            results = retriever.hydrate_results(raw_results)

        reranker = self._get_reranker()
        metrics["rerank_enabled"] = reranker is not None
        if reranker is not None and len(results) > 1:
            t0 = perf_counter()
            results = reranker.rerank(question, results)
            metrics["rerank_s"] = round(perf_counter() - t0, 4)
            metrics["reranker_backend"] = reranker.backend_name
            metrics["reranker_fallback"] = reranker.is_fallback
        else:
            metrics["rerank_s"] = 0.0
            metrics["reranker_backend"] = "disabled" if reranker is None else reranker.backend_name
            metrics["reranker_fallback"] = False if reranker is None else reranker.is_fallback

        metrics["embedding_fallback"] = getattr(self._get_embedder(), "is_fallback", False)
        metrics["result_count"] = len(results)
        return results, metrics

    def retrieve_results(
        self, question: str, top_k: int, method: str = "vector"
    ) -> list[SearchResult]:
        results, _ = self._retrieve_results_with_metrics(question, top_k, method=method)
        return results

    def build_context(self, results: list[SearchResult]) -> str:
        return self._get_prompts().format_context(results)

    def build_qa_context(self, results: list[SearchResult]) -> tuple[str, list[SearchResult]]:
        """为 QA 构建"速度优先"的上下文。

        注意这里不会影响最终返回给前端的 references 数量。
        我们只是裁剪送给 LLM 的上下文，来控制 prompt 体积和响应时延；
        前端仍然能拿到完整 top_k 检索结果做参考展示。
        """

        limited_results: list[SearchResult] = []
        max_items = max(1, self.settings.qa_context_top_k)
        max_chars = max(200, self.settings.qa_context_max_chars)
        used_chars = 0

        for result in results[:max_items]:
            remaining = max_chars - used_chars
            if remaining <= 0:
                break

            content = result.content.strip()
            if len(content) > remaining:
                if remaining <= 3:
                    break
                content = content[: remaining - 3].rstrip() + "..."

            if not content:
                continue

            limited_results.append(replace(result, content=content))
            used_chars += len(content)

        if not limited_results and results:
            fallback_chars = max(4, max_chars)
            content = results[0].content.strip()
            if len(content) > fallback_chars:
                content = content[: fallback_chars - 3].rstrip() + "..."
            limited_results = [replace(results[0], content=content)]

        return self._get_prompts().format_context(limited_results), limited_results

    def generate_answer(
        self,
        mode: str,
        question: str,
        context: str,
        temperature: float,
        max_tokens: int | None = None,
    ) -> str:
        prompt = self._get_prompts().format_prompt(mode, question, context)
        try:
            return self._get_llm().answer(prompt, temperature=temperature, max_tokens=max_tokens)
        except RuntimeError as exc:
            # LLMClient 会把底层网络/供应商异常包装成 RuntimeError，
            # 这里统一映射为服务不可用，保持 API 对外错误语义一致。
            raise ServiceUnavailableError(str(exc)) from exc

    @staticmethod
    def _build_references(results: list[SearchResult]) -> list[dict]:
        # 对引用内容做轻量截断，避免接口返回过长文本把前端消息区撑爆。
        references = []
        for idx, result in enumerate(results, 1):
            excerpt = result.content.strip()
            if len(excerpt) > 300:
                excerpt = excerpt[:300].rstrip() + "..."
            references.append(
                {
                    "index": idx,
                    "chunk_id": result.chunk_id,
                    "doc_id": result.doc_id,
                    "score": result.score,
                    "excerpt": excerpt,
                }
            )
        return references

    def answer_question(
        self, question: str, top_k: int, temperature: float, method: str = "vector"
    ) -> dict:
        # QA 日志里单独记录完整链路耗时，方便把"检索慢"和"LLM 慢"区分开。
        total_start = perf_counter()
        results, metrics = self._retrieve_results_with_metrics(question, top_k, method=method)

        t0 = perf_counter()
        context, context_results = self.build_qa_context(results)
        metrics["prompt_build_s"] = round(perf_counter() - t0, 4)
        metrics["context_result_count"] = len(context_results)
        metrics["context_chars"] = len(context)

        t0 = perf_counter()
        answer = self.generate_answer(
            "qa",
            question,
            context,
            temperature,
            max_tokens=max(1, self.settings.qa_max_tokens),
        )
        metrics["llm_s"] = round(perf_counter() - t0, 4)
        metrics["total_s"] = round(perf_counter() - total_start, 4)
        logger.info("QA timing: question=%r metrics=%s", question[:80], metrics)

        return {
            "answer": answer,
            "references": self._build_references(results),
        }

    def summarize(self, text: str, temperature: float) -> dict:
        # 长文本摘要走 LLMClient 的专门分段逻辑，避免一次性把超长文本塞进单轮 prompt。
        llm = self._get_llm()
        try:
            if len(text) > 8000:
                summary = llm.summarize_long_text(text)
            else:
                prompt = self._get_prompts().format_prompt("summary", "", text)
                summary = llm.answer(prompt, temperature=temperature)
        except RuntimeError as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        return {"summary": summary}



@lru_cache(maxsize=1)
def get_rag_service() -> RagService:
    # 进程级单例：让 API 请求和启动预热共享同一个服务实例与内部缓存。
    return RagService(settings)
