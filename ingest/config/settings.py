from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Database
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "rss_ingest"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/ingest.log"

    # Scheduler
    INGEST_INTERVAL_MINUTES: int = 30
    MAX_RETRIES: int = 4
    REQUEST_TIMEOUT_SECONDS: int = 10

    # Data Processing
    MAX_DESCRIPTION_LENGTH: int = 5000
    BATCH_SIZE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def database_url(self) -> str:
        """Generate database URL for SQLAlchemy"""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"


settings = Settings()
