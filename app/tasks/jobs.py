from app.helpers.enums import ArticleStatus
from app.dependencies import get_db
import logging

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.process_message")
def process_message(message: str) -> str:
    if not message or not message.strip():
        logger.error("process_message received a blank message")
        raise ValueError("message must not be blank")
    print(f"Processing message: {message}")
    return message


@celery_app.task(name="tasks.process_article")
def process_article( article_id: str):
    from app.models.arcticle import Article
    from app.helpers.scrapper import scrap_url
    from app.services.article import generate_content_hash
    for db in get_db():
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return None
        print(f"Summarizing and categorizing article: {article.id}")
        article.status = ArticleStatus.PROCESSING.value
        try:
            content = scrap_url(article.url)
            article.content = content
            article.content_hash = generate_content_hash(article.company_name, article.url, article.content)

            article = process_article_summary(article)
            article.status = ArticleStatus.COMPLETED.value
        except Exception as e:
            article.status = ArticleStatus.FAILED.value
        
        finally:
            db.commit()
            db.refresh(article)
    return article.id




@celery_app.task(name="tasks.process_article_summary")
def process_article_summary( article_id: str):
    from app.services.article import summarize_and_categorize_article
    from app.models.arcticle import Article
    for db in get_db():
        article = db.query(Article).filter(Article.id == article_id).first()
        article = summarize_and_categorize_article(article)
        db.commit()
        db.refresh(article)
        return article.id