"""URL category patterns and helpers for link detection."""

import logging
from re import Pattern
import re
from typing import Final, Dict, List

logger = logging.getLogger(__name__)

link_categories: Dict[str, List[str]] = {
    "youtube": [
        r"(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/",
        r"(?:https?://)?(?:www\.)?youtube\.com/watch",
        r"(?:https?://)?youtu\.be/",
    ],
    "twitch": [
        r"(?:https?://)?(?:www\.)?twitch\.tv/",
    ],
    "twitter": [
        r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/",
    ],
    "instagram": [
        r"(?:https?://)?(?:www\.)?instagram\.com/",
    ],
    "tiktok": [
        r"(?:https?://)?(?:www\.)?tiktok\.com/",
    ],
    "reddit": [
        r"(?:https?://)?(?:www\.)?reddit\.com/",
    ],
    "github": [
        r"(?:https?://)?(?:www\.)?github\.com/",
    ],
    "discord": [
        r"(?:https?://)?(?:www\.)?discord.gg/",
        r"(?:https?://)?(?:www\.)?discord.com/invite/",
    ],
}


# Link type constants
LINK_TYPE_YOUTUBE: Final[str] = "youtube"
LINK_TYPE_TWITTER: Final[str] = "twitter"
LINK_TYPE_REDDIT: Final[str] = "reddit"
LINK_TYPE_TIKTOK: Final[str] = "tiktok"
LINK_TYPE_INSTAGRAM: Final[str] = "instagram"
LINK_TYPE_GITHUB: Final[str] = "github"
LINK_TYPE_TWITCH: Final[str] = "twitch"
LINK_TYPE_DISCORD: Final[str] = "discord"
LINK_TYPE_OTHER: Final[str] = "other"


def _compile_patterns() -> dict[str, list[Pattern[str]]]:
    """Compile regex patterns for each link category in link_categories.

    Returns:
        A dictionary mapping category names to lists of compiled regex patterns.
    """
    return {
        category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        for category, patterns in link_categories.items()
    }

COMPILED_PATTERNS: Final[dict[str, list[Pattern[str]]]] = _compile_patterns()

def categorize_link(url: str) -> str:
    """Categorize a URL into a known link type.

    Args:
        url: The URL string to categorize.

    Returns:
        The link type category (e.g., 'youtube', 'other').
    """
    for category, regexes in COMPILED_PATTERNS.items():
        if any(regex.search(url) for regex in regexes):
            logger.debug("Categorized URL as %s: %s", category, url)
            return category
    logger.debug("Categorized URL as %s: %s", LINK_TYPE_OTHER, url)
    return LINK_TYPE_OTHER
