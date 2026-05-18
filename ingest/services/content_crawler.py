import httpx
import asyncio
from lxml import etree, html
from typing import Optional, Dict, Any
from config.settings import settings
from utils.logger import setup_logger
import bleach

logger = setup_logger(__name__)


class ContentCrawler:
    """Crawl and extract full article content from URLs"""

    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'a', 'img', 'div', 'span'
    ]
    
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title'],
        'div': ['class'],
        'span': ['class'],
    }

    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS
        self.max_retries = settings.MAX_RETRIES
        self.client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)

    async def crawl_content(self, url: str) -> Optional[str]:
        """Crawl and extract article content from URL"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Crawling content from: {url}")
                response = await self.client.get(url)
                response.raise_for_status()

                # Parse HTML
                content = self._extract_main_content(response.text, url)
                
                if content and len(content.strip()) > 50:
                    logger.info(f"Successfully extracted {len(content)} characters from {url}")
                    return content
                else:
                    logger.warning(f"No substantial content found at {url}")
                    return None

            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error {e.response.status_code} crawling {url}")
            except httpx.ConnectError as e:
                logger.warning(f"Connection error crawling {url}: {e}")
            except Exception as e:
                logger.warning(f"Error crawling {url}: {e}")

            # Exponential backoff
            if attempt < self.max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                logger.info(f"Retrying in {wait_time} seconds... (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(wait_time)

        logger.error(f"Failed to crawl {url} after {self.max_retries} retries")
        return None

    def _extract_main_content(self, html_text: str, url: str) -> Optional[str]:
        """Extract main article content from HTML"""
        try:
            # Parse HTML
            tree = html.fromstring(html_text)
            tree.make_links_absolute(url)

            # Try common article content selectors
            content_selectors = [
                '//article',
                '//*[@class and contains(@class, "article-content")]',
                '//*[@class and contains(@class, "post-content")]',
                '//*[@class and contains(@class, "entry-content")]',
                '//*[@class and contains(@class, "content")]',
                '//main',
                '//div[@role="main"]',
            ]

            content_elem = None
            for selector in content_selectors:
                elements = tree.xpath(selector)
                if elements:
                    content_elem = elements[0]
                    logger.debug(f"Found content using selector: {selector}")
                    break

            # Fallback to body if no specific content found
            if content_elem is None:
                body_elements = tree.xpath('//body')
                if body_elements:
                    content_elem = body_elements[0]
                else:
                    logger.warning(f"Could not find body element in {url}")
                    return None

            # Remove script, style, and navigation elements
            for elem in content_elem.xpath('.//script | .//style | .//nav | .//footer | .//header'):
                elem.getparent().remove(elem)

            # Convert to string and clean
            content_html = etree.tostring(content_elem, encoding='unicode', method='html')
            
            # Sanitize HTML
            clean_html = bleach.clean(
                content_html,
                tags=self.ALLOWED_TAGS,
                attributes=self.ALLOWED_ATTRIBUTES,
                strip=True
            )

            # Remove excessive whitespace
            clean_html = ' '.join(clean_html.split())
            
            return clean_html if clean_html.strip() else None

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
