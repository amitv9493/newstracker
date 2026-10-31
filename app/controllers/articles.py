from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import DbSession
from app.helpers.pagination import Page, Pagination
from app.schemas.article import Article, ArticleCreate
from app.services.article import create_article, get_articles, process_article
router = APIRouter()


@router.post("/articles", response_model=Article)
def create_article_route(article: ArticleCreate, db: DbSession):
    return create_article(db, article)


@router.get("/articles", response_model=Page[Article])
def get_articles_route(
    db: DbSession,
    pagination: Pagination,
    company_name: Annotated[str | None, Query()] = None,
):
    return get_articles(db, pagination, company_name)

@router.post("/articles/{article_id}/process", status_code=202)
def process_article_route(article_id: str, db: DbSession):
    task_id = process_article(db, article_id)
    return task_id