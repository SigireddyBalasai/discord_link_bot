"""
Version utility for Discord bot.

Provides functions to get the current build version from git.
"""

import subprocess
from pathlib import Path
from typing import Optional


def get_git_version() -> str:
    """Get the current git commit hash (short version).
    
    Returns:
        The short git commit hash, or 'unknown' if git is not available.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def get_version_string() -> str:
    """Get a formatted version string for display.
    
    Reads from VERSION file if available (production builds),
    otherwise falls back to git command (local development).
    
    Returns:
        A formatted version string like 'v0.1.0 (abc1234)'.
    """
    # Try to read from VERSION file (production)
    try:
        version_file = Path(__file__).parent.parent / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
    except Exception:
        pass
    
    # Fallback to git command (local development)
    git_hash = get_git_version()
    return f"v0.1.0 ({git_hash})"
