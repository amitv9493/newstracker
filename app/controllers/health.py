from fastapi import APIRouter

from app.dependencies import DbSession
from app.services.health import check_database
from app.views.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: DbSession) -> HealthResponse:
    check_database(db)
    return HealthResponse(status="ok")
