from http.client import HTTPException
from sqlalchemy.orm import Session

from app.models.arcticle import Article
from app.helpers.pagination import PageResult, PaginationParams, paginate
from app.schemas.article import ArticleCreate
from app.tasks.jobs import process_article as process_article_task
import hashlib
from app.helpers.enums import ArticleStatus

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



def process_article(db:Session, article_id: str) -> Article |None:
    article= db.query(Article).filter(Article.id == article_id).first()  
    if not article:
        return 
    if article.status == ArticleStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Article is already being processed.")
    if article.status == ArticleStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Article is already completed.")
    task = process_article_task.delay(article.id)
    return task.id 

def summarize_and_categorize_article(article :Article) -> Article:
    # some http call to summarize and categorize the article
    article.summary = "summary of the article"
    article.category = "category of the article"
    return article


def generate_content_hash(company_name:str, url:str, content:str) -> str:
    return hashlib.sha256(f"{company_name}{url}{content}".encode('utf-8')).hexdigest()