"""
BlueCrack — Advanced Browser Penetration Framework
====================================================
Hydra-style credential auditing tool with two attack modes:

  - **Browser Mode**: Selenium WebDriver for JS-heavy login forms
  - **HTTP Mode**: Raw HTTP POST requests (Hydra-style, 100x faster)

Usage::

    # Install
    pip install bluecrack

    # Launch Web UI
    bluecrack

    # CLI attack (browser mode)
    bluecrack attack -u admin -P passwords.txt --url https://target.com/login --error "failed"

    # CLI attack (HTTP mode — lightning fast)
    bluecrack attack --mode http -u admin -P passwords.txt --url https://target.com/login --error "failed"

    # Environment diagnostics
    bluecrack doctor
"""

from bluecrack._version import __version__

__all__ = [
    "__version__",
]

