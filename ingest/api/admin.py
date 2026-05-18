from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from db.database import get_db
from models.base import IngestionLog, FeedSource
from services.scheduler import ingestion_scheduler
from utils.logger import setup_logger
from schemas.ingestion_log import IngestionLog as IngestionLogSchema, IngestionLogResponse

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the ingestion scheduler"""
    success = ingestion_scheduler.start()
    if success:
        return {
            "status": "started",
            "message": "Ingestion scheduler started successfully",
        }
    return {
        "status": "error",
        "message": "Failed to start scheduler",
    }


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the ingestion scheduler"""
    success = ingestion_scheduler.stop()
    if success:
        return {
            "status": "stopped",
            "message": "Ingestion scheduler stopped successfully",
        }
    return {
        "status": "error",
        "message": "Failed to stop scheduler",
    }


@router.get("/scheduler/status")
async def scheduler_status():
    """Get scheduler status"""
    status = ingestion_scheduler.get_status()
    return status


@router.get("/logs", response_model=IngestionLogResponse)
async def get_logs(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    feed_source_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get paginated ingestion logs"""
    try:
        query = db.query(IngestionLog)

        # Apply filters
        if feed_source_id:
            query = query.filter(IngestionLog.feed_source_id == feed_source_id)
        if status:
            query = query.filter(IngestionLog.status == status)

        # Get total count
        total = query.count()

        # Get paginated results
        logs = query.order_by(IngestionLog.started_at.desc()).limit(limit).offset(offset).all()

        return IngestionLogResponse(
            total=total,
            limit=limit,
            offset=offset,
            logs=logs,
        )
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return IngestionLogResponse(
            total=0,
            limit=limit,
            offset=offset,
            logs=[],
        )


@router.get("/logs/latest", response_model=Optional[IngestionLogSchema])
async def get_latest_log(db: Session = Depends(get_db)):
    """Get latest ingestion log"""
    try:
        log = db.query(IngestionLog).order_by(IngestionLog.started_at.desc()).first()
        return log
    except Exception as e:
        logger.error(f"Error fetching latest log: {e}")
        return None


@router.get("/feeds")
async def get_feeds(db: Session = Depends(get_db)):
    """Get all feed sources"""
    try:
        feeds = db.query(FeedSource).all()
        return feeds
    except Exception as e:
        logger.error(f"Error fetching feeds: {e}")
        return []
