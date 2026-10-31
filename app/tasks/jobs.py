import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.process_message")
def process_message(message: str) -> str:
    if not message or not message.strip():
        logger.error("process_message received a blank message")
        raise ValueError("message must not be blank")
    return message
