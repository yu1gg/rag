"""Tests for dataset/index/evaluation state APIs."""

from fastapi.testclient import TestClient

from backend.app.services.dataset_service import get_dataset_service
from backend.app.services.evaluation_service import get_evaluation_service
from backend.app.services.index_service import get_index_service
from backend.main import create_app


class FakeDatasetService:
    def dataset_stats(self) -> dict:
        return {
            "documents_count": 12,
            "qa_pairs_count": 34,
            "chunks_count": 56,
            "total_document_chars": 7890,
        }


class FakeIndexService:
    def index_status(self) -> dict:
        return {
            "index_ready": True,
            "vector_count": 108,
            "metadata_count": 108,
        }


class FakeEvaluationService:
    def latest_reports(self) -> dict:
        return {
            "auto_report": "auto-report",
            "human_report": "human-report",
            "human_score_count": 10,
        }


def make_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_dataset_service] = lambda: FakeDatasetService()
    app.dependency_overrides[get_index_service] = lambda: FakeIndexService()
    app.dependency_overrides[get_evaluation_service] = lambda: FakeEvaluationService()
    return TestClient(app)


def test_dataset_stats_response():
    with make_client() as client:
        response = client.get("/api/v1/datasets/stats")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["documents_count"] == 12
    assert payload["data"]["qa_pairs_count"] == 34


def test_index_status_response():
    with make_client() as client:
        response = client.get("/api/v1/index/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["index_ready"] is True
    assert payload["data"]["vector_count"] == 108


def test_evaluation_latest_response():
    with make_client() as client:
        response = client.get("/api/v1/evaluations/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["auto_report"] == "auto-report"
    assert payload["data"]["human_score_count"] == 10

