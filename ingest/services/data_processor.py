from typing import Dict, Any, Optional
from datetime import datetime
from config.settings import settings
from utils.logger import setup_logger
from utils.text_cleaner import strip_html, truncate_text, create_slug
from utils.date_parser import parse_date

logger = setup_logger(__name__)


class DataProcessor:
    """Process and transform raw RSS item data"""

    @staticmethod
    def process_article(
        item: Dict[str, Any],
        feed_source_id: int,
        category_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Process raw RSS item into article data"""
        try:
            title = item.get("title", "").strip()
            link = item.get("link", "").strip()
            description = item.get("description", "").strip()
            author = item.get("author")
            published_date = item.get("published_date")
            guid = item.get("guid")
            comment_count = item.get("comment_count", 0)

            # Validate required fields
            if not title or not link:
                logger.warning("Missing required fields (title or link)")
                return None

            # Clean description - strip HTML
            content_html = description
            description_text = strip_html(description) if description else ""
            description_text = truncate_text(description_text, settings.MAX_DESCRIPTION_LENGTH)

            # Create slug from title
            slug = create_slug(title)
            if not slug:
                slug = link.split("/")[-1][:500]

            return {
                "title": title,
                "slug": slug,
                "description": description_text,
                "content_html": content_html,
                "link": link,
                "guid": guid,
                "author": author,
                "published_date": published_date,
                "feed_source_id": feed_source_id,
                "category_id": category_id,
                "comment_count": comment_count,
            }

        except Exception as e:
            logger.error(f"Error processing article: {e}")
            return None

    @staticmethod
    def batch_process_items(
        items: list[Dict[str, Any]],
        feed_source_id: int,
        category_id: int,
    ) -> list[Dict[str, Any]]:
        """Process multiple items"""
        processed = []
        for item in items:
            processed_item = DataProcessor.process_article(item, feed_source_id, category_id)
            if processed_item:
                processed.append(processed_item)

        logger.info(f"Processed {len(processed)} items out of {len(items)}")
        return processed
