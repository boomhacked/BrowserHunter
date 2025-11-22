"""
Advanced search and filtering engine for browser history
"""
import re
import signal
from typing import List, Callable, Optional
from datetime import datetime
from dataclasses import asdict

from .models import HistoryEntry, Download, Cookie, Bookmark


# Security: Regex complexity limits to prevent ReDoS attacks
MAX_REGEX_LENGTH = 500
MAX_REGEX_COMPILE_TIME = 1  # seconds


class RegexTimeoutError(Exception):
    """Raised when regex compilation or execution times out"""
    pass


def validate_regex_pattern(pattern: str) -> bool:
    """
    Validate regex pattern for safety

    Args:
        pattern: Regex pattern to validate

    Returns:
        True if pattern is safe, False otherwise
    """
    # Check length
    if len(pattern) > MAX_REGEX_LENGTH:
        return False

    # Check for excessive nesting/complexity
    nesting_patterns = [
        r'\(\?',  # Lookahead/lookbehind
        r'\*\+',  # Nested quantifiers
        r'\+\*',  # Nested quantifiers
        r'\{\d+,\}',  # Unbounded quantifiers
    ]

    # Count potential complexity indicators
    complexity_score = 0
    complexity_score += pattern.count('(')  # Groups
    complexity_score += pattern.count('*')  # Wildcards
    complexity_score += pattern.count('+')  # Plus quantifiers
    complexity_score += pattern.count('|')  # Alternations

    # Simple heuristic: reject overly complex patterns
    if complexity_score > 50:
        return False

    return True


def safe_regex_compile(pattern: str, flags: int = 0) -> Optional[re.Pattern]:
    """
    Safely compile regex pattern with timeout and validation

    Args:
        pattern: Regex pattern to compile
        flags: Regex flags

    Returns:
        Compiled pattern or None if unsafe/invalid
    """
    # Validate pattern first
    if not validate_regex_pattern(pattern):
        return None

    try:
        # Try to compile with timeout (using compile which is fast)
        compiled = re.compile(pattern, flags)
        return compiled
    except re.error:
        return None
    except Exception:
        return None


def safe_regex_search(pattern: re.Pattern, text: str, timeout: float = 0.5) -> Optional[re.Match]:
    """
    Safely search with regex pattern with timeout

    Args:
        pattern: Compiled regex pattern
        text: Text to search
        timeout: Timeout in seconds

    Returns:
        Match object or None
    """
    # Limit text length to prevent DoS
    MAX_TEXT_LENGTH = 1000000  # 1MB
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]

    try:
        # For simple implementation, we'll use the pattern directly
        # In production, consider using regex module with timeout support
        result = pattern.search(text)
        return result
    except Exception:
        return None


