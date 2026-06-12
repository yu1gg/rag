"""Health check routes."""

from fastapi import APIRouter

from backend.app.core.config import settings
from backend.app.core.response import success_response

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return success_response(
        {
            "status": "ok",
            "version": settings.app_version,
            "index_ready": settings.index_ready,
        }
    )

