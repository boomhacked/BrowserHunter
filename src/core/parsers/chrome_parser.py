"""
Chrome/Chromium browser history parser
"""
from typing import List
from datetime import datetime

from .base_parser import BaseParser
from ..models import HistoryEntry, Download, Cookie
from ..timezone_utils import TimezoneConverter


class ChromeParser(BaseParser):
    """Parser for Chrome/Chromium-based browsers (Chrome, Edge, Brave, Opera, etc.)"""

    def __init__(self, db_path: str, browser_name: str = "Chrome"):
        """
        Initialize Chrome parser

        Args:
            db_path: Path to History database file
            browser_name: Name of the browser (Chrome, Edge, etc.)
        """
        super().__init__(db_path)
        self.browser_name = browser_name

    def parse_history(self) -> List[HistoryEntry]:
        """
        Parse Chrome history from History database

        Returns:
            List of HistoryEntry objects
        """
        conn = self.connect()
        cursor = conn.cursor()

        entries = []

        try:
            # Query history
            query = """
            SELECT
                urls.id,
                urls.url,
                urls.title,
                urls.visit_count,
                urls.typed_count,
                urls.last_visit_time,
                urls.hidden,
                visits.visit_time,
                visits.visit_duration,
                visits.transition
            FROM urls
            LEFT JOIN visits ON urls.id = visits.url
            ORDER BY visits.visit_time DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                # Convert Chrome timestamp to datetime
                visit_time = TimezoneConverter.chrome_timestamp_to_datetime(
                    row['visit_time'] if row['visit_time'] else row['last_visit_time']
                )
                last_visit = TimezoneConverter.chrome_timestamp_to_datetime(row['last_visit_time'])

                entry = HistoryEntry(
                    id=row['id'],
                    url=row['url'] or "",
                    title=row['title'] or "",
                    visit_time=visit_time,
                    visit_count=row['visit_count'] or 0,
                    browser=self.browser_name,
                    typed_count=row['typed_count'] or 0,
                    last_visit_time=last_visit,
                    hidden=bool(row['hidden']),
                    source_file=str(self.db_path),
                    source_file_hash=self.file_hash
                )
                entries.append(entry)

        except Exception as e:
            print(f"Error parsing Chrome history: {e}")

        return entries

    def parse_downloads(self) -> List[Download]:
        """
        Parse Chrome downloads

        Returns:
            List of Download objects
        """
        conn = self.connect()
        cursor = conn.cursor()

        downloads = []

        try:
            # Check if downloads table exists
            if 'downloads' not in self.get_table_names():
                return downloads

            query = """
            SELECT
                id,
                current_path,
                target_path,
                start_time,
                end_time,
                received_bytes,
                total_bytes,
                state,
                danger_type,
                interrupt_reason,
                opened,
                last_access_time,
                mime_type,
                original_mime_type,
                tab_url,
                tab_referrer_url
            FROM downloads
            ORDER BY start_time DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                start_time = TimezoneConverter.chrome_timestamp_to_datetime(row['start_time'])
                end_time = TimezoneConverter.chrome_timestamp_to_datetime(row['end_time']) if row['end_time'] else None

                # Map state codes to readable strings
                state_map = {0: 'in_progress', 1: 'complete', 2: 'cancelled', 3: 'interrupted'}
                state = state_map.get(row['state'], 'unknown')

                download = Download(
                    id=row['id'],
                    url=row['tab_url'] or row['tab_referrer_url'] or "",
                    target_path=row['target_path'] or row['current_path'] or "",
                    start_time=start_time,
                    end_time=end_time,
                    total_bytes=row['total_bytes'] or 0,
                    received_bytes=row['received_bytes'] or 0,
                    state=state,
                    danger_type=str(row['danger_type']),
                    browser=self.browser_name,
                    source_file=str(self.db_path),
                    mime_type=row['mime_type'] or row['original_mime_type'] or ""
                )
                downloads.append(download)

        except Exception as e:
            print(f"Error parsing Chrome downloads: {e}")

        return downloads

    def parse_cookies(self, cookies_db_path: str = None) -> List[Cookie]:
        """
        Parse Chrome cookies (requires separate Cookies database)

        Args:
            cookies_db_path: Path to Cookies database file

        Returns:
            List of Cookie objects
        """
        if not cookies_db_path:
            return []

        cookies = []

        try:
            # Create a temporary parser for cookies DB
            from pathlib import Path
            if not Path(cookies_db_path).exists():
                return cookies

            import sqlite3
            conn = sqlite3.connect(f'file:{cookies_db_path}?mode=ro', uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
            SELECT
                host_key,
                name,
                value,
                path,
                creation_utc,
                expires_utc,
                last_access_utc,
                is_secure,
                is_httponly,
                has_expires,
                is_persistent
            FROM cookies
            ORDER BY last_access_utc DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                creation = TimezoneConverter.chrome_timestamp_to_datetime(row['creation_utc'])
                expires = TimezoneConverter.chrome_timestamp_to_datetime(row['expires_utc']) if row['expires_utc'] else None
                last_access = TimezoneConverter.chrome_timestamp_to_datetime(row['last_access_utc'])

                cookie = Cookie(
                    host_key=row['host_key'],
                    name=row['name'],
                    value=row['value'],
                    path=row['path'],
                    creation_utc=creation,
                    expires_utc=expires,
                    last_access_utc=last_access,
                    is_secure=bool(row['is_secure']),
                    is_httponly=bool(row['is_httponly']),
                    has_expires=bool(row['has_expires']),
                    is_persistent=bool(row['is_persistent']),
                    browser=self.browser_name,
                    source_file=cookies_db_path
                )
                cookies.append(cookie)

            conn.close()

        except Exception as e:
            print(f"Error parsing Chrome cookies: {e}")

        return cookies
