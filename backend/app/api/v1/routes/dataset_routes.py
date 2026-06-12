"""Dataset state routes."""

from fastapi import APIRouter, Depends

from backend.app.core.response import success_response
from backend.app.services.dataset_service import DatasetService, get_dataset_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/stats")
def dataset_stats(service: DatasetService = Depends(get_dataset_service)) -> dict:
    return success_response(service.dataset_stats())

