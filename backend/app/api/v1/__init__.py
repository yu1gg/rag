"""API v1 router registration."""

from fastapi import APIRouter

from backend.app.api.v1.routes.dataset_routes import router as dataset_router
from backend.app.api.v1.routes.evaluation_routes import router as evaluation_router
from backend.app.api.v1.routes.health_routes import router as health_router
from backend.app.api.v1.routes.index_routes import router as index_router
from backend.app.api.v1.routes.rag_routes import router as rag_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(rag_router)
api_router.include_router(dataset_router)
api_router.include_router(index_router)
api_router.include_router(evaluation_router)

