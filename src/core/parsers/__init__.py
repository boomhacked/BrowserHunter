"""
Browser parsers for Chrome, Firefox, and Edge
"""
from .chrome_parser import ChromeParser
from .firefox_parser import FirefoxParser
from .edge_parser import EdgeParser

__all__ = ['ChromeParser', 'FirefoxParser', 'EdgeParser']
