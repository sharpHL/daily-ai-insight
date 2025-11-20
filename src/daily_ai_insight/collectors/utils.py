"""Utility functions for collectors."""

import re
import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
import html


USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
]


def get_random_user_agent() -> str:
    """Get a random user agent string.

    Returns:
        Random user agent string
    """
    return random.choice(USER_AGENTS)


async def sleep_random(max_seconds: float = 5.0) -> None:
    """Sleep for a random duration to avoid rate limiting.

    Args:
        max_seconds: Maximum sleep duration in seconds
    """
    await asyncio.sleep(random.random() * max_seconds)


def is_date_within_last_days(
    date_str: str,
    days: int = 3,
    date_format: Optional[str] = None
) -> bool:
    """Check if a date is within the last N days.

    Args:
        date_str: Date string to check
        days: Number of days to check
        date_format: Optional date format string

    Returns:
        True if date is within last N days
    """
    if not date_str:
        return False

    try:
        # Try to parse ISO format first
        if date_format:
            date = datetime.strptime(date_str, date_format)
        else:
            # Try common formats
            if 'T' in date_str:
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date = datetime.strptime(date_str, "%Y-%m-%d")

        cutoff = datetime.now() - timedelta(days=days)
        return date >= cutoff
    except (ValueError, TypeError):
        return False


def strip_html(html_content: str) -> str:
    """Strip HTML tags and return plain text.

    Args:
        html_content: HTML content string

    Returns:
        Plain text without HTML tags
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text and clean up whitespace
    text = soup.get_text(separator='\n', strip=True)

    # Remove multiple newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)

    return text.strip()


def escape_html(text: str) -> str:
    """Escape HTML special characters.

    Args:
        text: Text to escape

    Returns:
        HTML-escaped text
    """
    if not text:
        return ""

    return html.escape(str(text))


def format_date_to_chinese(date_str: str) -> str:
    """Format date string to Chinese format.

    Args:
        date_str: ISO format date string

    Returns:
        Formatted Chinese date string
    """
    if not date_str:
        return "未知日期"

    try:
        if 'T' in date_str:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            date = datetime.strptime(date_str, "%Y-%m-%d")

        return date.strftime("%Y年%m月%d日 %H:%M")
    except (ValueError, TypeError):
        return date_str


def get_follow_headers(cookie: Optional[str] = None) -> dict:
    """Get standard Follow.is API headers.

    Args:
        cookie: Optional cookie string

    Returns:
        Dictionary of HTTP headers
    """
    headers = {
        'User-Agent': get_random_user_agent(),
        'Content-Type': 'application/json',
        'accept': 'application/json',
        'accept-language': 'zh-CN,zh;q=0.9',
        'origin': 'https://app.follow.is',
        'priority': 'u=1, i',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'x-app-name': 'Folo Web',
        'x-app-version': '0.4.9',
    }

    if cookie:
        headers['Cookie'] = cookie

    return headers
