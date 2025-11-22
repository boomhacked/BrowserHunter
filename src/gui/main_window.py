"""
Main window for Browser Hunter - Refactored Generic Version
Supports browsing any SQLite database with dynamic table/column discovery
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QMenu, QFileDialog,
    QMessageBox, QStatusBar, QToolBar, QPushButton,
    QLabel, QComboBox, QSplitter, QLineEdit, QDateEdit,
    QCheckBox, QGroupBox, QApplication, QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt6.QtGui import QAction, QIcon, QFont
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import io

from ..core.parsers.generic_parser import GenericSQLiteParser
from ..core.models import calculate_file_hash
from ..core.timezone_utils import TimezoneConverter
from ..core.export import DataExporter
from ..utils.annotations import AnnotationManager
from ..utils.saved_queries import SavedQueryManager

from .widgets.dynamic_table import DynamicTableWidget
from .widgets.statistics_panel import StatisticsPanel
from .widgets.virustotal_panel import (
    VirusTotalPanel, VirusTotalSettingsDialog,
    IP2WHOISSettingsDialog, VirusTotalAnalysisThread
)

# Security: Resource limits
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 * 1024  # 10GB
MAX_ROWS_WARNING = 500000
MAX_ROWS_LIMIT = 1000000


class LogCapture:
    """Capture print statements to a log buffer"""
    def __init__(self):
        self.log_buffer = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def start(self):
        """Start capturing output"""
        sys.stdout = self
        sys.stderr = self

    def stop(self):
        """Stop capturing output"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    def write(self, text):
        """Write to both log buffer and original stdout"""
        if self.log_buffer:
            self.log_buffer.write(text)
        if self.original_stdout:
            self.original_stdout.write(text)

    def flush(self):
        """Flush buffers"""
        if self.log_buffer:
            self.log_buffer.flush()
        if self.original_stdout:
            self.original_stdout.flush()

    def get_logs(self):
        """Get all captured logs"""
        return self.log_buffer.getvalue()

    def clear(self):
        """Clear the log buffer"""
        self.log_buffer = io.StringIO()


