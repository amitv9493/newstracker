import logging

from kombu.exceptions import OperationalError

from app.core.exceptions import BrokerUnavailable
from app.tasks.jobs import process_message

logger = logging.getLogger(__name__)


def enqueue_process_message(message: str) -> str:
    try:
        result = process_message.delay(message)
    except (OperationalError, ConnectionError, TimeoutError, OSError) as exc:
        logger.exception("failed to enqueue task")
        raise BrokerUnavailable() from exc
    if not result.id:
        logger.error("task broker accepted work without a task id")
        raise BrokerUnavailable()
    return result.id
