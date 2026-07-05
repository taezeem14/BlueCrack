"""
BlueCrack — Advanced Browser Penetration Framework
====================================================
Hydra-style credential auditing tool powered by Selenium WebDriver.

Usage::

    # Install
    pip install bluecrack

    # Launch Web UI
    bluecrack

    # CLI attack mode
    bluecrack attack -u admin -P passwords.txt --url https://target.com/login --error "failed"

    # Environment diagnostics
    bluecrack doctor
"""

from bluecrack._version import __version__

__all__ = [
    "__version__",
]
