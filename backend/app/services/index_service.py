"""Vector index build and status service."""

from functools import lru_cache

from backend.app.core.config import Settings, settings
from backend.app.core.exceptions import ServiceUnavailableError
from backend.app.rag.data.io import load_chunks
from backend.app.rag.indexing.embedder import Embedder
from backend.app.rag.indexing.vector_store import VectorStore


class IndexService:
    def __init__(self, app_settings: Settings):
        self.settings = app_settings

    def build_index(self) -> dict:
        chunks = load_chunks(self.settings.chunks_path)
        if not chunks:
            raise ServiceUnavailableError("未找到分块数据，请先运行 chunk_data")

        chunk_ids = [chunk.chunk_id for chunk in chunks]
        contents = [chunk.content for chunk in chunks]
        doc_ids = [chunk.doc_id for chunk in chunks]

        embedder = Embedder(
            model_name=self.settings.embedding_model,
            device=self.settings.embedding_device,
        )
        vectors = embedder.encode(contents, batch_size=self.settings.embedding_batch_size)

        store = VectorStore(dim=embedder.dim)
        store.add(chunk_ids, vectors, contents, doc_ids)
        store.save(self.settings.faiss_index_path, self.settings.chunk_meta_path)
        return self.index_status()

    def index_status(self) -> dict:
        if not self.settings.index_ready:
            return {
                "index_ready": False,
                "vector_count": 0,
                "metadata_count": 0,
            }

        store = VectorStore()
        store.load(self.settings.faiss_index_path, self.settings.chunk_meta_path)
        return {
            "index_ready": True,
            "vector_count": store.size,
            "metadata_count": len(store.metadata),
        }


@lru_cache(maxsize=1)
def get_index_service() -> IndexService:
    return IndexService(settings)

