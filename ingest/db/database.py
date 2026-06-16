import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"connect_timeout": 5},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def wait_for_database(max_attempts: int = 10, delay_seconds: int = 3) -> None:
    """Wait for the database to become available before creating tables.

    This keeps startup resilient when MySQL is still coming up or the port is
    temporarily unavailable.
    """
    last_error: OperationalError | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            return
        except OperationalError as exc:
            last_error = exc
            if attempt < max_attempts:
                logger.warning(
                    "Database not ready yet (%s/%s). Retrying in %ss...",
                    attempt,
                    max_attempts,
                    delay_seconds,
                )
                time.sleep(delay_seconds)

    if last_error is not None:
        raise last_error


def get_db() -> Session:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    from models.base import Base
    wait_for_database()
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")
