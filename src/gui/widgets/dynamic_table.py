"""
Dynamic table widget with column management
Supports showing/hiding columns, reordering, resizing, and timestamp conversion
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QComboBox,
    QCheckBox, QDialog, QDialogButtonBox, QListWidget,
    QListWidgetItem, QHeaderView, QAbstractItemView, QApplication,
    QMenu, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QAction
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import unquote
import pytz


class ColumnManagerDialog(QDialog):
    """Dialog for managing column visibility and order"""

    def __init__(self, columns: List[str], visible_columns: List[str], parent=None):
        super().__init__(parent)
        self.columns = columns
        self.visible_columns = visible_columns.copy()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Manage Columns")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)

        # Instructions
        label = QLabel("Check columns to show/hide. Drag to reorder.")
        layout.addWidget(label)

        # List widget for columns
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        # Add all columns with checkboxes
        for col in self.columns:
            item = QListWidgetItem(col)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if col in self.visible_columns:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        # Buttons
        button_layout = QHBoxLayout()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(deselect_all_btn)

        layout.addLayout(button_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def select_all(self):
        """Select all columns"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.CheckState.Checked)

    def deselect_all(self):
        """Deselect all columns"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)

    def get_visible_columns(self) -> List[str]:
        """Get list of visible columns in current order"""
        visible = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                visible.append(item.text())
        return visible

    def get_column_order(self) -> List[str]:
        """Get all columns in current order"""
        columns = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            columns.append(item.text())
        return columns


class DynamicTableWidget(QWidget):
    """
    Dynamic table widget that can display any data with configurable columns
    """
    rows_per_page_changed = pyqtSignal(int)
    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.all_data: List[Dict[str, Any]] = []
        self.all_columns: List[str] = []
        self.visible_columns: List[str] = []
        self.current_page = 0
        self.rows_per_page = 100
        self.current_timezone = "UTC"  # Default timezone
        self.timestamp_columns: List[str] = []  # Columns that contain timestamps

        # VirusTotal callback (set by parent)
        self.virustotal_query_requested = None

        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Top toolbar
        toolbar = QHBoxLayout()

        # Column manager button
        self.manage_columns_btn = QPushButton("Manage Columns")
        self.manage_columns_btn.clicked.connect(self.open_column_manager)
        toolbar.addWidget(self.manage_columns_btn)

        toolbar.addStretch()

        # Rows per page selector
        toolbar.addWidget(QLabel("Rows per page:"))
        self.rows_combo = QComboBox()
        self.rows_combo.addItems(["50", "100", "500", "1000", "5000", "All"])
        self.rows_combo.setCurrentText("100")
        self.rows_combo.currentTextChanged.connect(self.on_rows_per_page_changed)
        toolbar.addWidget(self.rows_combo)

        # Entry count label
        self.entry_count_label = QLabel("0 entries")
        toolbar.addWidget(self.entry_count_label)

        layout.addLayout(toolbar)

        # Table widget
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)

        # Enable cell selection and copying (instead of row selection)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Enable context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Enable sorting by clicking column headers
        self.table.setSortingEnabled(False)  # Will enable after data is loaded

        # Enable horizontal scrolling
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        # Make columns resizable
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setSortIndicatorShown(True)  # Show sort arrows

        # Add copy shortcut
        self.copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self.table)
        self.copy_shortcut.activated.connect(self.copy_selection_to_clipboard)

        layout.addWidget(self.table)

        # Pagination controls
        pagination = QHBoxLayout()

        self.prev_btn = QPushButton("< Previous")
        self.prev_btn.clicked.connect(self.previous_page)
        pagination.addWidget(self.prev_btn)

        self.page_label = QLabel("Page 1 of 1")
        pagination.addWidget(self.page_label)

        self.next_btn = QPushButton("Next >")
        self.next_btn.clicked.connect(self.next_page)
        pagination.addWidget(self.next_btn)

        pagination.addStretch()

        layout.addLayout(pagination)

    def set_timezone(self, timezone: str):
        """
        Set timezone for timestamp conversion

        Args:
            timezone: Timezone name (e.g., 'UTC', 'US/Eastern')
        """
        self.current_timezone = timezone
        # Refresh display if data is loaded
        if self.all_data:
            self.update_table()

    def _detect_timestamp_columns(self, columns: List[str]) -> List[str]:
        """
        Detect which columns likely contain timestamps

        Args:
            columns: List of column names

        Returns:
            List of column names that likely contain timestamps
        """
        timestamp_keywords = [
            'time', 'date', 'timestamp', 'visit', 'created', 'modified',
            'updated', 'last', 'first', 'start', 'end', 'expire'
        ]

        timestamp_cols = []
        for col in columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in timestamp_keywords):
                timestamp_cols.append(col)

        return timestamp_cols

    def _is_unix_timestamp(self, value: Any) -> bool:
        """
        Check if a value looks like a UNIX or WebKit timestamp

        Args:
            value: Value to check

        Returns:
            True if value appears to be a timestamp
        """
        if not isinstance(value, (int, float)):
            return False

        if value < 0:
            return False

        # WebKit timestamps (Chrome/Edge): microseconds since 1601-01-01
        # Typical range: 13000000000000000 to 13900000000000000 (for 2012-2040)
        if value > 12000000000000000:  # WebKit microseconds
            return True

        # UNIX timestamps:
        # - Microseconds: 16 digits (e.g., 1642521600000000)
        # - Milliseconds: 13 digits (e.g., 1642521600000)
        # - Seconds: 10 digits (e.g., 1642521600)

        # Check for microseconds (UNIX)
        if value > 10000000000000:  # Microseconds
            timestamp_seconds = value / 1000000
            return 946684800 <= timestamp_seconds <= 4102444800

        # Check for milliseconds
        elif value > 10000000000:  # Milliseconds
            timestamp_seconds = value / 1000
            return 946684800 <= timestamp_seconds <= 4102444800

        # Check for seconds
        elif value > 100000000:  # Seconds
            # Range: 2000-01-01 to 2100-01-01
            return 946684800 <= value <= 4102444800

        return False

    def _convert_timestamp(self, value: Any, timezone: str = "UTC") -> str:
        """
        Convert UNIX or WebKit timestamp to human-readable format

        Args:
            value: Timestamp value (seconds, milliseconds, microseconds, or WebKit)
            timezone: Target timezone

        Returns:
            Formatted datetime string or original value if not a timestamp
        """
        if not self._is_unix_timestamp(value):
            return str(value) if value is not None else ""

        try:
            # WebKit epoch: January 1, 1601
            # UNIX epoch: January 1, 1970
            # Difference: 11644473600 seconds
            WEBKIT_EPOCH_OFFSET = 11644473600

            # Convert to seconds
            if value > 12000000000000000:  # WebKit microseconds (Chrome/Edge)
                timestamp_seconds = (value / 1000000) - WEBKIT_EPOCH_OFFSET
            elif value > 10000000000000:  # UNIX Microseconds
                timestamp_seconds = value / 1000000
            elif value > 10000000000:  # Milliseconds
                timestamp_seconds = value / 1000
            else:  # Seconds
                timestamp_seconds = value

            # Create datetime in UTC
            dt_utc = datetime.fromtimestamp(timestamp_seconds, tz=pytz.UTC)

            # Convert to target timezone
            if timezone != "UTC":
                try:
                    target_tz = pytz.timezone(timezone)
                    dt_converted = dt_utc.astimezone(target_tz)
                except:
                    dt_converted = dt_utc
            else:
                dt_converted = dt_utc

            # Format as readable string
            formatted = dt_converted.strftime("%Y-%m-%d %H:%M:%S %Z")
            return formatted

        except Exception as e:
            # If conversion fails, return original value
            return str(value)

    def set_data(self, data: List[Dict[str, Any]], columns: Optional[List[str]] = None):
        """
        Set table data

        Args:
            data: List of row dicts
            columns: Column names (if None, extracted from first row)
        """
        try:
            self.all_data = data

            # Extract columns
            if columns:
                self.all_columns = columns
            elif data:
                self.all_columns = list(data[0].keys())
            else:
                self.all_columns = []

            # Detect timestamp columns
            self.timestamp_columns = self._detect_timestamp_columns(self.all_columns)

            # Default visible columns to all columns
            if not self.visible_columns:
                self.visible_columns = self.all_columns.copy()

            self.current_page = 0
            self.update_table()
            self.update_pagination_controls()

        except Exception as e:
            print(f"ERROR in set_data(): {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def update_table(self):
        """Update table display with current page data"""
        try:
            # Calculate pagination
            total_rows = len(self.all_data)

            if self.rows_per_page == -1:  # "All"
                start_idx = 0
                end_idx = total_rows
            else:
                start_idx = self.current_page * self.rows_per_page
                end_idx = min(start_idx + self.rows_per_page, total_rows)

            page_data = self.all_data[start_idx:end_idx]

            # Update entry count label
            if total_rows == 0:
                self.entry_count_label.setText("0 entries")
            else:
                self.entry_count_label.setText(
                    f"Showing {start_idx + 1}-{end_idx} of {total_rows:,} entries"
                )

            # Set table dimensions
            self.table.setRowCount(len(page_data))
            self.table.setColumnCount(len(self.visible_columns))
            self.table.setHorizontalHeaderLabels(self.visible_columns)

            # Populate table
            for row_idx, row_data in enumerate(page_data):
                for col_idx, col_name in enumerate(self.visible_columns):
                    try:
                        value = row_data.get(col_name, "")

                        # Convert to string
                        if value is None:
                            display_value = ""
                        # Check if this is a timestamp column and convert if needed
                        elif col_name in self.timestamp_columns:
                            display_value = self._convert_timestamp(value, self.current_timezone)
                        else:
                            display_value = str(value)

                        item = QTableWidgetItem(display_value)
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                        self.table.setItem(row_idx, col_idx, item)
                    except Exception as e:
                        # If a single cell fails, show error but continue
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(f"[ERROR: {str(e)}]"))

            # Enable sorting now that data is loaded
            self.table.setSortingEnabled(True)

            # Set compact default column widths (user can expand as needed)
            for col_idx in range(self.table.columnCount()):
                # Start with compact 150px width for all columns
                self.table.setColumnWidth(col_idx, 150)

        except Exception as e:
            print(f"ERROR in update_table(): {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def update_pagination_controls(self):
        """Update pagination button states and labels"""
        total_rows = len(self.all_data)

        if self.rows_per_page == -1:
            total_pages = 1
        else:
            total_pages = max(1, (total_rows + self.rows_per_page - 1) // self.rows_per_page)

        current_page_num = self.current_page + 1

        self.page_label.setText(f"Page {current_page_num} of {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)

    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()
            self.update_pagination_controls()
            self.page_changed.emit(self.current_page)

    def next_page(self):
        """Go to next page"""
        total_rows = len(self.all_data)
        if self.rows_per_page == -1:
            return

        total_pages = (total_rows + self.rows_per_page - 1) // self.rows_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_table()
            self.update_pagination_controls()
            self.page_changed.emit(self.current_page)

    def on_rows_per_page_changed(self, text: str):
        """Handle rows per page change"""
        if text == "All":
            self.rows_per_page = -1
        else:
            self.rows_per_page = int(text)

        self.current_page = 0
        self.update_table()
        self.update_pagination_controls()
        self.rows_per_page_changed.emit(self.rows_per_page)

    def open_column_manager(self):
        """Open column manager dialog"""
        if not self.all_columns:
            return

        dialog = ColumnManagerDialog(self.all_columns, self.visible_columns, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update visible columns
            self.visible_columns = dialog.get_visible_columns()

            # Update column order
            self.all_columns = dialog.get_column_order()

            # Refresh table
            self.update_table()

    def clear(self):
        """Clear table data"""
        self.all_data = []
        self.all_columns = []
        self.visible_columns = []
        self.current_page = 0
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.entry_count_label.setText("0 entries")
        self.update_pagination_controls()

    def get_selected_rows(self) -> List[Dict[str, Any]]:
        """Get data for selected rows"""
        selected = []
        selected_rows = set()

        for item in self.table.selectedItems():
            selected_rows.add(item.row())

        # Calculate actual indices in all_data
        if self.rows_per_page == -1:
            start_idx = 0
        else:
            start_idx = self.current_page * self.rows_per_page

        for row_idx in sorted(selected_rows):
            actual_idx = start_idx + row_idx
            if actual_idx < len(self.all_data):
                selected.append(self.all_data[actual_idx])

        return selected

    def copy_selection_to_clipboard(self):
        """Copy selected cells to clipboard"""
        selection = self.table.selectedItems()
        if not selection:
            return

        # Get selected ranges
        rows = set()
        cols = set()
        for item in selection:
            rows.add(item.row())
            cols.add(item.column())

        # Sort rows and columns
        sorted_rows = sorted(rows)
        sorted_cols = sorted(cols)

        # Build clipboard text
        clipboard_text = []
        for row in sorted_rows:
            row_data = []
            for col in sorted_cols:
                item = self.table.item(row, col)
                if item:
                    row_data.append(item.text())
                else:
                    row_data.append("")
            clipboard_text.append("\t".join(row_data))

        # Copy to clipboard
        final_text = "\n".join(clipboard_text)
        QApplication.clipboard().setText(final_text)

    def show_context_menu(self, position):
        """Show context menu for table cells"""
        item = self.table.itemAt(position)
        if not item:
            return

        menu = QMenu(self.table)

        # Copy action
        copy_action = QAction("Copy", self.table)
        copy_action.triggered.connect(self.copy_selection_to_clipboard)
        menu.addAction(copy_action)

        # Decode URL action (if text looks like a URL)
        text = item.text()
        if text and ('%' in text or 'http' in text.lower()):
            menu.addSeparator()

            decode_action = QAction("Decode URL", self.table)
            decode_action.triggered.connect(lambda: self.show_decoded_url(text))
            menu.addAction(decode_action)

            # VirusTotal action (if callback is set and text looks like URL)
            if self.virustotal_query_requested and 'http' in text.lower():
                vt_action = QAction("Query with VirusTotal", self.table)
                vt_action.triggered.connect(lambda: self.virustotal_query_requested(text))
                menu.addAction(vt_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def show_decoded_url(self, encoded_url: str):
        """Show decoded URL in a dialog"""
        try:
            decoded = unquote(encoded_url)

            dialog = QDialog(self)
            dialog.setWindowTitle("Decoded URL")
            dialog.setMinimumWidth(600)
            dialog.setMinimumHeight(300)

            layout = QVBoxLayout(dialog)

            # Original URL
            layout.addWidget(QLabel("<b>Original URL:</b>"))
            original_text = QTextEdit()
            original_text.setPlainText(encoded_url)
            original_text.setReadOnly(True)
            original_text.setMaximumHeight(80)
            layout.addWidget(original_text)

            # Decoded URL
            layout.addWidget(QLabel("<b>Decoded URL:</b>"))
            decoded_text = QTextEdit()
            decoded_text.setPlainText(decoded)
            decoded_text.setReadOnly(False)  # Allow selection and copying
            layout.addWidget(decoded_text)

            # Buttons
            button_layout = QHBoxLayout()
            copy_btn = QPushButton("Copy Decoded URL")
            copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(decoded))
            button_layout.addWidget(copy_btn)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(close_btn)

            layout.addLayout(button_layout)

            dialog.exec()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Decode Error",
                f"Failed to decode URL:\n\n{str(e)}"
            )
