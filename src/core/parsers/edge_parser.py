"""
Microsoft Edge browser history parser
Edge uses Chromium engine, so it's similar to Chrome
"""
from .chrome_parser import ChromeParser


class EdgeParser(ChromeParser):
    """Parser for Microsoft Edge browser (Chromium-based)"""

    def __init__(self, db_path: str):
        """
        Initialize Edge parser

        Args:
            db_path: Path to History database file
        """
        # Edge uses the same format as Chrome
        super().__init__(db_path, browser_name="Edge")
