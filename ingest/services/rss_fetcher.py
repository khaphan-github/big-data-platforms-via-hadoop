import httpx
import asyncio
from lxml import etree
from typing import List, Dict, Optional, Any
from config.settings import settings
from utils.logger import setup_logger
from utils.date_parser import parse_date

logger = setup_logger(__name__)


class RSSFetcher:
    """Fetch and parse RSS feeds"""

    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS
        self.max_retries = settings.MAX_RETRIES
        self.client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)

    async def fetch_feed(self, feed_url: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse a single RSS feed with retry logic"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching RSS feed: {feed_url}")
                response = await self.client.get(feed_url)
                response.raise_for_status()

                # Parse XML
                root = etree.fromstring(response.content)
                items = self._parse_items(root)

                logger.info(f"Successfully fetched {len(items)} items from {feed_url}")
                return {"url": feed_url, "items": items, "status": "success"}

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} fetching {feed_url}")
            except httpx.ConnectError as e:
                logger.error(f"Connection error fetching {feed_url}: {e}")
            except Exception as e:
                logger.error(f"Error parsing {feed_url}: {e}")

            # Exponential backoff
            if attempt < self.max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                logger.info(f"Retrying in {wait_time} seconds... (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(wait_time)

        logger.error(f"Failed to fetch {feed_url} after {self.max_retries} retries")
        return {"url": feed_url, "items": [], "status": "failed"}

    def _parse_items(self, root: etree._Element) -> List[Dict[str, Any]]:
        """Parse RSS items from XML root"""
        items = []

        # Find all item elements
        for item_elem in root.xpath("//item"):
            item = self._extract_item_data(item_elem)
            if item:
                items.append(item)

        return items

    def _extract_item_data(self, item_elem: etree._Element) -> Optional[Dict[str, Any]]:
        """Extract data from a single RSS item"""
        try:
            # Extract fields (handle both text and CDATA)
            title = self._get_text(item_elem, "title")
            link = self._get_text(item_elem, "link")
            description = self._get_text(item_elem, "description")
            guid = self._get_text(item_elem, "guid")
            pub_date_str = self._get_text(item_elem, "pubDate")
            author = self._get_text(item_elem, "author")
            comments_str = self._get_text(item_elem, "slash:comments") or "0"

            if not title or not link:
                return None

            # Parse publication date
            published_date = parse_date(pub_date_str)
            if not published_date:
                logger.warning(f"Could not parse date: {pub_date_str}")
                return None

            # Parse comment count
            try:
                comment_count = int(comments_str)
            except (ValueError, TypeError):
                comment_count = 0

            return {
                "title": title,
                "link": link,
                "description": description,
                "guid": guid,
                "author": author,
                "published_date": published_date,
                "comment_count": comment_count,
            }

        except Exception as e:
            logger.error(f"Error extracting item data: {e}")
            return None

    def _get_text(self, elem: etree._Element, xpath: str) -> Optional[str]:
        """Get text content from element, handling CDATA and text nodes"""
        try:
            elements = elem.xpath(f"{xpath}/text()")
            if elements:
                text = elements[0]
                if isinstance(text, str):
                    return text.strip() or None
            return None
        except Exception:
            return None

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
