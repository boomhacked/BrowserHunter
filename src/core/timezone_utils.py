"""
Timezone conversion utilities for browser history timestamps
"""
from datetime import datetime, timezone
import pytz
from typing import Optional


class TimezoneConverter:
    """Handle timezone conversions for browser history timestamps"""

    # Common timezones for forensic analysis
    COMMON_TIMEZONES = {
        'UTC': 'UTC',
        'US/Eastern': 'US/Eastern',
        'US/Central': 'US/Central',
        'US/Mountain': 'US/Mountain',
        'US/Pacific': 'US/Pacific',
        'Europe/London': 'Europe/London',
        'Europe/Paris': 'Europe/Paris',
        'Europe/Berlin': 'Europe/Berlin',
        'Asia/Tokyo': 'Asia/Tokyo',
        'Asia/Shanghai': 'Asia/Shanghai',
        'Asia/Dubai': 'Asia/Dubai',
        'Australia/Sydney': 'Australia/Sydney',
        'America/New_York': 'America/New_York',
        'America/Los_Angeles': 'America/Los_Angeles',
        'America/Chicago': 'America/Chicago',
    }

    @staticmethod
    def chrome_timestamp_to_datetime(chrome_timestamp: int) -> datetime:
        """
        Convert Chrome timestamp (microseconds since Jan 1, 1601) to datetime

        Args:
            chrome_timestamp: Chrome/WebKit timestamp in microseconds

        Returns:
            datetime object in UTC
        """
        if chrome_timestamp == 0:
            return datetime.fromtimestamp(0, tz=timezone.utc)

        # Chrome epoch starts at 1601-01-01
        # Unix epoch starts at 1970-01-01
        # Difference is 11644473600 seconds
        EPOCH_DIFF = 11644473600

        try:
            timestamp_seconds = (chrome_timestamp / 1000000) - EPOCH_DIFF
            return datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
        except (ValueError, OSError):
            return datetime.fromtimestamp(0, tz=timezone.utc)

    @staticmethod
    def firefox_timestamp_to_datetime(firefox_timestamp: int) -> datetime:
        """
        Convert Firefox timestamp (microseconds since Unix epoch) to datetime

        Args:
            firefox_timestamp: Firefox timestamp in microseconds

        Returns:
            datetime object in UTC
        """
        if firefox_timestamp == 0:
            return datetime.fromtimestamp(0, tz=timezone.utc)

        try:
            timestamp_seconds = firefox_timestamp / 1000000
            return datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
        except (ValueError, OSError):
            return datetime.fromtimestamp(0, tz=timezone.utc)

    @staticmethod
    def unix_timestamp_to_datetime(unix_timestamp: int) -> datetime:
        """
        Convert Unix timestamp (seconds since Unix epoch) to datetime

        Args:
            unix_timestamp: Unix timestamp in seconds

        Returns:
            datetime object in UTC
        """
        if unix_timestamp == 0:
            return datetime.fromtimestamp(0, tz=timezone.utc)

        try:
            return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
        except (ValueError, OSError):
            return datetime.fromtimestamp(0, tz=timezone.utc)

    @staticmethod
    def convert_timezone(dt: datetime, target_tz: str) -> datetime:
        """
        Convert datetime to target timezone

        Args:
            dt: datetime object (assumed to be UTC if naive)
            target_tz: Target timezone string (e.g., 'US/Eastern')

        Returns:
            datetime object in target timezone
        """
        if dt is None:
            return None

        # If naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        try:
            target_timezone = pytz.timezone(target_tz)
            return dt.astimezone(target_timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            # Return original if timezone unknown
            return dt

    @staticmethod
    def get_all_timezones() -> list:
        """Get list of all available timezones"""
        return sorted(pytz.all_timezones)

    @staticmethod
    def get_common_timezones() -> dict:
        """Get dictionary of common timezones for forensic analysis"""
        return TimezoneConverter.COMMON_TIMEZONES

    @staticmethod
    def format_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
        """
        Format datetime for display

        Args:
            dt: datetime object
            fmt: Format string

        Returns:
            Formatted string
        """
        if dt is None:
            return "N/A"

        try:
            return dt.strftime(fmt)
        except:
            return str(dt)

    @staticmethod
    def get_local_timezone() -> str:
        """Get the local system timezone"""
        try:
            import time
            if time.daylight:
                return time.tzname[1]
            else:
                return time.tzname[0]
        except:
            return "UTC"
