from sqlalchemy.orm import Session

from app.models.arcticle import Article
from app.pagination import PageResult, PaginationParams, paginate
from app.schemas.article import ArticleCreate


def create_article(db: Session, article: ArticleCreate) -> Article:
    url = str(article.url)
    existing = (
        db.query(Article)
        .filter(
            Article.company_name == article.company_name,
            Article.url == url,
        )
        .first()
    )
    if existing:
        return existing

    db_article = Article(
        company_name=article.company_name,
        title="",
        content="",
        url=url,
        category="",
        summary="",
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article


def get_articles(
    db: Session,
    pagination: PaginationParams,
    company_name: str | None = None,
) -> PageResult:
    query = db.query(Article)
    if company_name is not None and company_name.strip():
        query = query.filter(Article.company_name == company_name.strip())
    return paginate(query.order_by(Article.id), pagination)
