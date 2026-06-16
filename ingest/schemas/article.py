from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ArticleBase(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    content_html: Optional[str] = None
    link: str
    guid: Optional[str] = None
    author: Optional[str] = None
    published_date: datetime
    feed_source_id: int
    category_id: int
    comment_count: int = 0


class ArticleCreate(ArticleBase):
    pass


class Article(ArticleBase):
    id: int
    fetched_date: datetime
    is_duplicate: bool = False
    duplicate_of_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
