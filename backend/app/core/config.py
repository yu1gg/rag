"""后端配置读取与路径约定。

这里统一把 `.env` 中的配置项转换成 Python 可用的 settings 对象，
并集中维护后端运行时依赖的目录和产物路径，避免业务代码里到处散落字符串常量。
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# `backend/` 作为配置和存储路径的根目录，后续所有相对路径都从这里展开。
BACKEND_ROOT = Path(__file__).resolve().parents[2]
# Ver 2.0 明确只读取 `backend/.env`，不再兼容旧版 YAML 配置。
ENV_FILE = BACKEND_ROOT / ".env"

load_dotenv(ENV_FILE, override=False)


def _env(name: str, default: str = "") -> str:
    """读取字符串配置，并把空字符串视为未配置。"""
    value = os.getenv(name)
    return value if value not in (None, "") else default


def _env_int(name: str, default: int) -> int:
    """读取整数配置，非法值时回退到默认值，避免启动阶段直接崩掉。"""
    raw = _env(name, str(default))
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    """读取浮点配置，非法值时使用默认值。"""
    raw = _env(name, str(default))
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    """统一兼容常见布尔写法，例如 1/true/yes/on。"""
    raw = _env(name, "true" if default else "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _resolve_dir(path_value: str) -> Path:
    """把相对路径解析到 `backend/` 下，保证脚本和服务入口行为一致。"""
    path = Path(path_value)
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    return path.resolve()


class Settings:
    """集中承载运行配置。

    这个对象在进程内通常只实例化一次，业务代码通过 `from ... import settings`
    直接复用即可，不需要反复自己读环境变量。
    """

    def __init__(self) -> None:
        self.backend_root = BACKEND_ROOT

        # 应用基础信息：主要用于服务启动、文档展示和前端联调地址。
        self.app_name = _env("APP_NAME", "RAG 智能问答与文本摘要系统 API")
        self.app_version = _env("APP_VERSION", "2.0.0")
        self.app_host = _env("APP_HOST", "127.0.0.1")
        self.app_port = _env_int("APP_PORT", 8050)
        self.api_prefix = _env("API_PREFIX", "/api/v1")
        self.allowed_origins = self._parse_origins(_env("ALLOWED_ORIGINS", "*"))

        # LLM 配置：问答和摘要都会走这里，QA 再额外使用更小的 token 上限。
        self.openai_api_key = _env("OPENAI_API_KEY", "")
        self.openai_base_url = _env("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
        self.openai_model = _env("OPENAI_MODEL", "deepseek-chat")
        self.openai_timeout = _env_int("OPENAI_TIMEOUT", 20)
        self.openai_retries = _env_int("OPENAI_RETRIES", 1)
        self.openai_temperature = _env_float("OPENAI_TEMPERATURE", 0.7)
        self.openai_max_tokens = _env_int("OPENAI_MAX_TOKENS", 2048)
        self.qa_max_tokens = _env_int("QA_MAX_TOKENS", 512)

        # 检索模型配置：默认走“本地优先 + 快速降级”，避免首问卡在远程探测上。
        self.embedding_model = _env("EMBEDDING_MODEL", "BAAI/bge-m3")
        self.embedding_device = _env("EMBEDDING_DEVICE", "auto")
        self.embedding_batch_size = _env_int("EMBEDDING_BATCH_SIZE", 32)
        self.model_local_only = _env_bool("MODEL_LOCAL_ONLY", True)
        self.prewarm_rag_on_startup = _env_bool("PREWARM_RAG_ON_STARTUP", True)

        # 检索策略配置：这里控制召回数量、是否启用重排，以及 QA 注入 LLM 的上下文体积。
        self.retrieval_top_k = _env_int("RETRIEVAL_TOP_K", 5)
        self.rerank_enabled = _env_bool("RERANK_ENABLED", False)
        self.reranker_model = _env("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
        self.qa_context_top_k = _env_int("QA_CONTEXT_TOP_K", 3)
        self.qa_context_max_chars = _env_int("QA_CONTEXT_MAX_CHARS", 1600)

        # 数据准备与评估配置：供脚本链路使用，而不是直接给在线接口消费。
        self.arxiv_max_results = _env_int("ARXIV_MAX_RESULTS", 50)
        self.arxiv_query = _env(
            "ARXIV_QUERY",
            "deep learning natural language processing machine learning transformer BERT GPT",
        )
        self.news_max_articles = _env_int("NEWS_MAX_ARTICLES", 30)
        self.qa_min_pairs = _env_int("QA_MIN_PAIRS", 200)
        self.chunk_size = _env_int("CHUNK_SIZE", 512)
        self.chunk_overlap = _env_int("CHUNK_OVERLAP", 128)
        self.min_chunk_length = _env_int("MIN_CHUNK_LENGTH", 20)

        # 统一运行期产物目录；无论从 API 还是脚本入口进入，都写到同一套 storage 中。
        self.storage_dir = _resolve_dir(_env("STORAGE_DIR", "storage"))

    @staticmethod
    def _parse_origins(raw: str) -> list[str]:
        """把逗号分隔的 CORS 配置解析成列表。"""
        if raw.strip() == "*":
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]

    # 下面这些 property 统一维护存储目录结构。
    # 做成 property 而不是散落常量，后续如果目录结构调整，只需要改这一处。
    @property
    def raw_dir(self) -> Path:
        return self.storage_dir / "raw"

    @property
    def materials_dir(self) -> Path:
        return self.storage_dir / "materials"

    @property
    def processed_dir(self) -> Path:
        return self.storage_dir / "processed"

    @property
    def index_dir(self) -> Path:
        return self.storage_dir / "index"

    @property
    def eval_dir(self) -> Path:
        return self.storage_dir / "eval"

    @property
    def faiss_index_path(self) -> Path:
        return self.index_dir / "faiss.index"

    @property
    def chunk_meta_path(self) -> Path:
        return self.index_dir / "chunk_meta.json"

    @property
    def documents_path(self) -> Path:
        return self.raw_dir / "documents.json"

    @property
    def qa_pairs_path(self) -> Path:
        return self.raw_dir / "qa_pairs.json"

    @property
    def chunks_path(self) -> Path:
        return self.processed_dir / "chunks.json"

    @property
    def auto_eval_report_path(self) -> Path:
        return self.eval_dir / "auto_eval_report.txt"

    @property
    def human_scores_path(self) -> Path:
        return self.eval_dir / "human_scores.json"

    @property
    def human_eval_report_path(self) -> Path:
        return self.eval_dir / "human_eval_report.txt"

    @property
    def index_ready(self) -> bool:
        # 健康检查和预热都依赖这个快速判断，避免每次都尝试真正加载索引。
        return self.faiss_index_path.exists() and self.chunk_meta_path.exists()


settings = Settings()
