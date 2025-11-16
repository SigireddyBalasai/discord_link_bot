"""URL extraction and categorization utilities."""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

url_pattern = re.compile(r"(?:https?://|www\.)[^\s]+", re.IGNORECASE)


def extract_urls(text: str) -> Optional[list[str]]:
    """Extract all URLs from text. Returns None if input is empty or no URLs found."""
    if not text:
        return None
    matches = url_pattern.findall(text)
    if matches:
        logger.debug("Extracted %d URLs from text", len(matches))
        return matches
    return None
