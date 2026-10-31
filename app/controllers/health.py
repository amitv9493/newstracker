from fastapi import APIRouter

from app.dependencies import DbSession
from app.services.health import check_database

router = APIRouter(tags=["health"])


@router.get("/health",)
def health(db: DbSession) -> dict:
    check_database(db)
    return {"status": "ok"}
