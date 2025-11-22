"""
URL analysis and statistics for browser history
"""
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from urllib.parse import urlparse
import re

from .models import HistoryEntry


class URLAnalyzer:
    """Analyze URLs and extract insights"""

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""

    @staticmethod
    def extract_parameters(url: str) -> Dict[str, List[str]]:
        """Extract query parameters from URL"""
        try:
            from urllib.parse import parse_qs
            parsed = urlparse(url)
            return parse_qs(parsed.query)
        except:
            return {}

    @staticmethod
    def is_search_engine(url: str) -> bool:
        """Check if URL is a search engine"""
        search_engines = [
            'google.com', 'bing.com', 'yahoo.com', 'duckduckgo.com',
            'baidu.com', 'yandex.com', 'ask.com'
        ]
        domain = URLAnalyzer.extract_domain(url)
        return any(se in domain for se in search_engines)

    @staticmethod
    def extract_search_query(url: str) -> str:
        """Extract search query from search engine URL"""
        params = URLAnalyzer.extract_parameters(url)

        # Common search query parameter names
        query_params = ['q', 'query', 'search', 'p', 'text']

        for param in query_params:
            if param in params and params[param]:
                return params[param][0]

        return ""

    @staticmethod
    def group_by_domain(entries: List[HistoryEntry]) -> Dict[str, List[HistoryEntry]]:
        """Group entries by domain"""
        grouped = defaultdict(list)
        for entry in entries:
            grouped[entry.domain].append(entry)
        return dict(grouped)

    @staticmethod
    def get_top_domains(entries: List[HistoryEntry], limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get top visited domains

        Args:
            entries: List of history entries
            limit: Number of top domains to return

        Returns:
            List of (domain, visit_count) tuples
        """
        domain_counts = Counter()
        for entry in entries:
            domain_counts[entry.domain] += entry.visit_count

        return domain_counts.most_common(limit)

    @staticmethod
    def get_visit_frequency(entries: List[HistoryEntry]) -> Dict[str, int]:
        """
        Calculate visit frequency per domain

        Returns:
            Dictionary of {domain: total_visits}
        """
        frequency = defaultdict(int)
        for entry in entries:
            frequency[entry.domain] += entry.visit_count

        return dict(frequency)


class BrowserStatistics:
    """Generate statistics from browser history"""

    @staticmethod
    def get_total_visits(entries: List[HistoryEntry]) -> int:
        """Get total number of visits"""
        return sum(entry.visit_count for entry in entries)

    @staticmethod
    def get_unique_urls(entries: List[HistoryEntry]) -> int:
        """Get number of unique URLs"""
        return len(set(entry.url for entry in entries))

    @staticmethod
    def get_unique_domains(entries: List[HistoryEntry]) -> int:
        """Get number of unique domains"""
        return len(set(entry.domain for entry in entries))

    @staticmethod
    def get_date_range(entries: List[HistoryEntry]) -> Tuple[datetime, datetime]:
        """Get date range of history"""
        if not entries:
            return None, None

        dates = [entry.visit_time for entry in entries if entry.visit_time]
        if not dates:
            return None, None

        return min(dates), max(dates)

    @staticmethod
    def get_browser_distribution(entries: List[HistoryEntry]) -> Dict[str, int]:
        """Get distribution of entries by browser"""
        browser_counts = Counter()
        for entry in entries:
            browser_counts[entry.browser] += 1

        return dict(browser_counts)

    @staticmethod
    def get_most_visited_urls(entries: List[HistoryEntry], limit: int = 10) -> List[Tuple[str, str, int]]:
        """
        Get most visited URLs

        Args:
            entries: List of history entries
            limit: Number of top URLs to return

        Returns:
            List of (url, title, visit_count) tuples
        """
        # Group by URL to handle duplicates
        url_data = {}
        for entry in entries:
            if entry.url not in url_data:
                url_data[entry.url] = {
                    'title': entry.title,
                    'visits': entry.visit_count
                }
            else:
                url_data[entry.url]['visits'] += entry.visit_count

        # Sort by visit count
        sorted_urls = sorted(
            url_data.items(),
            key=lambda x: x[1]['visits'],
            reverse=True
        )

        return [(url, data['title'], data['visits']) for url, data in sorted_urls[:limit]]

    @staticmethod
    def get_activity_by_hour(entries: List[HistoryEntry]) -> Dict[int, int]:
        """
        Get browsing activity by hour of day

        Returns:
            Dictionary of {hour: visit_count}
        """
        hour_counts = defaultdict(int)
        for entry in entries:
            if entry.visit_time:
                hour = entry.visit_time.hour
                hour_counts[hour] += 1

        return dict(hour_counts)

    @staticmethod
    def get_activity_by_day_of_week(entries: List[HistoryEntry]) -> Dict[str, int]:
        """
        Get browsing activity by day of week

        Returns:
            Dictionary of {day_name: visit_count}
        """
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = defaultdict(int)

        for entry in entries:
            if entry.visit_time:
                day_idx = entry.visit_time.weekday()
                day_counts[day_names[day_idx]] += 1

        return dict(day_counts)

    @staticmethod
    def identify_duplicate_entries(entries: List[HistoryEntry]) -> List[List[HistoryEntry]]:
        """
        Identify potential duplicate entries (same URL)

        Returns:
            List of lists, where each inner list contains duplicate entries
        """
        url_groups = defaultdict(list)
        for entry in entries:
            url_groups[entry.url].append(entry)

        # Return only groups with more than one entry
        duplicates = [group for group in url_groups.values() if len(group) > 1]

        return duplicates

    @staticmethod
    def get_search_queries(entries: List[HistoryEntry]) -> List[Tuple[str, datetime]]:
        """
        Extract search queries from search engine URLs

        Returns:
            List of (query, timestamp) tuples
        """
        queries = []

        for entry in entries:
            if URLAnalyzer.is_search_engine(entry.url):
                query = URLAnalyzer.extract_search_query(entry.url)
                if query:
                    queries.append((query, entry.visit_time))

        return queries

    @staticmethod
    def identify_incognito_indicators(entries: List[HistoryEntry]) -> List[HistoryEntry]:
        """
        Identify entries that might indicate incognito/private browsing

        Note: Incognito mode doesn't save history, but we can identify:
        - Gaps in browsing activity
        - Single-visit entries in between heavy usage periods

        Returns:
            List of suspicious entries
        """
        # Simple heuristic: entries with exactly 1 visit count between high-activity periods
        suspicious = []

        for entry in entries:
            if entry.visit_count == 1 and entry.typed_count == 0:
                suspicious.append(entry)

        return suspicious

    @staticmethod
    def calculate_session_duration(entries: List[HistoryEntry], session_gap_minutes: int = 30) -> List[Dict]:
        """
        Calculate browsing sessions based on time gaps

        Args:
            entries: List of history entries (should be sorted by time)
            session_gap_minutes: Gap in minutes to consider a new session

        Returns:
            List of session dictionaries
        """
        if not entries:
            return []

        # Sort by visit time
        sorted_entries = sorted(entries, key=lambda x: x.visit_time)

        sessions = []
        current_session = {
            'start': sorted_entries[0].visit_time,
            'end': sorted_entries[0].visit_time,
            'entries': [sorted_entries[0]],
            'domains': set([sorted_entries[0].domain])
        }

        for i in range(1, len(sorted_entries)):
            entry = sorted_entries[i]
            prev_entry = sorted_entries[i - 1]

            # Calculate time gap
            time_gap = (entry.visit_time - prev_entry.visit_time).total_seconds() / 60

            if time_gap <= session_gap_minutes:
                # Same session
                current_session['end'] = entry.visit_time
                current_session['entries'].append(entry)
                current_session['domains'].add(entry.domain)
            else:
                # New session
                sessions.append(current_session)
                current_session = {
                    'start': entry.visit_time,
                    'end': entry.visit_time,
                    'entries': [entry],
                    'domains': set([entry.domain])
                }

        # Add last session
        sessions.append(current_session)

        # Calculate durations
        for session in sessions:
            duration = (session['end'] - session['start']).total_seconds() / 60
            session['duration_minutes'] = round(duration, 2)
            session['entry_count'] = len(session['entries'])
            session['unique_domains'] = len(session['domains'])
            session['domains'] = list(session['domains'])

        return sessions

    @staticmethod
    def generate_summary_report(entries: List[HistoryEntry]) -> Dict:
        """
        Generate comprehensive summary report

        Returns:
            Dictionary with various statistics
        """
        return {
            'total_entries': len(entries),
            'total_visits': BrowserStatistics.get_total_visits(entries),
            'unique_urls': BrowserStatistics.get_unique_urls(entries),
            'unique_domains': BrowserStatistics.get_unique_domains(entries),
            'date_range': BrowserStatistics.get_date_range(entries),
            'browser_distribution': BrowserStatistics.get_browser_distribution(entries),
            'top_domains': URLAnalyzer.get_top_domains(entries, limit=10),
            'most_visited': BrowserStatistics.get_most_visited_urls(entries, limit=10),
            'activity_by_hour': BrowserStatistics.get_activity_by_hour(entries),
            'activity_by_day': BrowserStatistics.get_activity_by_day_of_week(entries),
            'search_queries_count': len(BrowserStatistics.get_search_queries(entries)),
            'duplicate_groups': len(BrowserStatistics.identify_duplicate_entries(entries))
        }
