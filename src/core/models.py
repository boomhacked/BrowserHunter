"""
Data models for browser history entries
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import hashlib


@dataclass
class HistoryEntry:
    """Represents a single browser history entry"""
    id: int
    url: str
    title: Optional[str]
    visit_time: datetime
    visit_count: int
    browser: str  # chrome, firefox, edge
    typed_count: int = 0
    last_visit_time: Optional[datetime] = None
    hidden: bool = False
    favicon_id: Optional[int] = None

    # Extended fields
    domain: str = field(default="")
    url_params: Dict[str, Any] = field(default_factory=dict)

    # Forensic metadata
    source_file: str = ""
    source_file_hash: str = ""
    is_deleted: bool = False

    # User annotations
    notes: str = ""
    bookmarked: bool = False
    tags: list = field(default_factory=list)

    def __post_init__(self):
        """Extract domain and URL parameters"""
        if self.url:
            parsed = urlparse(self.url)
            self.domain = parsed.netloc
            self.url_params = parse_qs(parsed.query)


@dataclass
class Download:
    """Represents a download entry"""
    id: int
    url: str
    target_path: str
    start_time: datetime
    end_time: Optional[datetime]
    total_bytes: int
    received_bytes: int
    state: str  # complete, interrupted, cancelled
    danger_type: str
    browser: str
    source_file: str = ""
    mime_type: str = ""


@dataclass
class Cookie:
    """Represents a browser cookie"""
    host_key: str
    name: str
    value: str
    path: str
    creation_utc: datetime
    expires_utc: Optional[datetime]
    last_access_utc: datetime
    is_secure: bool
    is_httponly: bool
    has_expires: bool
    is_persistent: bool
    browser: str
    source_file: str = ""


@dataclass
class Bookmark:
    """Represents a bookmark"""
    id: int
    url: str
    title: str
    date_added: datetime
    parent_folder: str
    browser: str
    source_file: str = ""


@dataclass
class FormHistory:
    """Represents autofill/form history"""
    id: int
    field_name: str
    value: str
    times_used: int
    first_used: datetime
    last_used: datetime
    browser: str
    source_file: str = ""


@dataclass
class BrowserSession:
    """Represents a browsing session (group of related visits)"""
    session_id: int
    start_time: datetime
    end_time: datetime
    entries: list
    browser: str
    total_visits: int = 0
    duration_minutes: int = 0


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file for integrity verification"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        return f"ERROR: {str(e)}"
