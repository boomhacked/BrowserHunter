"""
Generic SQLite database parser
Discovers and extracts all tables and columns from any SQLite database
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from ..models import calculate_file_hash
from ...utils.security import validate_database_path
import tempfile
import shutil
import os
import stat

logger = logging.getLogger(__name__)


class GenericSQLiteParser:
    """Generic SQLite database parser that discovers all tables dynamically"""

    def __init__(self, db_path: str):
        """
        Initialize parser with database path

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._valid_tables: Optional[List[str]] = None  # Cache of valid table names
        self.file_hash = ""
        self.temp_db_path = None
        self._conn = None
        self.browser_type = None  # Will be auto-detected

        # Security: Validate database path (relaxed to allow files without .db extension)
        if not self.db_path.exists():
            raise ValueError(f"Database file does not exist: {self.db_path}")

        if not self.db_path.is_file():
            raise ValueError("Database path must be a regular file")

        if not os.access(self.db_path, os.R_OK):
            raise PermissionError("Database file is not readable")

        # Calculate file hash for integrity
        try:
            self.file_hash = calculate_file_hash(str(self.db_path))
            logger.info(f"Database loaded, hash: {self.file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to calculate file hash: {type(e).__name__}")
            raise ValueError("Failed to verify file integrity")

        # Detect browser type
        self.browser_type = self._detect_browser_type()

    def _detect_browser_type(self) -> str:
        """
        Auto-detect browser type based on filename and table structure

        Returns:
            Browser type: 'Chrome', 'Edge', 'Firefox', or 'Unknown'
        """
        filename = self.db_path.name.lower()

        # Check filename patterns
        if 'places.sqlite' in filename:
            return 'Firefox'
        elif 'history' in filename:
            # Could be Chrome or Edge, check parent directory
            parent = str(self.db_path.parent).lower()
            if 'chrome' in parent:
                return 'Chrome'
            elif 'edge' in parent:
                return 'Edge'
            else:
                # Check tables to determine
                try:
                    # Use temp connection to avoid threading issues
                    conn = self._get_temp_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT name FROM sqlite_master
                        WHERE type='table'
                        AND name NOT LIKE 'sqlite_%'
                        ORDER BY name
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                    conn.close()

                    # Chrome/Edge have 'urls', 'visits' tables
                    # Firefox has 'moz_places', 'moz_historyvisits'
                    if 'moz_places' in tables or 'moz_historyvisits' in tables:
                        return 'Firefox'
                    elif 'urls' in tables and 'visits' in tables:
                        return 'Chrome'  # Default to Chrome for Chromium-based
                except:
                    pass

        return 'Unknown'

    def _create_temp_copy(self) -> str:
        """
        Create a temporary copy of the database

        Returns:
            Path to temporary database
        """
        try:
            temp_dir = Path(tempfile.gettempdir()) / "BrowserHunter"

            if not temp_dir.exists():
                temp_dir.mkdir(mode=0o700, exist_ok=True)
            else:
                current_mode = temp_dir.stat().st_mode
                if stat.S_IMODE(current_mode) != 0o700:
                    os.chmod(temp_dir, 0o700)

            fd = None
            try:
                fd = tempfile.NamedTemporaryFile(
                    mode='w+b',
                    delete=False,
                    dir=temp_dir,
                    suffix='.db',
                    prefix='generic_'
                )
                temp_path = fd.name

                with open(self.db_path, 'rb') as source:
                    shutil.copyfileobj(source, fd)

                fd.close()
                fd = None

                os.chmod(temp_path, 0o600)
                logger.debug(f"Created temp copy: {Path(temp_path).name}")

            finally:
                if fd is not None:
                    try:
                        fd.close()
                    except:
                        pass

            # Copy WAL and SHM files if they exist
            for ext in ['-wal', '-shm']:
                wal_path = Path(str(self.db_path) + ext)
                if wal_path.exists():
                    try:
                        wal_temp_path = temp_path + ext
                        shutil.copy2(wal_path, wal_temp_path)
                        os.chmod(wal_temp_path, 0o600)
                    except Exception as e:
                        logger.warning(f"Failed to copy {ext} file: {type(e).__name__}")

            return temp_path

        except Exception as e:
            logger.error(f"Failed to create temp copy: {type(e).__name__}: {str(e)}")
            raise RuntimeError("Failed to create temporary database copy")

    def _get_temp_connection(self) -> sqlite3.Connection:
        """Get a temporary read-only connection without storing it"""
        temp_path = self._create_temp_copy()
        conn = sqlite3.connect(f'file:{temp_path}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        # Clean up temp file when connection is closed
        original_close = conn.close

        def close_with_cleanup():
            try:
                original_close()
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

        conn.close = close_with_cleanup
        return conn

    def connect(self) -> sqlite3.Connection:
        """
        Connect to database in read-only mode

        Returns:
            SQLite connection object
        """
        if self._conn:
            return self._conn

        self.temp_db_path = self._create_temp_copy()
        conn = sqlite3.connect(f'file:{self.temp_db_path}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        self._conn = conn
        return conn

    def close(self):
        """Close database connection and cleanup temp files"""
        if self._conn:
            try:
                self._conn.close()
                logger.debug("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {type(e).__name__}")
            finally:
                self._conn = None

        if self.temp_db_path and os.path.exists(self.temp_db_path):
            try:
                os.unlink(self.temp_db_path)
                logger.debug(f"Cleaned up temp file")
            except Exception as e:
                logger.error(f"Error cleaning up: {type(e).__name__}")

            for ext in ['-wal', '-shm']:
                wal_path = self.temp_db_path + ext
                if os.path.exists(wal_path):
                    try:
                        os.unlink(wal_path)
                    except:
                        pass

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def _validate_table_name(self, table_name: str) -> bool:
        """
        Validate that a table name exists in the database (security check)

        Args:
            table_name: Table name to validate

        Returns:
            True if table exists, False otherwise
        """
        if self._valid_tables is None:
            self._valid_tables = self.get_tables()
        return table_name in self._valid_tables

    def get_tables(self) -> List[str]:
        """
        Get list of all tables in the database

        Returns:
            List of table names
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        self._valid_tables = tables  # Cache for validation
        logger.info(f"Found {len(tables)} tables in database")
        return tables

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get column information for a table

        Args:
            table_name: Name of the table

        Returns:
            List of column info dicts with keys: cid, name, type, notnull, dflt_value, pk
        """
        # Security: Validate table name
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'cid': row[0],
                'name': row[1],
                'type': row[2],
                'notnull': row[3],
                'dflt_value': row[4],
                'pk': row[5]
            })
        return columns

    def get_column_names(self, table_name: str) -> List[str]:
        """
        Get column names for a table

        Args:
            table_name: Name of the table

        Returns:
            List of column names
        """
        columns_info = self.get_table_info(table_name)
        return [col['name'] for col in columns_info]

    def get_table_data(self, table_name: str, limit: Optional[int] = None,
                       offset: int = 0) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Get data from a table

        Args:
            table_name: Name of the table
            limit: Maximum number of rows to return
            offset: Number of rows to skip

        Returns:
            Tuple of (column_names, rows) where rows is list of dicts
        """
        # Security: Validate table name
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        conn = self.connect()
        cursor = conn.cursor()

        # Get column names
        columns = self.get_column_names(table_name)

        # Build query (table_name is validated above)
        query = f"SELECT * FROM {table_name}"
        if limit:
            # Security: Validate limit and offset are non-negative integers
            limit = max(0, int(limit))
            offset = max(0, int(offset))
            query += f" LIMIT {limit} OFFSET {offset}"

        cursor.execute(query)
        rows = []
        for row in cursor.fetchall():
            row_dict = {}
            for idx, col_name in enumerate(columns):
                value = row[idx]
                # Convert bytes to string if needed
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8')
                    except:
                        value = str(value)
                row_dict[col_name] = value
            rows.append(row_dict)

        logger.info(f"Retrieved {len(rows)} rows from table '{table_name}'")
        return columns, rows

    def get_row_count(self, table_name: str) -> int:
        """
        Get total row count for a table

        Args:
            table_name: Name of the table

        Returns:
            Row count
        """
        # Security: Validate table name
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        return count

    def search_table(self, table_name: str, search_term: str,
                     columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for a term across specified columns in a table

        Args:
            table_name: Name of the table
            search_term: Search term
            columns: List of column names to search (None = all text columns)

        Returns:
            List of matching rows as dicts
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Get all columns if not specified
        if columns is None:
            columns = self.get_column_names(table_name)

        # Build WHERE clause for text search
        where_conditions = []
        for col in columns:
            where_conditions.append(f"{col} LIKE ?")

        where_clause = " OR ".join(where_conditions)
        query = f"SELECT * FROM {table_name} WHERE {where_clause}"

        # Execute with parameters (% wildcards for LIKE)
        params = [f"%{search_term}%" for _ in columns]
        cursor.execute(query, params)

        rows = []
        all_columns = self.get_column_names(table_name)
        for row in cursor.fetchall():
            row_dict = {}
            for idx, col_name in enumerate(all_columns):
                value = row[idx]
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8')
                    except:
                        value = str(value)
                row_dict[col_name] = value
            rows.append(row_dict)

        return rows

    def get_database_info(self) -> Dict[str, Any]:
        """
        Get overall database information

        Returns:
            Dict with database metadata
        """
        tables = self.get_tables()
        info = {
            'file_path': str(self.db_path),
            'file_name': self.db_path.name,
            'file_size': self.db_path.stat().st_size,
            'file_hash': self.file_hash,
            'browser_type': self.browser_type,
            'table_count': len(tables),
            'tables': []
        }

        for table in tables:
            row_count = self.get_row_count(table)
            columns = self.get_column_names(table)
            info['tables'].append({
                'name': table,
                'row_count': row_count,
                'column_count': len(columns),
                'columns': columns
            })

        return info
