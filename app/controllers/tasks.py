from fastapi import APIRouter

from app.services.tasks import enqueue_process_message

from app.schemas.tasks import TaskAccepted
router = APIRouter(tags=["tasks"])


@router.post("/tasks", response_model=TaskAccepted, status_code=202)
def enqueue_task(payload: str) -> TaskAccepted:
    task_id = enqueue_process_message(payload)
    return TaskAccepted(task_id=task_id, status="queued")
