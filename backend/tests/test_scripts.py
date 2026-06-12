"""Tests for backend script entrypoints."""

import json
from pathlib import Path

from backend.scripts import build_index, chunk_data, clean_data, collect_data, run_evaluation


class FakeDatasetService:
    def __init__(self, storage_root: Path):
        self.storage_root = storage_root

    def collect_data(self) -> dict:
        raw_dir = self.storage_root / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "documents.json").write_text(
            json.dumps(
                [
                    {
                        "id": "doc_001",
                        "title": "Title",
                        "content": "内容",
                        "source": "course",
                        "char_count": 2,
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (raw_dir / "qa_pairs.json").write_text(
            json.dumps(
                [
                    {
                        "id": "qa_001",
                        "question": "Q",
                        "answer": "A",
                        "source": "auto_generated",
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return {"documents_count": 1, "qa_pairs_count": 1, "chunks_count": 0, "total_document_chars": 2}

    def clean_data(self) -> dict:
        return {"documents_count": 1, "qa_pairs_count": 1, "chunks_count": 0, "total_document_chars": 2}

    def chunk_data(self) -> dict:
        processed_dir = self.storage_root / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        (processed_dir / "chunks.json").write_text(
            json.dumps(
                [
                    {
                        "chunk_id": "chunk_000000",
                        "doc_id": "doc_001",
                        "content": "内容",
                        "char_start": 0,
                        "char_end": 2,
                        "token_count": 1,
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return {"documents_count": 1, "qa_pairs_count": 1, "chunks_count": 1, "total_document_chars": 2}


class FakeIndexService:
    def __init__(self, storage_root: Path):
        self.storage_root = storage_root

    def build_index(self) -> dict:
        index_dir = self.storage_root / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        (index_dir / "faiss.index").write_text("fake-index", encoding="utf-8")
        (index_dir / "chunk_meta.json").write_text("{}", encoding="utf-8")
        return {"index_ready": True, "vector_count": 1, "metadata_count": 1}


class FakeEvaluationService:
    def __init__(self, storage_root: Path):
        self.storage_root = storage_root

    def run_evaluation(self) -> dict:
        eval_dir = self.storage_root / "eval"
        eval_dir.mkdir(parents=True, exist_ok=True)
        (eval_dir / "auto_eval_report.txt").write_text("auto-report", encoding="utf-8")
        (eval_dir / "human_eval_report.txt").write_text("human-report", encoding="utf-8")
        (eval_dir / "human_scores.json").write_text("[]", encoding="utf-8")
        return {"auto_report": "auto-report", "human_report": "human-report", "human_score_count": 0}


def test_script_entrypoints_write_expected_artifacts(tmp_path: Path, monkeypatch):
    storage_root = tmp_path / "storage"
    dataset_service = FakeDatasetService(storage_root)
    index_service = FakeIndexService(storage_root)
    evaluation_service = FakeEvaluationService(storage_root)

    monkeypatch.setattr(collect_data, "get_dataset_service", lambda: dataset_service)
    monkeypatch.setattr(clean_data, "get_dataset_service", lambda: dataset_service)
    monkeypatch.setattr(chunk_data, "get_dataset_service", lambda: dataset_service)
    monkeypatch.setattr(build_index, "get_index_service", lambda: index_service)
    monkeypatch.setattr(run_evaluation, "get_evaluation_service", lambda: evaluation_service)

    collect_data.main()
    clean_data.main()
    chunk_data.main()
    build_index.main()
    run_evaluation.main()

    assert (storage_root / "raw" / "documents.json").exists()
    assert (storage_root / "raw" / "qa_pairs.json").exists()
    assert (storage_root / "processed" / "chunks.json").exists()
    assert (storage_root / "index" / "faiss.index").exists()
    assert (storage_root / "index" / "chunk_meta.json").exists()
    assert (storage_root / "eval" / "auto_eval_report.txt").exists()
    assert (storage_root / "eval" / "human_eval_report.txt").exists()
    assert (storage_root / "eval" / "human_scores.json").exists()
