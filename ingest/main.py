from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime
import logging

from config.settings import settings
from db.database import init_db
from db.init_db import init_db as seed_db
from api.admin import router as admin_router
from services.scheduler import ingestion_scheduler
from utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    
    # Seed data if needed
    try:
        seed_db()
        logger.info("Database seeded")
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
    
    # Auto-start the ingestion scheduler
    try:
        ingestion_scheduler.start()
        logger.info("Ingestion scheduler auto-started on app startup")
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        ingestion_scheduler.stop()
        logger.info("Ingestion scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="RSS Feed Ingestion API",
    description="Admin API for RSS feed ingestion system",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routes
app.include_router(admin_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RSS Feed Ingestion API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
