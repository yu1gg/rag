"""RAG-related routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.core.response import success_response
from backend.app.schemas.rag import QaRequest, SummaryRequest
from backend.app.services.rag_service import RagService, get_rag_service

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/qa")
def qa(payload: QaRequest, service: RagService = Depends(get_rag_service)) -> dict:
    result = service.answer_question(
        question=payload.question,
        top_k=payload.top_k,
        temperature=payload.temperature,
    )
    return success_response(result)


@router.post("/summary")
def summary(
    payload: SummaryRequest,
    service: RagService = Depends(get_rag_service),
) -> dict:
    result = service.summarize(
        text=payload.text,
        temperature=payload.temperature,
    )
    return success_response(result)


