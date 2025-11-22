"""
Annotations and bookmarks management
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .security import validate_storage_directory

# Configure logging
logger = logging.getLogger(__name__)


class AnnotationManager:
    """Manage annotations and bookmarks for history entries"""

    def __init__(self, storage_path: str = "data/annotations"):
        """
        Initialize annotation manager

        Args:
            storage_path: Path to store annotations
        """
        # Security: Validate storage path to prevent directory traversal
        base_dir = os.getcwd()  # Application directory
        if not validate_storage_directory(storage_path, base_dir=base_dir):
            logger.error(f"Invalid storage path: {storage_path}")
            # Fall back to safe default
            storage_path = "data/annotations"
            logger.warning(f"Using default storage path: {storage_path}")

        self.storage_path = Path(storage_path).resolve()

        # Create directory with restrictive permissions
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True, mode=0o700)
            logger.info(f"Annotation storage initialized: {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {type(e).__name__}: {str(e)}")
            raise RuntimeError("Failed to initialize annotation storage")

        self.annotations_file = self.storage_path / "annotations.json"
        self.bookmarks_file = self.storage_path / "bookmarks.json"

        self.annotations = self._load_annotations()
        self.bookmarks = self._load_bookmarks()

    def _load_annotations(self) -> Dict:
        """Load annotations from file"""
        if self.annotations_file.exists():
            try:
                with open(self.annotations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.debug(f"Loaded {len(data)} annotations")
                    return data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in annotations file: {str(e)}")
                return {}
            except PermissionError as e:
                logger.error(f"Permission denied reading annotations: {str(e)}")
                return {}
            except Exception as e:
                logger.error(f"Error loading annotations: {type(e).__name__}: {str(e)}")
                return {}
        return {}

    def _load_bookmarks(self) -> Dict:
        """Load bookmarks from file"""
        if self.bookmarks_file.exists():
            try:
                with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.debug(f"Loaded {len(data)} bookmarks")
                    return data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in bookmarks file: {str(e)}")
                return {}
            except PermissionError as e:
                logger.error(f"Permission denied reading bookmarks: {str(e)}")
                return {}
            except Exception as e:
                logger.error(f"Error loading bookmarks: {type(e).__name__}: {str(e)}")
                return {}
        return {}

    def _save_annotations(self):
        """Save annotations to file"""
        with open(self.annotations_file, 'w', encoding='utf-8') as f:
            json.dump(self.annotations, f, indent=2, ensure_ascii=False)

    def _save_bookmarks(self):
        """Save bookmarks to file"""
        with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
            json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)

    def add_annotation(self, entry_id: str, note: str, tags: Optional[List[str]] = None):
        """
        Add annotation to an entry

        Args:
            entry_id: Unique identifier for the entry (combination of URL + timestamp)
            note: Annotation text
            tags: Optional list of tags
        """
        self.annotations[entry_id] = {
            'note': note,
            'tags': tags or [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self._save_annotations()

    def get_annotation(self, entry_id: str) -> Optional[Dict]:
        """
        Get annotation for an entry

        Args:
            entry_id: Entry identifier

        Returns:
            Annotation dictionary or None
        """
        return self.annotations.get(entry_id)

    def update_annotation(self, entry_id: str, note: str = None, tags: List[str] = None):
        """
        Update existing annotation

        Args:
            entry_id: Entry identifier
            note: Updated note text
            tags: Updated tags
        """
        if entry_id in self.annotations:
            if note is not None:
                self.annotations[entry_id]['note'] = note
            if tags is not None:
                self.annotations[entry_id]['tags'] = tags
            self.annotations[entry_id]['updated_at'] = datetime.now().isoformat()
            self._save_annotations()

    def delete_annotation(self, entry_id: str):
        """
        Delete annotation

        Args:
            entry_id: Entry identifier
        """
        if entry_id in self.annotations:
            del self.annotations[entry_id]
            self._save_annotations()

    def add_bookmark(self, entry_id: str, url: str, title: str):
        """
        Bookmark an entry

        Args:
            entry_id: Entry identifier
            url: Entry URL
            title: Entry title
        """
        self.bookmarks[entry_id] = {
            'url': url,
            'title': title,
            'bookmarked_at': datetime.now().isoformat()
        }
        self._save_bookmarks()

    def remove_bookmark(self, entry_id: str):
        """
        Remove bookmark

        Args:
            entry_id: Entry identifier
        """
        if entry_id in self.bookmarks:
            del self.bookmarks[entry_id]
            self._save_bookmarks()

    def is_bookmarked(self, entry_id: str) -> bool:
        """Check if entry is bookmarked"""
        return entry_id in self.bookmarks

    def get_all_bookmarks(self) -> Dict:
        """Get all bookmarks"""
        return self.bookmarks

    def get_entries_by_tag(self, tag: str) -> List[str]:
        """
        Get entry IDs by tag

        Args:
            tag: Tag to search for

        Returns:
            List of entry IDs
        """
        return [
            entry_id for entry_id, data in self.annotations.items()
            if tag in data.get('tags', [])
        ]

    def get_all_tags(self) -> List[str]:
        """Get all unique tags"""
        tags = set()
        for data in self.annotations.values():
            tags.update(data.get('tags', []))
        return sorted(list(tags))

    @staticmethod
    def generate_entry_id(url: str, visit_time: datetime) -> str:
        """
        Generate unique entry ID

        Args:
            url: Entry URL
            visit_time: Visit timestamp

        Returns:
            Unique ID string
        """
        import hashlib
        unique_str = f"{url}_{visit_time.isoformat()}"
        # Use SHA256 instead of MD5 for better collision resistance
        return hashlib.sha256(unique_str.encode()).hexdigest()
