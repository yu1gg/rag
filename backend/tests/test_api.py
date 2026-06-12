"""API tests for Ver 2.0 backend."""

from fastapi.testclient import TestClient

from backend.app.core.exceptions import ServiceUnavailableError
from backend.app.services.rag_service import get_rag_service
from backend.main import create_app


class FakeRagService:
    def answer_question(self, question: str, top_k: int, temperature: float) -> dict:
        return {
            "answer": f"mock-answer:{question}:{top_k}:{temperature}",
            "references": [
                {
                    "index": 1,
                    "chunk_id": "chunk_001",
                    "doc_id": "doc_001",
                    "score": 0.99,
                    "excerpt": "mock excerpt",
                }
            ],
        }

    def summarize(self, text: str, temperature: float) -> dict:
        return {"summary": f"mock-summary:{len(text)}:{temperature}"}


class FailingRagService:
    def answer_question(self, question: str, top_k: int, temperature: float) -> dict:
        raise ServiceUnavailableError("索引尚未就绪")

    def summarize(self, text: str, temperature: float) -> dict:
        raise ServiceUnavailableError("摘要服务暂不可用")


def make_client(service) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_rag_service] = lambda: service
    return TestClient(app)


def test_health_returns_status():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["version"] == "2.0.0"
    assert isinstance(payload["data"]["index_ready"], bool)


def test_qa_success_response():
    with make_client(FakeRagService()) as client:
        response = client.post(
            "/api/v1/rag/qa",
            json={"question": "什么是 RAG？", "top_k": 3, "temperature": 0.6},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert "mock-answer" in payload["data"]["answer"]
    assert payload["data"]["references"][0]["chunk_id"] == "chunk_001"


def test_summary_success_response():
    with make_client(FakeRagService()) as client:
        response = client.post(
            "/api/v1/rag/summary",
            json={"text": "这是一段需要摘要的文本。", "temperature": 0.5},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["summary"].startswith("mock-summary")


def test_validation_error_uses_response_envelope():
    with make_client(FakeRagService()) as client:
        response = client.post(
            "/api/v1/rag/qa",
            json={"question": "   ", "top_k": 11, "temperature": 2.0},
        )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == 422
    assert payload["message"] == "请求参数校验失败"
    assert payload["data"]


def test_service_error_uses_response_envelope():
    with make_client(FailingRagService()) as client:
        response = client.post(
            "/api/v1/rag/qa",
            json={"question": "什么是 RAG？"},
        )

    assert response.status_code == 503
    payload = response.json()
    assert payload["code"] == 503
    assert payload["message"] == "索引尚未就绪"
