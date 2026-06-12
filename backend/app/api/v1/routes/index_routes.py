"""Index status routes."""

from fastapi import APIRouter, Depends

from backend.app.core.response import success_response
from backend.app.services.index_service import IndexService, get_index_service

router = APIRouter(prefix="/index", tags=["index"])


@router.get("/status")
async def index_status(service: IndexService = Depends(get_index_service)) -> dict:
    return success_response(service.index_status())

