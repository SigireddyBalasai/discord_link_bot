"""Tests for URL tools."""

from link_utils.url_tools import extract_urls


class TestExtractUrls:
    """Test extract_urls function."""

    def test_extract_single_url(self):
        """Test extracting a single URL."""
        text = "Check this out: https://example.com"
        result = extract_urls(text)
        assert result == ["https://example.com"]

    def test_extract_multiple_urls(self):
        """Test extracting multiple URLs."""
        text = "Visit https://site1.com and https://site2.com"
        result = extract_urls(text)
        assert result == ["https://site1.com", "https://site2.com"]

    def test_no_urls(self):
        """Test with no URLs."""
        text = "This is just text."
        result = extract_urls(text)
        assert result is None

    def test_empty_text(self):
        """Test with empty text."""
        result = extract_urls("")
        assert result is None

    def test_www_urls(self):
        """Test URLs starting with www."""
        text = "Go to www.example.com"
        result = extract_urls(text)
        assert result == ["www.example.com"]

    def test_url_with_query(self):
        """Test URL with query parameters."""
        text = "Check https://example.com?page=1&sort=asc"
        result = extract_urls(text)
        assert result == ["https://example.com?page=1&sort=asc"]

    def test_url_with_fragment(self):
        """Test URL with fragment."""
        text = "Link: https://example.com#section"
        result = extract_urls(text)
        assert result == ["https://example.com#section"]

    def test_mixed_urls_and_text(self):
        """Test multiple URLs mixed with text."""
        text = "Visit https://site1.com for info, or https://site2.com/page?q=test"
        result = extract_urls(text)
        assert result == ["https://site1.com", "https://site2.com/page?q=test"]
