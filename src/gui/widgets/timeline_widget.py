"""
Timeline visualization widget
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QTableWidget,
    QTableWidgetItem, QTabWidget
)
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import pytz

from ...core.models import HistoryEntry
from ...core.analytics import BrowserStatistics
from ...utils.security import escape_html


class TimelineWidget(QWidget):
    """Timeline visualization widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Create tabs
        self.tabs = QTabWidget()

        # Sessions tab
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(5)
        self.sessions_table.setHorizontalHeaderLabels([
            'Session #', 'Start Time', 'End Time', 'Duration (min)', 'Pages Visited'
        ])
        self.sessions_table.setAlternatingRowColors(True)
        self.sessions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.sessions_table, "Browsing Sessions")

        # Timeline view
        self.timeline_text = QTextEdit()
        self.timeline_text.setReadOnly(True)
        self.tabs.addTab(self.timeline_text, "Timeline View")

        layout.addWidget(self.tabs)

    def update_timeline(self, entries: List[HistoryEntry]):
        """
        Update timeline display

        Args:
            entries: List of history entries
        """
        if not entries:
            self.timeline_text.setPlainText("No data available")
            return

        # Calculate sessions
        sessions = BrowserStatistics.calculate_session_duration(entries, session_gap_minutes=30)

        # Update sessions table
        self.update_sessions_table(sessions)

        # Update timeline view
        self.update_timeline_view(entries)

    def update_sessions_table(self, sessions: List[dict]):
        """Update sessions table"""
        self.sessions_table.setRowCount(len(sessions))

        for row, session in enumerate(sessions):
            # Session number
            self.sessions_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))

            # Start time
            start_str = session['start'].strftime("%Y-%m-%d %H:%M:%S")
            self.sessions_table.setItem(row, 1, QTableWidgetItem(start_str))

            # End time
            end_str = session['end'].strftime("%Y-%m-%d %H:%M:%S")
            self.sessions_table.setItem(row, 2, QTableWidgetItem(end_str))

            # Duration
            self.sessions_table.setItem(row, 3, QTableWidgetItem(f"{session['duration_minutes']:.1f}"))

            # Pages visited
            self.sessions_table.setItem(row, 4, QTableWidgetItem(str(session['entry_count'])))

        self.sessions_table.resizeColumnsToContents()

    def update_timeline_view(self, entries: List[HistoryEntry]):
        """Update timeline view"""
        # Group entries by date
        entries_by_date = defaultdict(list)
        for entry in entries:
            date_key = entry.visit_time.date()
            entries_by_date[date_key].append(entry)

        # Sort dates
        sorted_dates = sorted(entries_by_date.keys(), reverse=True)

        # Generate timeline HTML
        html = """
        <html>
        <head>
        <style>
            body { font-family: Arial, sans-serif; }
            .date-header {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                margin-top: 20px;
                border-radius: 5px;
            }
            .entry {
                margin-left: 20px;
                padding: 5px;
                border-left: 3px solid #ddd;
                margin-top: 5px;
            }
            .time { color: #666; font-size: 12px; }
            .url { color: #1a0dab; }
            .browser {
                display: inline-block;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
                margin-left: 5px;
            }
            .chrome { background-color: #ffd966; }
            .firefox { background-color: #ff9966; }
            .edge { background-color: #99ccff; }
        </style>
        </head>
        <body>
        <h2>Browsing Timeline</h2>
        """

        # Limit to last 30 days for performance
        max_dates = 30
        for date in sorted_dates[:max_dates]:
            day_entries = entries_by_date[date]

            # Date header
            html += f"""
            <div class="date-header">
                <h3>{date.strftime('%A, %B %d, %Y')} ({len(day_entries)} visits)</h3>
            </div>
            """

            # Sort entries by time (most recent first)
            day_entries.sort(key=lambda x: x.visit_time, reverse=True)

            # Limit entries per day
            for entry in day_entries[:50]:
                time_str = entry.visit_time.strftime("%H:%M:%S")
                browser_class = entry.browser.lower()

                # Security: Escape all user-controlled data to prevent XSS
                browser_escaped = escape_html(entry.browser)
                url_escaped = escape_html(entry.url)
                title_escaped = escape_html(entry.title or 'No title')

                html += f"""
                <div class="entry">
                    <span class="time">{escape_html(time_str)}</span>
                    <span class="browser {browser_class}">{browser_escaped}</span><br>
                    <span class="url">{url_escaped}</span><br>
                    <span>{title_escaped}</span>
                    <small> (visits: {entry.visit_count})</small>
                </div>
                """

            if len(day_entries) > 50:
                html += f"<div class='entry'><i>... and {len(day_entries) - 50} more entries</i></div>"

        if len(sorted_dates) > max_dates:
            html += f"<p><i>Showing last {max_dates} days. Total: {len(sorted_dates)} days of history.</i></p>"

        html += """
        </body>
        </html>
        """

        self.timeline_text.setHtml(html)

    def update_generic_timeline(self, data: List[Dict[str, Any]], table_name: str = "Table"):
        """
        Update timeline for generic table data

        Args:
            data: List of row dictionaries
            table_name: Name of the table
        """
        if not data:
            self.timeline_text.setPlainText("No data available")
            self.sessions_table.setRowCount(0)
            return

        # Detect timestamp columns
        timestamp_keywords = ['time', 'date', 'timestamp', 'visit', 'created', 'modified', 'updated']
        timestamp_cols = []
        columns = list(data[0].keys()) if data else []

        for col in columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in timestamp_keywords):
                timestamp_cols.append(col)

        if not timestamp_cols:
            self.timeline_text.setPlainText(
                f"No timestamp columns detected in '{table_name}'.\n\n"
                "Timeline requires columns with keywords like:\n"
                "time, date, timestamp, visit, created, modified, updated"
            )
            self.sessions_table.setRowCount(0)
            return

        # Use the first timestamp column
        timestamp_col = timestamp_cols[0]

        # Convert timestamps and group by date
        WEBKIT_EPOCH_OFFSET = 11644473600
        entries_by_date = defaultdict(list)

        for row in data:
            value = row.get(timestamp_col)
            if value is None:
                continue

            try:
                # Convert to datetime
                if isinstance(value, (int, float)):
                    if value > 12000000000000000:  # WebKit microseconds
                        timestamp_seconds = (value / 1000000) - WEBKIT_EPOCH_OFFSET
                    elif value > 10000000000000:  # Microseconds
                        timestamp_seconds = value / 1000000
                    elif value > 10000000000:  # Milliseconds
                        timestamp_seconds = value / 1000
                    else:  # Seconds
                        timestamp_seconds = value

                    dt = datetime.fromtimestamp(timestamp_seconds, tz=pytz.UTC)
                elif isinstance(value, str):
                    # Try parsing string dates
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    continue

                date_key = dt.date()
                entries_by_date[date_key].append({
                    'datetime': dt,
                    'row': row
                })
            except:
                continue

        if not entries_by_date:
            self.timeline_text.setPlainText(
                f"No valid timestamps found in column '{timestamp_col}'"
            )
            self.sessions_table.setRowCount(0)
            return

        # Clear sessions table (not applicable for generic data)
        self.sessions_table.setRowCount(0)

        # Generate timeline HTML
        sorted_dates = sorted(entries_by_date.keys(), reverse=True)

        html = """
        <html>
        <head>
        <style>
            body { font-family: Arial, sans-serif; }
            .date-header {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                margin-top: 20px;
                border-radius: 5px;
            }
            .entry {
                margin-left: 20px;
                padding: 5px;
                border-left: 3px solid #ddd;
                margin-top: 5px;
            }
            .time { color: #666; font-size: 12px; }
            .field { color: #333; margin-left: 10px; }
        </style>
        </head>
        <body>
        """

        html += f"<h2>Timeline: {escape_html(table_name)}</h2>"
        html += f"<p><i>Sorted by: {escape_html(timestamp_col)}</i></p>"

        # Limit to last 30 days for performance
        max_dates = 30
        for date in sorted_dates[:max_dates]:
            day_entries = entries_by_date[date]

            # Date header
            html += f"""
            <div class="date-header">
                <h3>{date.strftime('%A, %B %d, %Y')} ({len(day_entries)} entries)</h3>
            </div>
            """

            # Sort entries by time (most recent first)
            day_entries.sort(key=lambda x: x['datetime'], reverse=True)

            # Limit entries per day
            for entry_data in day_entries[:50]:
                dt = entry_data['datetime']
                row = entry_data['row']

                time_str = dt.strftime("%H:%M:%S %Z")

                html += f"""
                <div class="entry">
                    <span class="time">{escape_html(time_str)}</span><br>
                """

                # Show a few key fields (exclude the timestamp column)
                fields_shown = 0
                for col, val in row.items():
                    if col != timestamp_col and fields_shown < 5 and val is not None:
                        val_str = str(val)[:100]  # Limit length
                        html += f"""<span class="field"><b>{escape_html(col)}:</b> {escape_html(val_str)}</span><br>"""
                        fields_shown += 1

                html += "</div>"

            if len(day_entries) > 50:
                html += f"<div class='entry'><i>... and {len(day_entries) - 50} more entries</i></div>"

        if len(sorted_dates) > max_dates:
            html += f"<p><i>Showing last {max_dates} days. Total: {len(sorted_dates)} days of data.</i></p>"

        html += """
        </body>
        </html>
        """

        self.timeline_text.setHtml(html)
