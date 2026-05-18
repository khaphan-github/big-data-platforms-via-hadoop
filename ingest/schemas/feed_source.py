from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FeedSourceBase(BaseModel):
    name: str
    url: str
    category_id: int
    is_active: bool = True


class FeedSourceCreate(FeedSourceBase):
    pass


class FeedSource(FeedSourceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_fetched_at: Optional[datetime] = None

    class Config:
        from_attributes = True