class LogViewerDialog(QDialog):
    """Dialog for viewing application logs"""
    def __init__(self, log_capture, parent=None):
        super().__init__(parent)
        self.log_capture = log_capture
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Application Logs")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        layout = QVBoxLayout(self)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.log_text)

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_logs)
        button_layout.addWidget(refresh_btn)

        clear_btn = QPushButton("Clear Logs")
        clear_btn.clicked.connect(self.clear_logs)
        button_layout.addWidget(clear_btn)

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_logs)
        button_layout.addWidget(copy_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # Load logs
        self.refresh_logs()

    def refresh_logs(self):
        """Refresh the log display"""
        logs = self.log_capture.get_logs()
        self.log_text.setPlainText(logs)
        # Scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def clear_logs(self):
        """Clear all logs"""
        self.log_capture.clear()
        self.log_text.clear()

    def copy_logs(self):
        """Copy logs to clipboard"""
        logs = self.log_capture.get_logs()
        QApplication.clipboard().setText(logs)


class LoadDatabaseThread(QThread):
    """Background thread for loading SQLite databases"""
    finished = pyqtSignal(object)  # GenericSQLiteParser object
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        """Load database in background"""
        try:
            self.progress.emit("Loading database...")

            # Check file size
            file_path_obj = Path(self.file_path)
            file_size = file_path_obj.stat().st_size

            if file_size > MAX_FILE_SIZE_BYTES:
                size_gb = file_size / (1024**3)
                raise ValueError(
                    f"File too large ({size_gb:.1f} GB). Maximum size is "
                    f"{MAX_FILE_SIZE_BYTES/(1024**3):.0f} GB."
                )

            self.progress.emit(f"File size: {file_size / (1024**2):.1f} MB")

            # Create parser
            parser = GenericSQLiteParser(self.file_path)

            # Get database info
            self.progress.emit("Analyzing database structure...")
            db_info = parser.get_database_info()

            self.progress.emit(
                f"Found {db_info['table_count']} tables "
                f"(Browser type: {db_info['browser_type']})"
            )

            # Close any connections created in this thread
            # The main thread will recreate connections as needed
            parser.close()

            self.finished.emit(parser)

        except Exception as e:
            error_msg = str(e)
            if self.file_path in error_msg:
                error_msg = error_msg.replace(self.file_path, Path(self.file_path).name)
            self.error.emit(error_msg)


class MainWindow(QMainWindow):
    """Main application window - Generic SQLite Browser"""

    def __init__(self):
        super().__init__()

        self.parser: Optional[GenericSQLiteParser] = None
        self.current_table: Optional[str] = None
        self.current_data: List[Dict[str, Any]] = []
        self.filtered_data: List[Dict[str, Any]] = []
        self.current_timezone = "UTC"
        self.current_file_hash = ""

        # Initialize managers
        self.annotation_manager = AnnotationManager()
        self.query_manager = SavedQueryManager()

        # VirusTotal
        self.vt_panel: Optional[VirusTotalPanel] = None
        self.vt_analysis_thread: Optional[VirusTotalAnalysisThread] = None

        # Log capture
        self.log_capture = LogCapture()
        self.log_capture.start()

        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Browser Hunter - SQLite Browser")
        self.setGeometry(100, 100, 1400, 900)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Create menu bar
        self.create_menu_bar()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Create compact toolbar with all controls
        toolbar_widget = self.create_compact_toolbar()
        main_layout.addWidget(toolbar_widget)

        # Create horizontal splitter for main content and VT panel
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create tab widget
        self.tabs = QTabWidget()

        # Data browser tab
        self.table_widget = DynamicTableWidget()
        # Connect table widget to VT query
        self.table_widget.virustotal_query_requested = self.query_virustotal
        self.tabs.addTab(self.table_widget, "Data Browser")

        # Statistics tab
        self.statistics_panel = StatisticsPanel()
        # Connect statistics panel to VT query
        self.statistics_panel.virustotal_query_requested = self.query_virustotal
        self.tabs.addTab(self.statistics_panel, "Statistics")

        self.main_splitter.addWidget(self.tabs)

        # VirusTotal panel (initially hidden)
        self.vt_panel = VirusTotalPanel()
        self.vt_panel.setMinimumWidth(300)
        self.vt_panel.hide()
        self.main_splitter.addWidget(self.vt_panel)

        # Set splitter proportions (90% main, 10% VT when shown)
        self.main_splitter.setStretchFactor(0, 9)
        self.main_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self.main_splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Click 'Load Database' to begin")

    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        load_action = QAction("Load Database...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_database_file)
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        export_menu = file_menu.addMenu("Export")

        export_csv_action = QAction("Export to CSV", self)
        export_csv_action.triggered.connect(lambda: self.export_data('csv'))
        export_menu.addAction(export_csv_action)

        export_json_action = QAction("Export to JSON", self)
        export_json_action.triggered.connect(lambda: self.export_data('json'))
        export_menu.addAction(export_json_action)

        export_excel_action = QAction("Export to Excel", self)
        export_excel_action.triggered.connect(lambda: self.export_data('excel'))
        export_menu.addAction(export_excel_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

        vt_settings_action = QAction("VirusTotal API Settings", self)
        vt_settings_action.triggered.connect(self.show_virustotal_settings)
        settings_menu.addAction(vt_settings_action)

        ip2whois_settings_action = QAction("IP2WHOIS Settings", self)
        ip2whois_settings_action.triggered.connect(self.show_ip2whois_settings)
        settings_menu.addAction(ip2whois_settings_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        view_logs_action = QAction("View Logs", self)
        view_logs_action.triggered.connect(self.show_logs)
        help_menu.addAction(view_logs_action)

        help_menu.addSeparator()

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_compact_toolbar(self) -> QWidget:
        """Create compact toolbar with all controls in one row"""
        toolbar_widget = QWidget()
        toolbar_widget.setMaximumHeight(35)  # Limit height
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(2, 2, 2, 2)
        toolbar_layout.setSpacing(5)

        # Refresh button
        refresh_btn = QPushButton("⟳")
        refresh_btn.setToolTip("Refresh current table")
        refresh_btn.clicked.connect(self.refresh_current_table)
        refresh_btn.setMaximumWidth(30)
        refresh_btn.setMaximumHeight(25)
        toolbar_layout.addWidget(refresh_btn)

        # Table selector
        self.table_combo = QComboBox()
        self.table_combo.setMinimumWidth(150)
        self.table_combo.setMaximumWidth(200)
        self.table_combo.setMaximumHeight(25)
        self.table_combo.currentTextChanged.connect(self.on_table_changed)
        toolbar_layout.addWidget(self.table_combo)

        # Timezone selector
        self.timezone_combo = QComboBox()
        self.timezone_combo.addItems(list(TimezoneConverter.get_common_timezones().keys()))
        self.timezone_combo.setCurrentText("UTC")
        self.timezone_combo.setMaximumWidth(120)
        self.timezone_combo.setMaximumHeight(25)
        self.timezone_combo.currentTextChanged.connect(self.on_timezone_changed)
        toolbar_layout.addWidget(self.timezone_combo)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setMaximumWidth(150)
        self.search_input.setMaximumHeight(25)
        self.search_input.returnPressed.connect(self.apply_filters)
        toolbar_layout.addWidget(self.search_input)

        # Date range
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setMinimumWidth(110)
        self.start_date.setMaximumWidth(110)
        self.start_date.setMaximumHeight(25)
        toolbar_layout.addWidget(self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setMinimumWidth(110)
        self.end_date.setMaximumWidth(110)
        self.end_date.setMaximumHeight(25)
        toolbar_layout.addWidget(self.end_date)

        # Search button
        self.search_btn = QPushButton("Go")
        self.search_btn.clicked.connect(self.apply_filters)
        self.search_btn.setMaximumWidth(40)
        self.search_btn.setMaximumHeight(25)
        toolbar_layout.addWidget(self.search_btn)

        # Clear button
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setToolTip("Clear filters")
        self.clear_btn.clicked.connect(self.clear_filters)
        self.clear_btn.setMaximumWidth(30)
        self.clear_btn.setMaximumHeight(25)
        toolbar_layout.addWidget(self.clear_btn)

        # Database info label (compact)
        self.db_info_label = QLabel("No DB loaded")
        self.db_info_label.setStyleSheet("color: gray; font-size: 9px;")
        toolbar_layout.addWidget(self.db_info_label)

        toolbar_layout.addStretch()

        return toolbar_widget


    def load_database_file(self):
        """Load SQLite database file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SQLite Database",
            "",
            "All Files (*);;SQLite DB (*.db *.sqlite *.sqlite3)"
        )

        if file_path:
            self.load_database(file_path)

    def load_database(self, file_path: str):
        """Load database file in background thread"""
        self.status_bar.showMessage("Loading database...")

        self.load_thread = LoadDatabaseThread(file_path)
        self.load_thread.finished.connect(self.on_database_loaded)
        self.load_thread.error.connect(self.on_load_error)
        self.load_thread.progress.connect(self.status_bar.showMessage)
        self.load_thread.start()

    def on_database_loaded(self, parser: GenericSQLiteParser):
        """Handle successful database load"""
        self.parser = parser

        # Get database info
        db_info = parser.get_database_info()
        self.current_file_hash = db_info['file_hash']

        # Update database info label (compact)
        file_size_mb = db_info['file_size'] / (1024 * 1024)
        self.db_info_label.setText(
            f"{db_info['file_name']} ({file_size_mb:.0f}MB, {db_info['table_count']} tables)"
        )
        self.db_info_label.setToolTip(
            f"File: {db_info['file_name']}\n"
            f"Type: {db_info['browser_type']}\n"
            f"Size: {file_size_mb:.1f} MB\n"
            f"Tables: {db_info['table_count']}"
        )

        # Populate table selector
        tables = parser.get_tables()
        self.table_combo.clear()
        self.table_combo.addItems(tables)

        # Auto-select first table
        if tables:
            self.table_combo.setCurrentIndex(0)

        self.status_bar.showMessage(
            f"Loaded {db_info['file_name']} - {db_info['table_count']} tables found",
            5000
        )

        QMessageBox.information(
            self,
            "Database Loaded",
            f"Successfully loaded database:\n\n"
            f"File: {db_info['file_name']}\n"
            f"Type: {db_info['browser_type']}\n"
            f"Tables: {db_info['table_count']}\n"
            f"Size: {file_size_mb:.1f} MB"
        )

    def on_load_error(self, error_msg: str):
        """Handle database load error"""
        self.status_bar.showMessage("Error loading database")
        QMessageBox.critical(
            self,
            "Error Loading Database",
            f"Failed to load database:\n\n{error_msg}"
        )

    def on_table_changed(self, table_name: str):
        """Handle table selection change"""
        if not table_name or not self.parser:
            return

        self.current_table = table_name
        self.load_table_data()

    def load_table_data(self):
        """Load data from currently selected table"""
        if not self.parser or not self.current_table:
            return

        try:
            self.status_bar.showMessage(f"Loading table '{self.current_table}'...")

            # Get row count
            row_count = self.parser.get_row_count(self.current_table)

            # Check limits
            if row_count > MAX_ROWS_LIMIT:
                QMessageBox.warning(
                    self,
                    "Too Many Rows",
                    f"Table has {row_count:,} rows. Maximum is {MAX_ROWS_LIMIT:,}.\n\n"
                    f"Please use filters or SQL query to reduce the dataset."
                )
                return

            if row_count > MAX_ROWS_WARNING:
                reply = QMessageBox.question(
                    self,
                    "Large Dataset",
                    f"Table has {row_count:,} rows. This may be slow.\n\n"
                    f"Do you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            # Load data (use batching for large datasets)
            if row_count > 50000:
                # For large datasets, load in batches
                self.status_bar.showMessage(f"Loading {row_count:,} rows in batches...")
                columns, rows = self.parser.get_table_data(self.current_table, limit=50000)
                QMessageBox.information(
                    self,
                    "Large Dataset",
                    f"Loaded first 50,000 rows of {row_count:,} total rows.\n\n"
                    f"Use filters to narrow down the dataset for better performance."
                )
            else:
                columns, rows = self.parser.get_table_data(self.current_table)

            self.current_data = rows
            self.filtered_data = rows.copy()

            # Update table widget
            self.table_widget.set_data(self.filtered_data, columns)

            self.status_bar.showMessage(
                f"Loaded {len(rows):,} rows from table '{self.current_table}'",
                3000
            )

            # Update statistics if this looks like history data
            self.update_statistics_if_applicable()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Table",
                f"Failed to load table data:\n\n{str(e)}"
            )
            self.status_bar.showMessage("Error loading table data")

    def apply_filters(self):
        """Apply search and date filters"""
        if not self.current_data:
            return

        try:
            filtered = self.current_data.copy()

            # Apply date filter first
            filtered = self.filter_by_date(filtered)

            # Apply keyword search on the date-filtered results
            keyword = self.search_input.text().strip()
            if keyword:
                filtered = self.filter_by_keyword(filtered, keyword)

            self.filtered_data = filtered
            self.table_widget.set_data(self.filtered_data)

            # Update statistics with filtered data
            self.update_statistics_if_applicable()

            self.status_bar.showMessage(
                f"Filter applied: {len(filtered):,} of {len(self.current_data):,} rows",
                3000
            )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Filter Error",
                f"Error applying filters:\n\n{str(e)}"
            )

    def filter_by_keyword(self, data: List[Dict[str, Any]], keyword: str) -> List[Dict[str, Any]]:
        """Filter data by keyword search"""
        keyword_lower = keyword.lower()
        filtered = []

        for row in data:
            # Search across all columns
            for value in row.values():
                if value is not None and keyword_lower in str(value).lower():
                    filtered.append(row)
                    break

        return filtered

    def filter_by_date(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter data by date range"""
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()

        # Try to find date/time columns
        if not data:
            return data

        first_row = data[0]
        date_columns = []

        # Look for common date column names
        for col_name in first_row.keys():
            col_lower = col_name.lower()
            if any(keyword in col_lower for keyword in ['time', 'date', 'created', 'modified', 'visit', 'expire', 'last', 'first']):
                date_columns.append(col_name)

        # If no date columns found, return data as-is (no filtering)
        if not date_columns:
            return data

        # WebKit epoch offset
        WEBKIT_EPOCH_OFFSET = 11644473600

        # Filter by date
        filtered = []
        for row in data:
            match_found = False
            for col_name in date_columns:
                value = row.get(col_name)
                if value is not None and isinstance(value, (int, float)) and value > 0:
                    try:
                        # Convert timestamp to datetime
                        if value > 12000000000000000:  # WebKit microseconds (Chrome/Edge)
                            timestamp_seconds = (value / 1000000) - WEBKIT_EPOCH_OFFSET
                        elif value > 10000000000000:  # UNIX microseconds
                            timestamp_seconds = value / 1000000
                        elif value > 10000000000:  # Milliseconds
                            timestamp_seconds = value / 1000
                        else:  # Seconds
                            timestamp_seconds = value

                        dt = datetime.fromtimestamp(timestamp_seconds)

                        if start_date <= dt.date() <= end_date:
                            match_found = True
                            break
                    except:
                        pass

            # If any date column matches, include the row
            if match_found:
                filtered.append(row)

        # If no rows matched but we had date columns, return filtered result
        # If no date columns were found, we already returned data as-is above
        return filtered

    def clear_filters(self):
        """Clear all filters"""
        self.search_input.clear()
        self.filtered_data = self.current_data.copy()
        self.table_widget.set_data(self.filtered_data)

        # Update statistics with unfiltered data
        self.update_statistics_if_applicable()

        self.status_bar.showMessage("Filters cleared", 2000)

    def refresh_current_table(self):
        """Refresh the current table"""
        if self.current_table:
            self.load_table_data()

    def on_timezone_changed(self, timezone: str):
        """Handle timezone change"""
        self.current_timezone = timezone
        # Update table widget to use new timezone
        self.table_widget.set_timezone(timezone)
        self.status_bar.showMessage(f"Timezone changed to {timezone}", 2000)

    def update_statistics_if_applicable(self):
        """Update statistics panel with current table data"""
        if not self.filtered_data or not self.current_table:
            return

        # Update statistics with generic table data
        self.statistics_panel.update_generic_statistics(
            self.filtered_data,
            self.current_table
        )

    def export_data(self, format_type: str):
        """Export current filtered data"""
        if not self.filtered_data:
            QMessageBox.warning(
                self,
                "No Data",
                "No data to export. Please load a table first."
            )
            return

        # Get save file path
        filters = {
            'csv': "CSV Files (*.csv)",
            'json': "JSON Files (*.json)",
            'excel': "Excel Files (*.xlsx)"
        }

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            filters.get(format_type, "All Files (*.*)")
        )

        if not file_path:
            return

        try:
            exporter = DataExporter()

            if format_type == 'csv':
                exporter.export_generic_to_csv(self.filtered_data, file_path)
            elif format_type == 'json':
                exporter.export_generic_to_json(self.filtered_data, file_path)
            elif format_type == 'excel':
                exporter.export_generic_to_excel(self.filtered_data, file_path)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Data exported successfully to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export data:\n\n{str(e)}"
            )

    def show_logs(self):
        """Show log viewer dialog"""
        dialog = LogViewerDialog(self.log_capture, self)
        dialog.exec()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Browser Hunter",
            "Browser Hunter v1.0\n\n"
            "Generic SQLite Database Browser\n"
            "Designed for forensic analysis of browser history files\n\n"
            "Supports Chrome, Firefox, Edge, and any SQLite database\n\n"
            "© 2024 Forensic Tools"
        )

    def show_virustotal_settings(self):
        """Show VirusTotal settings dialog"""
        dialog = VirusTotalSettingsDialog(self)
        dialog.exec()

    def show_ip2whois_settings(self):
        """Show IP2WHOIS settings dialog"""
        dialog = IP2WHOISSettingsDialog(self)
        dialog.exec()

    def query_virustotal(self, url: str):
        """Query VirusTotal for URL analysis"""
        # Load VirusTotal API key
        vt_api_key = VirusTotalSettingsDialog.load_api_key()

        if not vt_api_key:
            reply = QMessageBox.question(
                self,
                "API Key Required",
                "VirusTotal API key is not configured.\n\n"
                "Would you like to configure it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.show_virustotal_settings()
                # Try loading again
                vt_api_key = VirusTotalSettingsDialog.load_api_key()
                if not vt_api_key:
                    return
            else:
                return

        # Load IP2WHOIS API key (optional)
        ip2whois_api_key = IP2WHOISSettingsDialog.load_api_key()

        # Show VT panel
        self.vt_panel.show()
        self.vt_panel.show_loading(url)

        # Start analysis in background thread (with both API keys)
        self.vt_analysis_thread = VirusTotalAnalysisThread(vt_api_key, url, ip2whois_api_key)
        self.vt_analysis_thread.finished.connect(self.on_vt_analysis_complete)
        self.vt_analysis_thread.error.connect(self.on_vt_analysis_error)
        self.vt_analysis_thread.start()

    def on_vt_analysis_complete(self, results: Dict[str, Any]):
        """Handle VirusTotal analysis completion"""
        self.vt_panel.show_results(results)

    def on_vt_analysis_error(self, error: str):
        """Handle VirusTotal analysis error"""
        self.vt_panel.show_error(error)

    def dragEnterEvent(self, event):
        """Handle drag enter event for drag & drop"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle drop event for drag & drop"""
        urls = event.mimeData().urls()
        if urls:
            # Get first file path
            file_path = urls[0].toLocalFile()

            # Check if file exists
            if file_path and Path(file_path).exists():
                self.load_database(file_path)
                event.acceptProposedAction()
            else:
                QMessageBox.warning(
                    self,
                    "Invalid File",
                    "The dropped file does not exist or is not accessible."
                )
                event.ignore()

    def closeEvent(self, event):
        """Handle window close event"""
        # Stop log capture
        self.log_capture.stop()

        if self.parser:
            self.parser.close()
        event.accept()
