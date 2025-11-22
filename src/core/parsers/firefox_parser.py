"""
Firefox browser history parser
"""
from typing import List
from datetime import datetime

from .base_parser import BaseParser
from ..models import HistoryEntry, Download, Cookie, Bookmark, FormHistory
from ..timezone_utils import TimezoneConverter


class FirefoxParser(BaseParser):
    """Parser for Firefox browser"""

    def __init__(self, db_path: str):
        """
        Initialize Firefox parser

        Args:
            db_path: Path to places.sqlite database file
        """
        super().__init__(db_path)
        self.browser_name = "Firefox"

    def parse_history(self) -> List[HistoryEntry]:
        """
        Parse Firefox history from places.sqlite

        Returns:
            List of HistoryEntry objects
        """
        conn = self.connect()
        cursor = conn.cursor()

        entries = []

        try:
            query = """
            SELECT
                moz_places.id,
                moz_places.url,
                moz_places.title,
                moz_places.visit_count,
                moz_places.hidden,
                moz_places.typed,
                moz_places.last_visit_date,
                moz_places.favicon_id,
                moz_historyvisits.visit_date,
                moz_historyvisits.visit_type
            FROM moz_places
            LEFT JOIN moz_historyvisits ON moz_places.id = moz_historyvisits.place_id
            ORDER BY moz_historyvisits.visit_date DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                # Firefox stores timestamps in microseconds since Unix epoch
                visit_time = TimezoneConverter.firefox_timestamp_to_datetime(
                    row['visit_date'] if row['visit_date'] else row['last_visit_date']
                )
                last_visit = TimezoneConverter.firefox_timestamp_to_datetime(row['last_visit_date']) if row['last_visit_date'] else None

                entry = HistoryEntry(
                    id=row['id'],
                    url=row['url'] or "",
                    title=row['title'] or "",
                    visit_time=visit_time,
                    visit_count=row['visit_count'] or 0,
                    browser=self.browser_name,
                    typed_count=row['typed'] or 0,
                    last_visit_time=last_visit,
                    hidden=bool(row['hidden']),
                    favicon_id=row['favicon_id'],
                    source_file=str(self.db_path),
                    source_file_hash=self.file_hash
                )
                entries.append(entry)

        except Exception as e:
            print(f"Error parsing Firefox history: {e}")

        return entries

    def parse_downloads(self) -> List[Download]:
        """
        Parse Firefox downloads from places.sqlite

        Returns:
            List of Download objects
        """
        conn = self.connect()
        cursor = conn.cursor()

        downloads = []

        try:
            # Check if downloads annotation exists
            query = """
            SELECT
                moz_places.url,
                moz_annos.content,
                moz_annos.dateAdded,
                moz_annos.lastModified
            FROM moz_annos
            JOIN moz_anno_attributes ON moz_annos.anno_attribute_id = moz_anno_attributes.id
            JOIN moz_places ON moz_annos.place_id = moz_places.id
            WHERE moz_anno_attributes.name = 'downloads/destinationFileURI'
            ORDER BY moz_annos.dateAdded DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            for idx, row in enumerate(rows):
                start_time = TimezoneConverter.firefox_timestamp_to_datetime(row['dateAdded'])
                end_time = TimezoneConverter.firefox_timestamp_to_datetime(row['lastModified']) if row['lastModified'] else None

                download = Download(
                    id=idx,
                    url=row['url'] or "",
                    target_path=row['content'] or "",
                    start_time=start_time,
                    end_time=end_time,
                    total_bytes=0,  # Not available in places.sqlite
                    received_bytes=0,
                    state='unknown',
                    danger_type='',
                    browser=self.browser_name,
                    source_file=str(self.db_path)
                )
                downloads.append(download)

        except Exception as e:
            # Downloads may not be available in all Firefox versions
            pass

        return downloads

    def parse_bookmarks(self) -> List[Bookmark]:
        """
        Parse Firefox bookmarks from places.sqlite

        Returns:
            List of Bookmark objects
        """
        conn = self.connect()
        cursor = conn.cursor()

        bookmarks = []

        try:
            query = """
            SELECT
                moz_bookmarks.id,
                moz_bookmarks.title,
                moz_bookmarks.dateAdded,
                moz_bookmarks.parent,
                moz_places.url
            FROM moz_bookmarks
            JOIN moz_places ON moz_bookmarks.fk = moz_places.id
            WHERE moz_bookmarks.type = 1
            ORDER BY moz_bookmarks.dateAdded DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                date_added = TimezoneConverter.firefox_timestamp_to_datetime(row['dateAdded'])

                bookmark = Bookmark(
                    id=row['id'],
                    url=row['url'] or "",
                    title=row['title'] or "",
                    date_added=date_added,
                    parent_folder=str(row['parent']),
                    browser=self.browser_name,
                    source_file=str(self.db_path)
                )
                bookmarks.append(bookmark)

        except Exception as e:
            print(f"Error parsing Firefox bookmarks: {e}")

        return bookmarks

    def parse_form_history(self, formhistory_db_path: str = None) -> List[FormHistory]:
        """
        Parse Firefox form history (requires formhistory.sqlite)

        Args:
            formhistory_db_path: Path to formhistory.sqlite

        Returns:
            List of FormHistory objects
        """
        if not formhistory_db_path:
            return []

        form_entries = []

        try:
            from pathlib import Path
            if not Path(formhistory_db_path).exists():
                return form_entries

            import sqlite3
            conn = sqlite3.connect(f'file:{formhistory_db_path}?mode=ro', uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
            SELECT
                id,
                fieldname,
                value,
                timesUsed,
                firstUsed,
                lastUsed
            FROM moz_formhistory
            ORDER BY lastUsed DESC
            """

            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                first_used = TimezoneConverter.firefox_timestamp_to_datetime(row['firstUsed'])
                last_used = TimezoneConverter.firefox_timestamp_to_datetime(row['lastUsed'])

                form_entry = FormHistory(
                    id=row['id'],
                    field_name=row['fieldname'],
                    value=row['value'],
                    times_used=row['timesUsed'],
                    first_used=first_used,
                    last_used=last_used,
                    browser=self.browser_name,
                    source_file=formhistory_db_path
                )
                form_entries.append(form_entry)

            conn.close()

        except Exception as e:
            print(f"Error parsing Firefox form history: {e}")

        return form_entries
