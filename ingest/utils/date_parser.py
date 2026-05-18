from email.utils import parsedate_to_datetime
from datetime import datetime
from typing import Optional


def parse_rfc2822_date(date_str: str) -> Optional[datetime]:
    """Parse RFC2822 date format (used in RSS feeds)"""
    if not date_str:
        return None
    try:
        dt = parsedate_to_datetime(date_str)
        # Convert to naive datetime (remove timezone)
        return dt.replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def parse_iso_date(date_str: str) -> Optional[datetime]:
    """Parse ISO8601 date format"""
    if not date_str:
        return None
    try:
        # Handle timezone info
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None)
        else:
            return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


def parse_date(date_str: str) -> Optional[datetime]:
    """Try parsing date in various formats"""
    if not date_str:
        return None

    # Try RFC2822 first (RSS standard)
    result = parse_rfc2822_date(date_str)
    if result:
        return result

    # Try ISO format
    result = parse_iso_date(date_str)
    if result:
        return result

    # Return None if all parsing attempts fail
    return None
