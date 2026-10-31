import logging

from fastapi import APIRouter, FastAPI

from app.controllers.articles import router as articles_router
from app.controllers.health import router as health_router
from app.controllers.tasks import router as tasks_router
from app.core.handlers import register_exception_handlers

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(health_router)
api_v1.include_router(tasks_router)
api_v1.include_router(articles_router)


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    app = FastAPI(title="newsextractor", docs_url="/docs", redoc_url="/redoc")
    register_exception_handlers(app)
    app.include_router(api_v1)
    return app


app = create_app()
