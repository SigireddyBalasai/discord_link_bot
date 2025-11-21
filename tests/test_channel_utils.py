"""Tests for channel utilities."""

from core.channel_utils import validate_acls, create_acls


class TestValidateAcls:
    """Test validate_acls function."""

    def test_all_false(self):
        """Test with all ACLs false."""
        acls = {"youtube": False, "twitch": False, "twitter": False}
        assert validate_acls(acls) is False

    def test_one_true(self):
        """Test with one ACL true."""
        acls = {"youtube": True, "twitch": False, "twitter": False}
        assert validate_acls(acls) is True

    def test_all_true(self):
        """Test with all ACLs true."""
        acls = {"youtube": True, "twitch": True, "twitter": True}
        assert validate_acls(acls) is True

    def test_empty_dict(self):
        """Test with empty dictionary."""
        acls = {}
        assert validate_acls(acls) is False


class TestCreateAcls:
    """Test create_acls function."""

    def test_default(self):
        """Test default ACLs."""
        result = create_acls()
        expected = {
            "youtube": False,
            "twitch": False,
            "twitter": False,
            "instagram": False,
            "tiktok": False,
            "reddit": False,
            "github": False,
            "discord": False,
            "other": False,
        }
        assert result == expected

    def test_some_true(self):
        """Test with some ACLs true."""
        result = create_acls(youtube=True, twitter=True)
        expected = {
            "youtube": True,
            "twitch": False,
            "twitter": True,
            "instagram": False,
            "tiktok": False,
            "reddit": False,
            "github": False,
            "discord": False,
            "other": False,
        }
        assert result == expected

    def test_all_true(self):
        """Test with all ACLs true."""
        result = create_acls(
            youtube=True,
            twitch=True,
            twitter=True,
            instagram=True,
            tiktok=True,
            reddit=True,
            github=True,
            discord_links=True,
            other=True,
        )
        expected = {
            "youtube": True,
            "twitch": True,
            "twitter": True,
            "instagram": True,
            "tiktok": True,
            "reddit": True,
            "github": True,
            "discord": True,
            "other": True,
        }
        assert result == expected
