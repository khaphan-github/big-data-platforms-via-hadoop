from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class IngestionLogBase(BaseModel):
    feed_source_id: Optional[int] = None
    status: str  # success, failed, partial
    articles_fetched: int = 0
    articles_saved: int = 0
    duplicates_found: int = 0
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None


class IngestionLogCreate(IngestionLogBase):
    pass


class IngestionLog(IngestionLogBase):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IngestionLogResponse(BaseModel):
    total: int
    limit: int
    offset: int
    logs: list[IngestionLog]
