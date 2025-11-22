"""
Saved queries management
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


class SavedQueryManager:
    """Manage saved search queries and filters"""

    def __init__(self, storage_path: str = "data/saved_queries"):
        """
        Initialize saved query manager

        Args:
            storage_path: Path to store saved queries
        """
        # Security: Validate storage path to prevent directory traversal
        base_dir = os.getcwd()  # Application directory
        if not validate_storage_directory(storage_path, base_dir=base_dir):
            logger.error(f"Invalid storage path: {storage_path}")
            # Fall back to safe default
            storage_path = "data/saved_queries"
            logger.warning(f"Using default storage path: {storage_path}")

        self.storage_path = Path(storage_path).resolve()

        # Create directory with restrictive permissions
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True, mode=0o700)
            logger.info(f"Query storage initialized: {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {type(e).__name__}: {str(e)}")
            raise RuntimeError("Failed to initialize query storage")

        self.queries_file = self.storage_path / "queries.json"

        self.queries = self._load_queries()

    def _load_queries(self) -> Dict:
        """Load saved queries from file"""
        if self.queries_file.exists():
            try:
                with open(self.queries_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.debug(f"Loaded {len(data)} saved queries")
                    return data
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in queries file: {str(e)}")
                return {}
            except PermissionError as e:
                logger.error(f"Permission denied reading queries: {str(e)}")
                return {}
            except Exception as e:
                logger.error(f"Error loading queries: {type(e).__name__}: {str(e)}")
                return {}
        return {}

    def _save_queries(self):
        """Save queries to file"""
        with open(self.queries_file, 'w', encoding='utf-8') as f:
            json.dump(self.queries, f, indent=2, ensure_ascii=False)

    def save_query(self, name: str, query: str, filters: Optional[Dict] = None, description: str = ""):
        """
        Save a search query

        Args:
            name: Query name
            query: Search query string
            filters: Dictionary of filter settings
            description: Query description
        """
        self.queries[name] = {
            'query': query,
            'filters': filters or {},
            'description': description,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'use_count': 0
        }
        self._save_queries()

    def get_query(self, name: str) -> Optional[Dict]:
        """
        Get saved query

        Args:
            name: Query name

        Returns:
            Query dictionary or None
        """
        return self.queries.get(name)

    def update_query(self, name: str, query: str = None, filters: Dict = None, description: str = None):
        """
        Update existing query

        Args:
            name: Query name
            query: Updated query string
            filters: Updated filters
            description: Updated description
        """
        if name in self.queries:
            if query is not None:
                self.queries[name]['query'] = query
            if filters is not None:
                self.queries[name]['filters'] = filters
            if description is not None:
                self.queries[name]['description'] = description
            self.queries[name]['updated_at'] = datetime.now().isoformat()
            self._save_queries()

    def delete_query(self, name: str):
        """
        Delete saved query

        Args:
            name: Query name
        """
        if name in self.queries:
            del self.queries[name]
            self._save_queries()

    def increment_use_count(self, name: str):
        """
        Increment use count for a query

        Args:
            name: Query name
        """
        if name in self.queries:
            self.queries[name]['use_count'] += 1
            self._save_queries()

    def get_all_queries(self) -> Dict:
        """Get all saved queries"""
        return self.queries

    def get_query_names(self) -> List[str]:
        """Get list of query names"""
        return sorted(self.queries.keys())

    def get_most_used_queries(self, limit: int = 10) -> List[tuple]:
        """
        Get most frequently used queries

        Args:
            limit: Number of queries to return

        Returns:
            List of (name, query_data) tuples
        """
        sorted_queries = sorted(
            self.queries.items(),
            key=lambda x: x[1].get('use_count', 0),
            reverse=True
        )
        return sorted_queries[:limit]