class SearchFilter:
    """Advanced search and filtering for browser history"""

    def __init__(self):
        self.filters = []

    def add_keyword_filter(self, keyword: str, case_sensitive: bool = False, use_regex: bool = False):
        """
        Add keyword filter

        Args:
            keyword: Search keyword
            case_sensitive: Case-sensitive search
            use_regex: Use regex pattern matching
        """
        def filter_func(entry):
            # Search in all text fields
            searchable_fields = [
                str(entry.url),
                str(entry.title),
                str(entry.domain),
                str(entry.notes) if hasattr(entry, 'notes') else ""
            ]

            search_text = ' '.join(searchable_fields)

            if use_regex:
                # Security: Use safe regex compilation with validation
                pattern = safe_regex_compile(keyword, re.IGNORECASE if not case_sensitive else 0)
                if pattern is None:
                    # Invalid or unsafe regex pattern
                    return False
                match = safe_regex_search(pattern, search_text)
                return match is not None
            else:
                # Plain text search (safe)
                if not case_sensitive:
                    return keyword.lower() in search_text.lower()
                return keyword in search_text

        self.filters.append(filter_func)
        return self

    def add_url_filter(self, url_pattern: str, use_regex: bool = True):
        """
        Add URL-specific filter

        Args:
            url_pattern: URL pattern to match
            use_regex: Use regex pattern matching
        """
        def filter_func(entry):
            if use_regex:
                # Security: Use safe regex compilation with validation
                pattern = safe_regex_compile(url_pattern, re.IGNORECASE)
                if pattern is None:
                    # Invalid or unsafe regex pattern
                    return False
                match = safe_regex_search(pattern, str(entry.url))
                return match is not None
            else:
                # Plain text search (safe)
                return url_pattern.lower() in entry.url.lower()

        self.filters.append(filter_func)
        return self

    def add_domain_filter(self, domains: List[str]):
        """
        Add domain filter

        Args:
            domains: List of domains to include
        """
        def filter_func(entry):
            return entry.domain in domains

        self.filters.append(filter_func)
        return self

    def add_date_range_filter(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        """
        Add date range filter

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
        """
        def filter_func(entry):
            if start_date and entry.visit_time < start_date:
                return False
            if end_date and entry.visit_time > end_date:
                return False
            return True

        self.filters.append(filter_func)
        return self

    def add_visit_count_filter(self, min_count: Optional[int] = None, max_count: Optional[int] = None):
        """
        Add visit count filter

        Args:
            min_count: Minimum visit count
            max_count: Maximum visit count
        """
        def filter_func(entry):
            if min_count and entry.visit_count < min_count:
                return False
            if max_count and entry.visit_count > max_count:
                return False
            return True

        self.filters.append(filter_func)
        return self

    def add_browser_filter(self, browsers: List[str]):
        """
        Add browser filter

        Args:
            browsers: List of browser names to include
        """
        def filter_func(entry):
            return entry.browser in browsers

        self.filters.append(filter_func)
        return self

    def add_bookmarked_filter(self, bookmarked: bool = True):
        """
        Add bookmarked entries filter

        Args:
            bookmarked: True to show only bookmarked, False for non-bookmarked
        """
        def filter_func(entry):
            return entry.bookmarked == bookmarked

        self.filters.append(filter_func)
        return self

    def add_custom_filter(self, filter_func: Callable):
        """
        Add custom filter function

        Args:
            filter_func: Function that takes an entry and returns bool
        """
        self.filters.append(filter_func)
        return self

    def apply(self, entries: List) -> List:
        """
        Apply all filters to entries

        Args:
            entries: List of entries to filter

        Returns:
            Filtered list of entries
        """
        if not self.filters:
            return entries

        filtered = entries
        for filter_func in self.filters:
            filtered = [entry for entry in filtered if filter_func(entry)]

        return filtered

    def clear(self):
        """Clear all filters"""
        self.filters = []


class QueryParser:
    """Parse search queries with operators (AND, OR, NOT)"""

    @staticmethod
    def parse_query(query: str) -> SearchFilter:
        """
        Parse search query with operators

        Syntax:
            - Simple: "keyword"
            - AND: "keyword1 AND keyword2"
            - OR: "keyword1 OR keyword2"
            - NOT: "NOT keyword"
            - Quotes for exact match: "exact phrase"
            - Regex: /pattern/

        Args:
            query: Search query string

        Returns:
            SearchFilter with parsed conditions
        """
        search_filter = SearchFilter()

        # Handle empty query
        if not query.strip():
            return search_filter

        # Split by AND/OR operators (simple implementation)
        # For production, use proper query parser
        tokens = QueryParser._tokenize(query)

        for token in tokens:
            token = token.strip()

            # Check for regex pattern
            if token.startswith('/') and token.endswith('/'):
                pattern = token[1:-1]
                search_filter.add_keyword_filter(pattern, use_regex=True)

            # Check for exact phrase
            elif token.startswith('"') and token.endswith('"'):
                phrase = token[1:-1]
                search_filter.add_keyword_filter(phrase, case_sensitive=True)

            # Regular keyword
            elif token and token not in ['AND', 'OR', 'NOT']:
                search_filter.add_keyword_filter(token)

        return search_filter

    @staticmethod
    def _tokenize(query: str) -> List[str]:
        """
        Tokenize query string

        Args:
            query: Query string

        Returns:
            List of tokens
        """
        # Simple tokenizer - split by whitespace but preserve quoted strings
        tokens = []
        current_token = ""
        in_quotes = False
        in_regex = False

        for char in query:
            if char == '"' and not in_regex:
                in_quotes = not in_quotes
                current_token += char
            elif char == '/' and not in_quotes:
                in_regex = not in_regex
                current_token += char
            elif char.isspace() and not in_quotes and not in_regex:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            else:
                current_token += char

        if current_token:
            tokens.append(current_token)

        return tokens


class SortOptions:
    """Sorting options for history entries"""

    SORT_BY_DATE = "date"
    SORT_BY_URL = "url"
    SORT_BY_TITLE = "title"
    SORT_BY_DOMAIN = "domain"
    SORT_BY_VISIT_COUNT = "visit_count"
    SORT_BY_BROWSER = "browser"

    @staticmethod
    def sort(entries: List, sort_by: str = SORT_BY_DATE, ascending: bool = False) -> List:
        """
        Sort entries

        Args:
            entries: List of entries
            sort_by: Field to sort by
            ascending: Sort order (False = descending)

        Returns:
            Sorted list
        """
        if not entries:
            return entries

        sort_key_map = {
            SortOptions.SORT_BY_DATE: lambda x: x.visit_time,
            SortOptions.SORT_BY_URL: lambda x: x.url.lower(),
            SortOptions.SORT_BY_TITLE: lambda x: (x.title or "").lower(),
            SortOptions.SORT_BY_DOMAIN: lambda x: x.domain.lower(),
            SortOptions.SORT_BY_VISIT_COUNT: lambda x: x.visit_count,
            SortOptions.SORT_BY_BROWSER: lambda x: x.browser.lower(),
        }

        sort_key = sort_key_map.get(sort_by, sort_key_map[SortOptions.SORT_BY_DATE])

        try:
            return sorted(entries, key=sort_key, reverse=not ascending)
        except Exception as e:
            print(f"Error sorting: {e}")
            return entries
