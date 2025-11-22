"""
Statistics panel widget
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QTableWidget, QTableWidgetItem, QTabWidget,
    QGroupBox, QScrollArea, QMenu, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QAction
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime
from collections import Counter

from ...core.models import HistoryEntry
from ...core.analytics import BrowserStatistics, URLAnalyzer
from ...utils.security import escape_html


class StatisticsPanel(QWidget):
    """Statistics and analytics panel"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.virustotal_query_requested = None  # Callback for VirusTotal queries
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Create tabs for different statistics
        self.tabs = QTabWidget()

        # Overview tab
        self.overview_text = QTextEdit()
        self.overview_text.setReadOnly(True)
        self.tabs.addTab(self.overview_text, "Overview")

        # Top domains tab
        self.domains_table = self.create_top_table(["Domain", "Visits"])
        self.tabs.addTab(self.domains_table, "Top Domains")

        # Top URLs tab
        self.urls_table = self.create_top_table(["URL", "Title", "Visits"])
        self.tabs.addTab(self.urls_table, "Top URLs")

        layout.addWidget(self.tabs)

    def create_top_table(self, headers: List[str]) -> QTableWidget:
        """Create table for top items"""
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Enable context menu for right-click
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(
            lambda pos, t=table: self.show_table_context_menu(pos, t)
        )

        # Enable Ctrl+C copying
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, table)
        copy_shortcut.activated.connect(lambda t=table: self.copy_table_selection(t))

        return table

    def update_statistics(self, entries: List[HistoryEntry]):
        """
        Update statistics display

        Args:
            entries: List of history entries
        """
        if not entries:
            self.overview_text.setPlainText("No data available")
            return

        # Generate summary report
        report = BrowserStatistics.generate_summary_report(entries)

        # Update overview
        overview = self.format_overview(report)
        self.overview_text.setHtml(overview)

        # Update top domains
        self.update_top_domains(report['top_domains'])

        # Update top URLs
        self.update_top_urls(report['most_visited'])

        # Update activity patterns
        activity = self.format_activity_patterns(report)
        self.activity_text.setHtml(activity)

    def format_overview(self, report: dict) -> str:
        """Format overview HTML"""
        date_range = report['date_range']
        start_date = date_range[0].strftime("%Y-%m-%d %H:%M:%S") if date_range[0] else "N/A"
        end_date = date_range[1].strftime("%Y-%m-%d %H:%M:%S") if date_range[1] else "N/A"

        # Security: Escape dates
        start_date_escaped = escape_html(start_date)
        end_date_escaped = escape_html(end_date)

        html = f"""
        <html>
        <body>
        <h2>Browser History Statistics</h2>

        <h3>Overview</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
            <tr><td><b>Total Entries:</b></td><td>{report['total_entries']:,}</td></tr>
            <tr><td><b>Total Visits:</b></td><td>{report['total_visits']:,}</td></tr>
            <tr><td><b>Unique URLs:</b></td><td>{report['unique_urls']:,}</td></tr>
            <tr><td><b>Unique Domains:</b></td><td>{report['unique_domains']:,}</td></tr>
            <tr><td><b>Search Queries:</b></td><td>{report['search_queries_count']:,}</td></tr>
            <tr><td><b>Duplicate Groups:</b></td><td>{report['duplicate_groups']:,}</td></tr>
        </table>

        <h3>Date Range</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
            <tr><td><b>First Visit:</b></td><td>{start_date_escaped}</td></tr>
            <tr><td><b>Last Visit:</b></td><td>{end_date_escaped}</td></tr>
        </table>

        <h3>Browser Distribution</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
        """

        for browser, count in report['browser_distribution'].items():
            percentage = (count / report['total_entries'] * 100) if report['total_entries'] > 0 else 0
            # Security: Escape browser name to prevent XSS
            browser_escaped = escape_html(str(browser))
            html += f"<tr><td><b>{browser_escaped}:</b></td><td>{count:,} ({percentage:.1f}%)</td></tr>"

        html += """
        </table>
        </body>
        </html>
        """

        return html

    def update_top_domains(self, top_domains: List[tuple]):
        """Update top domains table"""
        self.domains_table.setRowCount(len(top_domains))

        for row, (domain, visits) in enumerate(top_domains):
            self.domains_table.setItem(row, 0, QTableWidgetItem(domain))
            self.domains_table.setItem(row, 1, QTableWidgetItem(str(visits)))

        self.domains_table.resizeColumnsToContents()

    def update_top_urls(self, top_urls: List[tuple]):
        """Update top URLs table"""
        self.urls_table.setRowCount(len(top_urls))

        for row, (url, title, visits) in enumerate(top_urls):
            self.urls_table.setItem(row, 0, QTableWidgetItem(url))
            self.urls_table.setItem(row, 1, QTableWidgetItem(title or "N/A"))
            self.urls_table.setItem(row, 2, QTableWidgetItem(str(visits)))

        self.urls_table.resizeColumnsToContents()

    def update_generic_statistics(self, data: List[dict], table_name: str = "Table"):
        """
        Update statistics for generic table data

        Args:
            data: List of row dictionaries
            table_name: Name of the table
        """
        if not data:
            self.overview_text.setPlainText("No data available")
            return

        # Generate generic statistics
        total_rows = len(data)

        # Get column names
        columns = list(data[0].keys()) if data else []

        # Find URL columns (for Top Domains and Top URLs)
        url_columns = [col for col in columns if 'url' in col.lower()]

        # Find title columns
        title_columns = [col for col in columns if 'title' in col.lower() or 'name' in col.lower()]

        # Find visit count columns
        visit_columns = [col for col in columns if 'visit' in col.lower() and 'count' in col.lower()]

        # Find time/date columns for activity patterns
        time_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['time', 'date', 'created', 'modified', 'visit'])]

        # Count non-null values per column
        column_stats = {}
        for col in columns:
            non_null = sum(1 for row in data if row.get(col) is not None and row.get(col) != '')
            column_stats[col] = {
                'non_null': non_null,
                'null': total_rows - non_null,
                'percentage': (non_null / total_rows * 100) if total_rows > 0 else 0
            }

        # Format overview HTML
        html = f"""
        <html>
        <body>
        <h2>Table Statistics: {escape_html(table_name)}</h2>

        <h3>Overview</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
            <tr><td><b>Total Rows:</b></td><td>{total_rows:,}</td></tr>
            <tr><td><b>Total Columns:</b></td><td>{len(columns)}</td></tr>
        </table>

        <h3>Column Statistics</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
            <tr><th>Column Name</th><th>Non-Null Values</th><th>Null Values</th><th>Fill Rate</th></tr>
        """

        for col, stats in column_stats.items():
            col_escaped = escape_html(str(col))
            html += f"""
            <tr>
                <td><b>{col_escaped}</b></td>
                <td>{stats['non_null']:,}</td>
                <td>{stats['null']:,}</td>
                <td>{stats['percentage']:.1f}%</td>
            </tr>
            """

        html += """
        </table>
        </body>
        </html>
        """

        self.overview_text.setHtml(html)

        # Generate Top Domains if URL columns exist
        if url_columns:
            self._generate_top_domains(data, url_columns[0])
        else:
            self.domains_table.setRowCount(0)

        # Generate Top URLs if URL columns exist
        if url_columns:
            self._generate_top_urls(data, url_columns[0], title_columns[0] if title_columns else None, visit_columns[0] if visit_columns else None)
        else:
            self.urls_table.setRowCount(0)

    def _generate_top_domains(self, data: List[Dict[str, Any]], url_column: str):
        """Generate top domains statistics from URL column"""
        domain_counts = Counter()

        for row in data:
            url = row.get(url_column)
            if url and isinstance(url, str):
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc or parsed.path.split('/')[0]
                    if domain:
                        domain_counts[domain] += 1
                except:
                    pass

        # Get top 20 domains
        top_domains = domain_counts.most_common(20)

        # Update table
        self.domains_table.setRowCount(len(top_domains))
        for row, (domain, count) in enumerate(top_domains):
            self.domains_table.setItem(row, 0, QTableWidgetItem(domain))
            self.domains_table.setItem(row, 1, QTableWidgetItem(str(count)))

        self.domains_table.resizeColumnsToContents()

    def _generate_top_urls(self, data: List[Dict[str, Any]], url_column: str, title_column: str = None, visit_column: str = None):
        """Generate top URLs statistics"""
        url_data = {}

        for row in data:
            url = row.get(url_column)
            if url and isinstance(url, str):
                if url not in url_data:
                    title = row.get(title_column, "") if title_column else ""
                    visit_count = row.get(visit_column, 1) if visit_column else 1
                    url_data[url] = {
                        'title': title,
                        'count': visit_count if isinstance(visit_count, int) else 1
                    }
                else:
                    # Aggregate visit counts
                    visit_count = row.get(visit_column, 1) if visit_column else 1
                    url_data[url]['count'] += visit_count if isinstance(visit_count, int) else 1

        # Sort by count
        sorted_urls = sorted(url_data.items(), key=lambda x: x[1]['count'], reverse=True)[:20]

        # Update table
        self.urls_table.setRowCount(len(sorted_urls))
        for row, (url, info) in enumerate(sorted_urls):
            self.urls_table.setItem(row, 0, QTableWidgetItem(url))
            self.urls_table.setItem(row, 1, QTableWidgetItem(str(info['title']) if info['title'] else "N/A"))
            self.urls_table.setItem(row, 2, QTableWidgetItem(str(info['count'])))

        self.urls_table.resizeColumnsToContents()

    def copy_table_selection(self, table: QTableWidget):
        """Copy selected rows from table to clipboard"""
        selection = table.selectedItems()
        if not selection:
            return

        # Get selected rows
        rows = set()
        for item in selection:
            rows.add(item.row())

        # Sort rows
        sorted_rows = sorted(rows)

        # Build clipboard text
        clipboard_text = []
        for row in sorted_rows:
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            clipboard_text.append("\t".join(row_data))

        # Copy to clipboard
        final_text = "\n".join(clipboard_text)
        QApplication.clipboard().setText(final_text)

    def show_table_context_menu(self, position, table: QTableWidget):
        """Show context menu for statistics table"""
        item = table.itemAt(position)
        if not item:
            return

        menu = QMenu(table)

        # Copy action
        copy_action = QAction("Copy", table)
        copy_action.triggered.connect(lambda: self.copy_table_selection(table))
        menu.addAction(copy_action)

        # VirusTotal action for domain/URL columns
        # Check if this is domains table (column 0 = domain) or URLs table (column 0 = URL)
        if item.column() == 0:  # Domain or URL column
            text = item.text()
            if text:
                menu.addSeparator()

                # For domains table, construct a URL
                if table == self.domains_table:
                    url = f"https://{text}"
                else:
                    url = text

                if self.virustotal_query_requested and 'http' in url.lower():
                    vt_action = QAction("Query with VirusTotal", table)
                    vt_action.triggered.connect(lambda: self.virustotal_query_requested(url))
                    menu.addAction(vt_action)

        menu.exec(table.viewport().mapToGlobal(position))

    def format_activity_patterns(self, report: dict) -> str:
        """Format activity patterns HTML"""
        html = """
        <html>
        <body>
        <h2>Activity Patterns</h2>

        <h3>Activity by Hour</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
        <tr><th>Hour</th><th>Visits</th><th>Bar</th></tr>
        """

        activity_by_hour = report['activity_by_hour']
        max_hour_visits = max(activity_by_hour.values()) if activity_by_hour else 1

        for hour in range(24):
            visits = activity_by_hour.get(hour, 0)
            bar_width = int((visits / max_hour_visits) * 100) if max_hour_visits > 0 else 0
            bar = "█" * (bar_width // 5)
            html += f"""
            <tr>
                <td>{hour:02d}:00</td>
                <td>{visits:,}</td>
                <td>{bar}</td>
            </tr>
            """

        html += """
        </table>

        <h3>Activity by Day of Week</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
        <tr><th>Day</th><th>Visits</th><th>Bar</th></tr>
        """

        activity_by_day = report['activity_by_day']
        max_day_visits = max(activity_by_day.values()) if activity_by_day else 1

        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in days_order:
            visits = activity_by_day.get(day, 0)
            bar_width = int((visits / max_day_visits) * 100) if max_day_visits > 0 else 0
            bar = "█" * (bar_width // 5)
            html += f"""
            <tr>
                <td>{day}</td>
                <td>{visits:,}</td>
                <td>{bar}</td>
            </tr>
            """

        html += """
        </table>
        </body>
        </html>
        """

        return html
