from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, null

from .base import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True)
    title = Column(String, index=True)
    content = Column(Text, index=True)
    url = Column(String, index=True)
    category = Column(String, index=True)
    summary = Column(Text, index=True)
    content_hash = Column(String, index=True, unique=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)