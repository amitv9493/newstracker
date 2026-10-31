from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ArticleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    company_name: str
    title: str
    content: str
    url: HttpUrl
    category: Optional[str] = None
    summary: Optional[str] = None
    content_hash: Optional[str] = None


class ArticleCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    url: HttpUrl

    @field_validator("company_name")
    @classmethod
    def company_name_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class Article(ArticleBase):
    created_at: datetime
    updated_at: datetime
