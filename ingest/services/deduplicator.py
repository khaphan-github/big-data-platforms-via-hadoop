from sqlalchemy.orm import Session
from models.base import Article
from utils.logger import setup_logger
from utils.text_cleaner import normalize_title
from datetime import datetime, timedelta

logger = setup_logger(__name__)


class Deduplicator:
    """Handle article deduplication"""

    @staticmethod
    def check_duplicate(
        db: Session,
        title: str,
        published_date: datetime,
        feed_source_id: int,
    ) -> tuple[bool, int | None]:
        """
        Check if article already exists by title + publication date.
        Returns (is_duplicate, duplicate_id)
        """
        try:
            # Normalize title for comparison
            normalized_title = normalize_title(title)

            # Search for articles with same title published on same day
            same_day_start = published_date.replace(hour=0, minute=0, second=0, microsecond=0)
            same_day_end = same_day_start + timedelta(days=1)

            existing = db.query(Article).filter(
                Article.feed_source_id == feed_source_id,
                Article.published_date >= same_day_start,
                Article.published_date < same_day_end,
            ).all()

            for article in existing:
                if normalize_title(article.title) == normalized_title:
                    logger.info(f"Duplicate found: {title}")
                    return True, article.id

            return False, None

        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return False, None

    @staticmethod
    def mark_duplicate(
        db: Session,
        article_id: int,
        duplicate_of_id: int,
    ) -> bool:
        """Mark an article as a duplicate"""
        try:
            article = db.query(Article).filter(Article.id == article_id).first()
            if article:
                article.is_duplicate = True
                article.duplicate_of_id = duplicate_of_id
                db.commit()
                logger.info(f"Article {article_id} marked as duplicate of {duplicate_of_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error marking duplicate: {e}")
            db.rollback()
            return False
