"""Tests for URL categories."""

from link_utils.categories import (
    categorize_link,
    LINK_TYPE_YOUTUBE,
    LINK_TYPE_TWITTER,
    LINK_TYPE_OTHER,
    LINK_TYPE_TWITCH,
    LINK_TYPE_GITHUB,
)


class TestCategorizeLink:
    """Test categorize_link function."""

    def test_youtube_url(self):
        """Test YouTube URL categorization."""
        assert (
            categorize_link("https://www.youtube.com/watch?v=123") == LINK_TYPE_YOUTUBE
        )
        assert categorize_link("https://youtu.be/123") == LINK_TYPE_YOUTUBE

    def test_twitter_url(self):
        """Test Twitter/X URL categorization."""
        assert categorize_link("https://twitter.com/user") == LINK_TYPE_TWITTER
        assert categorize_link("https://x.com/user") == LINK_TYPE_TWITTER

    def test_other_url(self):
        """Test unknown URL categorization."""
        assert categorize_link("https://example.com") == LINK_TYPE_OTHER

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert categorize_link("HTTPS://YOUTUBE.COM/WATCH") == LINK_TYPE_YOUTUBE

    def test_twitch_url(self):
        """Test Twitch URL categorization."""
        assert categorize_link("https://twitch.tv/user") == LINK_TYPE_TWITCH

    def test_github_url(self):
        """Test GitHub URL categorization."""
        assert categorize_link("https://github.com/user/repo") == LINK_TYPE_GITHUB

    def test_invalid_url(self):
        """Test invalid URL."""
        assert categorize_link("not a url") == LINK_TYPE_OTHER
