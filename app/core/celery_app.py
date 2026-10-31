from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "newsextractor",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.jobs"]
)