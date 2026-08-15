"""Tests for version consistency."""

import re

from bluecrack._version import __version__


def test_version_format():
    """Verify that __version__ is a valid semver string."""
    assert isinstance(__version__, str)
    match = re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$", __version__)
    assert match is not None, f"Invalid version string format: {__version__}"
