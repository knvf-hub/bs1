from fastapi import APIRouter

from app.interfaces.routes.health import router as health_router
from app.interfaces.routes.workflow import router as workflow_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(workflow_router)