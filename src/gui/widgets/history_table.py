"""
History table widget with pagination
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QTextEdit, QDialog, QDialogButtonBox, QHeaderView, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from typing import List

from ...core.models import HistoryEntry
from ...core.timezone_utils import TimezoneConverter
from ...utils.annotations import AnnotationManager


class AnnotationDialog(QDialog):
    """Dialog for adding/editing annotations"""

    def __init__(self, entry: HistoryEntry, existing_note: str = "", parent=None):
        super().__init__(parent)
        self.entry = entry
        self.setWindowTitle("Add Annotation")
        self.setModal(True)
        self.resize(500, 300)

        layout = QVBoxLayout(self)

        # Entry info
        info_label = QLabel(f"<b>URL:</b> {entry.url}<br><b>Title:</b> {entry.title}")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Note editor
        layout.addWidget(QLabel("Note:"))
        self.note_edit = QTextEdit()
        self.note_edit.setPlainText(existing_note)
        layout.addWidget(self.note_edit)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_note(self) -> str:
        """Get entered note"""
        return self.note_edit.toPlainText()


class HistoryTableWidget(QWidget):
    """Table widget for displaying browser history with pagination"""

    annotation_added = pyqtSignal()

    def __init__(self, annotation_manager: AnnotationManager, parent=None):
        super().__init__(parent)
        self.annotation_manager = annotation_manager
        self.entries: List[HistoryEntry] = []
        self.current_timezone = "UTC"
        self.current_page = 0
        self.page_size = 100

        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'Browser', 'Visit Time', 'URL', 'Title', 'Domain',
            'Visit Count', 'Typed', 'Bookmarked', 'Notes'
        ])

        # Configure table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Browser
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Time
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # URL
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Title
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Domain
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Visit Count
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Typed
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Bookmarked
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Notes

        layout.addWidget(self.table)

        # Pagination controls
        pagination_layout = QHBoxLayout()

        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("Page 0 of 0 (0 entries)")
        pagination_layout.addWidget(self.page_label)

        self.next_btn = QPushButton("Next →")
        self.next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_btn)

        pagination_layout.addStretch()

        # Page size selector
        pagination_layout.addWidget(QLabel("Rows per page:"))
        self.page_size_input = QLineEdit(str(self.page_size))
        self.page_size_input.setMaximumWidth(60)
        self.page_size_input.returnPressed.connect(self.on_page_size_changed)
        pagination_layout.addWidget(self.page_size_input)

        layout.addLayout(pagination_layout)

    def load_entries(self, entries: List[HistoryEntry], timezone: str = "UTC"):
        """
        Load entries into table

        Args:
            entries: List of history entries
            timezone: Timezone for display
        """
        self.entries = entries
        self.current_timezone = timezone
        self.current_page = 0
        self.update_table()

    def update_table(self):
        """Update table with current page"""
        # Calculate pagination
        total_entries = len(self.entries)
        total_pages = (total_entries + self.page_size - 1) // self.page_size if total_entries > 0 else 0
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, total_entries)

        # Get page entries
        page_entries = self.entries[start_idx:end_idx]

        # Update table
        self.table.setRowCount(len(page_entries))

        for row, entry in enumerate(page_entries):
            # Browser
            browser_item = QTableWidgetItem(entry.browser)
            self.set_browser_color(browser_item, entry.browser)
            self.table.setItem(row, 0, browser_item)

            # Visit time
            visit_time = TimezoneConverter.convert_timezone(entry.visit_time, self.current_timezone)
            time_str = TimezoneConverter.format_datetime(visit_time, fmt="%Y-%m-%d %H:%M:%S")
            self.table.setItem(row, 1, QTableWidgetItem(time_str))

            # URL
            self.table.setItem(row, 2, QTableWidgetItem(entry.url))

            # Title
            self.table.setItem(row, 3, QTableWidgetItem(entry.title or ""))

            # Domain
            self.table.setItem(row, 4, QTableWidgetItem(entry.domain))

            # Visit count
            self.table.setItem(row, 5, QTableWidgetItem(str(entry.visit_count)))

            # Typed count
            self.table.setItem(row, 6, QTableWidgetItem(str(entry.typed_count)))

            # Bookmarked
            entry_id = AnnotationManager.generate_entry_id(entry.url, entry.visit_time)
            is_bookmarked = self.annotation_manager.is_bookmarked(entry_id)
            bookmark_item = QTableWidgetItem("★" if is_bookmarked else "")
            self.table.setItem(row, 7, bookmark_item)

            # Notes
            annotation = self.annotation_manager.get_annotation(entry_id)
            has_note = annotation is not None and annotation.get('note', '')
            note_item = QTableWidgetItem("📝" if has_note else "")
            self.table.setItem(row, 8, note_item)

        # Update pagination controls
        self.page_label.setText(
            f"Page {self.current_page + 1} of {total_pages} ({total_entries} entries, showing {start_idx + 1}-{end_idx})"
        )
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)

    def set_browser_color(self, item: QTableWidgetItem, browser: str):
        """Set background color based on browser"""
        colors = {
            'Chrome': QColor(255, 217, 102),  # Yellow
            'Firefox': QColor(255, 153, 102),  # Orange
            'Edge': QColor(153, 204, 255),     # Blue
        }
        color = colors.get(browser, QColor(255, 255, 255))
        item.setBackground(color)

    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self):
        """Go to next page"""
        total_pages = (len(self.entries) + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_table()

    def on_page_size_changed(self):
        """Handle page size change"""
        try:
            new_size = int(self.page_size_input.text())
            if new_size > 0:
                self.page_size = new_size
                self.current_page = 0
                self.update_table()
        except ValueError:
            self.page_size_input.setText(str(self.page_size))

    def show_context_menu(self, position):
        """Show context menu"""
        menu = QMenu()

        add_note_action = QAction("Add/Edit Note", self)
        add_note_action.triggered.connect(self.add_annotation)
        menu.addAction(add_note_action)

        bookmark_action = QAction("Toggle Bookmark", self)
        bookmark_action.triggered.connect(self.toggle_bookmark)
        menu.addAction(bookmark_action)

        menu.addSeparator()

        copy_url_action = QAction("Copy URL", self)
        copy_url_action.triggered.connect(self.copy_url)
        menu.addAction(copy_url_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def add_annotation(self):
        """Add annotation to selected entry"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        # Get entry
        global_idx = self.current_page * self.page_size + current_row
        entry = self.entries[global_idx]

        # Get existing annotation
        entry_id = AnnotationManager.generate_entry_id(entry.url, entry.visit_time)
        existing = self.annotation_manager.get_annotation(entry_id)
        existing_note = existing.get('note', '') if existing else ''

        # Show dialog
        dialog = AnnotationDialog(entry, existing_note, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            note = dialog.get_note()
            self.annotation_manager.add_annotation(entry_id, note)
            self.update_table()
            self.annotation_added.emit()

    def toggle_bookmark(self):
        """Toggle bookmark for selected entry"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        # Get entry
        global_idx = self.current_page * self.page_size + current_row
        entry = self.entries[global_idx]

        entry_id = AnnotationManager.generate_entry_id(entry.url, entry.visit_time)

        if self.annotation_manager.is_bookmarked(entry_id):
            self.annotation_manager.remove_bookmark(entry_id)
        else:
            self.annotation_manager.add_bookmark(entry_id, entry.url, entry.title)

        self.update_table()

    def copy_url(self):
        """Copy URL to clipboard"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        url = self.table.item(current_row, 2).text()

        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(url)
