import re
from html.parser import HTMLParser
from typing import List
from slugify import slugify


class MLStripper(HTMLParser):
    """HTML tag stripper"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_data(self):
        return ''.join(self.text)


def strip_html(html_text: str) -> str:
    """Remove HTML tags from text"""
    if not html_text:
        return ""
    stripper = MLStripper()
    stripper.feed(html_text)
    return stripper.get_data()


def normalize_title(title: str) -> str:
    """Normalize title for deduplication"""
    if not title:
        return ""
    # Lowercase and strip whitespace
    normalized = title.lower().strip()
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def truncate_text(text: str, max_length: int = 5000) -> str:
    """Truncate text to max length"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def create_slug(title: str) -> str:
    """Create URL-friendly slug from title, handling Vietnamese characters"""
    if not title:
        return ""
    
    # Use python-slugify to convert Vietnamese characters to ASCII equivalents
    # e.g., "Việt Nam" -> "viet-nam", "Đặc biệt" -> "dac-biet"
    slug = slugify(
        title,
        max_length=500,
        word_boundary=True,
        save_order=True,
        lowercase=True
    )
    
    return slug if slug else "article"  # Fallback if slug is empty
