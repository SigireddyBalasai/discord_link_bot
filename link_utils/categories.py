"""URL category patterns and helpers for link detection."""

import logging
from re import Pattern
import re
from typing import Final

logger = logging.getLogger(__name__)

link_categories = {
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


def categorize_link(url: str) -> str:
    """Categorize a URL into a known link type."""
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        logger.debug("Categorized URL as YouTube: %s", url)
        return LINK_TYPE_YOUTUBE
    if "twitter.com" in url_lower or "x.com" in url_lower:
        logger.debug("Categorized URL as Twitter: %s", url)
        return LINK_TYPE_TWITTER
    if "reddit.com" in url_lower:
        logger.debug("Categorized URL as Reddit: %s", url)
        return LINK_TYPE_REDDIT
    if "tiktok.com" in url_lower:
        logger.debug("Categorized URL as TikTok: %s", url)
        return LINK_TYPE_TIKTOK
    if "instagram.com" in url_lower:
        logger.debug("Categorized URL as Instagram: %s", url)
        return LINK_TYPE_INSTAGRAM
    if "github.com" in url_lower:
        logger.debug("Categorized URL as GitHub: %s", url)
        return LINK_TYPE_GITHUB
    if "twitch.tv" in url_lower:
        logger.debug("Categorized URL as Twitch: %s", url)
        return LINK_TYPE_TWITCH
    if "discord.gg" in url_lower or "discord.com/invite" in url_lower:
        logger.debug("Categorized URL as Discord: %s", url)
        return LINK_TYPE_DISCORD
    logger.debug("Categorized URL as Other: %s", url)
    return LINK_TYPE_OTHER


def get_category_patterns() -> dict[str, list[Pattern[str]]]:
    """Compile regex patterns for each link category in link_categories."""
    return {
        category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        for category, patterns in link_categories.items()
    }
