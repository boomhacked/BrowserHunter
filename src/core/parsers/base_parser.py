"""
Base parser class for browser history
"""
import sqlite3
import shutil
import stat
import logging
from pathlib import Path
from typing import List, Optional
from abc import ABC, abstractmethod
import tempfile
import os

from ..models import HistoryEntry, Download, Cookie, Bookmark, calculate_file_hash
from ...utils.security import validate_database_path

# Configure logging
logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Base class for browser history parsers"""

    def __init__(self, db_path: str):
        """
        Initialize parser with database path

        Args:
            db_path: Path to browser database file
        """
        self.db_path = Path(db_path)
        self.file_hash = ""
        self.temp_db_path = None
        self._conn = None

        # Security: Validate database path
        if not validate_database_path(str(db_path)):
            logger.error("Invalid or unsafe database path")
            raise ValueError("Invalid or unsafe database path. File must be a regular database file.")

        # Verify it's a regular file (not symlink, directory, etc.)
        if not self.db_path.is_file():
            logger.error(f"Path is not a regular file: {self.db_path.name}")
            raise ValueError("Database path must be a regular file")

        # Check file is readable
        if not os.access(self.db_path, os.R_OK):
            logger.error(f"Database file is not readable: {self.db_path.name}")
            raise PermissionError("Database file is not readable")

        # Calculate file hash for integrity
        try:
            self.file_hash = calculate_file_hash(str(self.db_path))
            logger.info(f"Database loaded, hash: {self.file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to calculate file hash: {type(e).__name__}")
            raise ValueError("Failed to verify file integrity")

    def _create_temp_copy(self) -> str:
        """
        Create a temporary copy of the database for read-only access

        Security: Uses secure temp directory with restricted permissions
        and atomic file operations to prevent race conditions.

        Returns:
            Path to temporary database
        """
        try:
            # Security: Create secure temp directory with restrictive permissions
            temp_dir = Path(tempfile.gettempdir()) / "BrowserHunter"

            if not temp_dir.exists():
                # Create with restricted permissions (owner only: rwx------)
                temp_dir.mkdir(mode=0o700, exist_ok=True)
                logger.info(f"Created secure temp directory: {temp_dir}")
            else:
                # Verify existing directory has secure permissions
                current_mode = temp_dir.stat().st_mode
                if stat.S_IMODE(current_mode) != 0o700:
                    # Fix permissions if not secure
                    os.chmod(temp_dir, 0o700)
                    logger.warning(f"Fixed insecure permissions on temp directory")

            # Security: Create temp file with secure permissions
            # Use file descriptor to avoid race conditions
            fd = None
            try:
                # Create unique temp file atomically
                fd = tempfile.NamedTemporaryFile(
                    mode='w+b',
                    delete=False,
                    dir=temp_dir,
                    suffix='.db',
                    prefix='bhh_'
                )
                temp_path = fd.name

                # Security: Copy data while keeping file descriptor open
                # This prevents TOCTOU race conditions
                with open(self.db_path, 'rb') as source:
                    shutil.copyfileobj(source, fd)

                # Close file descriptor
                fd.close()
                fd = None

                # Set restrictive permissions on temp file (owner read/write only)
                os.chmod(temp_path, 0o600)

                logger.debug(f"Created secure temp copy: {Path(temp_path).name}")

            finally:
                if fd is not None:
                    try:
                        fd.close()
                    except:
                        pass

            # Also copy WAL and SHM files if they exist (for SQLite)
            for ext in ['-wal', '-shm']:
                wal_path = Path(str(self.db_path) + ext)
                if wal_path.exists():
                    try:
                        wal_temp_path = temp_path + ext
                        shutil.copy2(wal_path, wal_temp_path)
                        os.chmod(wal_temp_path, 0o600)
                        logger.debug(f"Copied WAL/SHM file: {ext}")
                    except Exception as e:
                        logger.warning(f"Failed to copy {ext} file: {type(e).__name__}")
                        # Continue even if WAL/SHM copy fails

            return temp_path

        except Exception as e:
            logger.error(f"Failed to create temp copy: {type(e).__name__}: {str(e)}")
            raise RuntimeError("Failed to create temporary database copy")

    def connect(self) -> sqlite3.Connection:
        """
        Connect to database in read-only mode

        Returns:
            SQLite connection object
        """
        if self._conn:
            return self._conn

        # Create temporary copy to avoid locking issues
        self.temp_db_path = self._create_temp_copy()

        # Open in read-only mode
        conn = sqlite3.connect(f'file:{self.temp_db_path}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        self._conn = conn
        return conn

    def close(self):
        """Close database connection and cleanup temp files"""
        # Close database connection
        if self._conn:
            try:
                self._conn.close()
                logger.debug("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {type(e).__name__}: {str(e)}")
            finally:
                self._conn = None

        # Clean up temporary files
        if self.temp_db_path and os.path.exists(self.temp_db_path):
            try:
                os.unlink(self.temp_db_path)
                logger.debug(f"Cleaned up temp file: {Path(self.temp_db_path).name}")
            except PermissionError as e:
                logger.error(f"Permission denied cleaning up temp file: {str(e)}")
            except OSError as e:
                logger.error(f"OS error cleaning up temp file: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error cleaning up temp file: {type(e).__name__}: {str(e)}")

            # Clean up WAL and SHM files
            for ext in ['-wal', '-shm']:
                wal_path = self.temp_db_path + ext
                if os.path.exists(wal_path):
                    try:
                        os.unlink(wal_path)
                        logger.debug(f"Cleaned up {ext} file")
                    except Exception as e:
                        logger.warning(f"Failed to clean up {ext} file: {type(e).__name__}")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    @abstractmethod
    def parse_history(self) -> List[HistoryEntry]:
        """
        Parse browser history

        Returns:
            List of HistoryEntry objects
        """
        pass

    @abstractmethod
    def parse_downloads(self) -> List[Download]:
        """
        Parse download history

        Returns:
            List of Download objects
        """
        pass

    def parse_cookies(self) -> List[Cookie]:
        """
        Parse cookies (optional, not all browsers store in same DB)

        Returns:
            List of Cookie objects
        """
        return []

    def parse_bookmarks(self) -> List[Bookmark]:
        """
        Parse bookmarks (optional, may be in separate file)

        Returns:
            List of Bookmark objects
        """
        return []

    def get_table_names(self) -> List[str]:
        """Get list of all tables in database"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]

    def get_table_schema(self, table_name: str) -> str:
        """Get schema for a specific table"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        result = cursor.fetchone()
        return result[0] if result else ""
