"""Evaluation status routes."""

from fastapi import APIRouter, Depends

from backend.app.core.response import success_response
from backend.app.services.evaluation_service import EvaluationService, get_evaluation_service

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/latest")
async def latest_evaluations(service: EvaluationService = Depends(get_evaluation_service)) -> dict:
    return success_response(service.latest_reports())

