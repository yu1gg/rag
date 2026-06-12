"""Dataset preparation service for backend scripts and status APIs."""

from functools import lru_cache

from backend.app.core.config import Settings, settings
from backend.app.core.exceptions import ServiceUnavailableError
from backend.app.rag.data.chunker import Chunker
from backend.app.rag.data.cleaner import Deduplicator, TextCleaner
from backend.app.rag.data.collector import (
    ArxivCollector,
    CourseMaterialCollector,
    NewsCollector,
    QAPairCollector,
)
from backend.app.rag.data.io import (
    load_chunks,
    load_documents,
    load_qa_pairs,
    save_chunks,
    save_documents,
    save_qa_pairs,
)
from backend.app.rag.data.supplement import generate_supplement_docs


class DatasetService:
    TARGET_DOCS = 50
    TARGET_CHARS = 100000

    def __init__(self, app_settings: Settings):
        self.settings = app_settings

    def collect_data(self) -> dict:
        self.settings.raw_dir.mkdir(parents=True, exist_ok=True)
        self.settings.materials_dir.mkdir(parents=True, exist_ok=True)

        arxiv_docs = ArxivCollector(
            max_results=self.settings.arxiv_max_results,
            query=self.settings.arxiv_query,
        ).collect()
        news_docs = NewsCollector(max_articles=self.settings.news_max_articles).collect()
        course_docs = CourseMaterialCollector(self.settings.materials_dir).collect()
        qa_pairs = QAPairCollector(
            min_pairs=self.settings.qa_min_pairs,
            qa_pairs_path=self.settings.qa_pairs_path,
        ).collect()

        all_docs = arxiv_docs + news_docs + course_docs
        current_chars = sum(doc.char_count for doc in all_docs)
        if len(all_docs) < self.TARGET_DOCS or current_chars < self.TARGET_CHARS:
            shortfall_chars = max(0, self.TARGET_CHARS - current_chars)
            supplement_docs = generate_supplement_docs(shortfall_chars, len(all_docs))
            all_docs.extend(supplement_docs)

        save_documents(all_docs, self.settings.documents_path)
        save_qa_pairs(qa_pairs, self.settings.qa_pairs_path)
        return self.dataset_stats()

    def clean_data(self) -> dict:
        docs = load_documents(self.settings.documents_path)
        if not docs:
            raise ServiceUnavailableError("未找到原始文档，请先运行 collect_data")

        cleaner = TextCleaner()
        deduplicator = Deduplicator()
        docs = cleaner.clean_documents(docs)
        docs = deduplicator.deduplicate(docs)
        docs = deduplicator.filter_short(docs, min_length=self.settings.min_chunk_length)
        save_documents(docs, self.settings.documents_path)
        return self.dataset_stats()

    def chunk_data(self) -> dict:
        docs = load_documents(self.settings.documents_path)
        if not docs:
            raise ServiceUnavailableError("未找到文档，请先运行 collect_data/clean_data")

        chunker = Chunker(
            chunk_size=self.settings.chunk_size,
            overlap=self.settings.chunk_overlap,
        )
        chunks = chunker.chunk_all(docs)
        save_chunks(chunks, self.settings.chunks_path)
        return self.dataset_stats()

    def dataset_stats(self) -> dict:
        docs = load_documents(self.settings.documents_path)
        qa_pairs = load_qa_pairs(self.settings.qa_pairs_path)
        chunks = load_chunks(self.settings.chunks_path)
        return {
            "documents_count": len(docs),
            "qa_pairs_count": len(qa_pairs),
            "chunks_count": len(chunks),
            "total_document_chars": sum(doc.char_count for doc in docs),
        }


@lru_cache(maxsize=1)
def get_dataset_service() -> DatasetService:
    return DatasetService(settings)

