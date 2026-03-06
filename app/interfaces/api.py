import logging
from fastapi import FastAPI

from app.core.config import settings
from app.core.logger import setup_logging
from app.interfaces.routes import api_router

from app.application.workflows_registry import WORKFLOW_REGISTRY
from app.infrastructure.executor import InMemoryExecutor

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    setup_logging(settings.debug)

    app = FastAPI(title=settings.app_name)
    app.include_router(api_router, prefix=settings.api_prefix)

    app.state.executor = InMemoryExecutor(WORKFLOW_REGISTRY)

    @app.on_event("startup")
    async def on_startup():
        app.state.executor.start()
        logger.info("Starting %s (debug=%s)", settings.app_name, settings.debug)

    @app.on_event("shutdown")
    async def on_shutdown():
        await app.state.executor.stop()

    return app