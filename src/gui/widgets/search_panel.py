"""
Search and filter panel
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QCheckBox, QDateTimeEdit, QComboBox,
    QSpinBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import pyqtSignal, QDateTime
from datetime import datetime

from ...core.search import SortOptions


class SearchPanel(QWidget):
    """Search and filter panel"""

    search_triggered = pyqtSignal(dict)
    clear_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Main search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Keyword:"))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Enter keyword to search...")
        self.keyword_input.returnPressed.connect(self.on_search)
        search_layout.addWidget(self.keyword_input)

        self.case_sensitive_cb = QCheckBox("Case Sensitive")
        search_layout.addWidget(self.case_sensitive_cb)

        self.regex_cb = QCheckBox("Regex")
        search_layout.addWidget(self.regex_cb)

        layout.addLayout(search_layout)

        # Advanced filters (collapsible)
        filters_group = QGroupBox("Advanced Filters")
        filters_layout = QFormLayout()

        # URL pattern
        self.url_pattern_input = QLineEdit()
        self.url_pattern_input.setPlaceholderText("URL pattern (regex)")
        filters_layout.addRow("URL Pattern:", self.url_pattern_input)

        # Date range
        date_layout = QHBoxLayout()
        self.start_date = QDateTimeEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDateTime(QDateTime.currentDateTime().addDays(-30))
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.start_date)

        self.end_date = QDateTimeEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDateTime(QDateTime.currentDateTime())
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.end_date)

        self.enable_date_filter = QCheckBox("Enable")
        date_layout.addWidget(self.enable_date_filter)

        filters_layout.addRow("Date Range:", date_layout)

        # Visit count
        visit_layout = QHBoxLayout()
        self.min_visits = QSpinBox()
        self.min_visits.setMinimum(0)
        self.min_visits.setMaximum(999999)
        visit_layout.addWidget(QLabel("Min:"))
        visit_layout.addWidget(self.min_visits)

        self.max_visits = QSpinBox()
        self.max_visits.setMinimum(0)
        self.max_visits.setMaximum(999999)
        self.max_visits.setValue(999999)
        visit_layout.addWidget(QLabel("Max:"))
        visit_layout.addWidget(self.max_visits)

        self.enable_visit_filter = QCheckBox("Enable")
        visit_layout.addWidget(self.enable_visit_filter)

        filters_layout.addRow("Visit Count:", visit_layout)

        # Browser filter
        browser_layout = QHBoxLayout()
        self.chrome_cb = QCheckBox("Chrome")
        self.chrome_cb.setChecked(True)
        browser_layout.addWidget(self.chrome_cb)

        self.firefox_cb = QCheckBox("Firefox")
        self.firefox_cb.setChecked(True)
        browser_layout.addWidget(self.firefox_cb)

        self.edge_cb = QCheckBox("Edge")
        self.edge_cb.setChecked(True)
        browser_layout.addWidget(self.edge_cb)

        filters_layout.addRow("Browsers:", browser_layout)

        # Sort options
        sort_layout = QHBoxLayout()
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Date", "URL", "Title", "Domain", "Visit Count", "Browser"
        ])
        sort_layout.addWidget(self.sort_combo)

        self.sort_ascending = QCheckBox("Ascending")
        sort_layout.addWidget(self.sort_ascending)

        filters_layout.addRow("Sort By:", sort_layout)

        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.on_search)
        button_layout.addWidget(self.search_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.on_clear)
        button_layout.addWidget(self.clear_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

    def on_search(self):
        """Trigger search"""
        search_params = self.get_search_params()
        self.search_triggered.emit(search_params)

    def on_clear(self):
        """Clear all filters"""
        self.keyword_input.clear()
        self.url_pattern_input.clear()
        self.case_sensitive_cb.setChecked(False)
        self.regex_cb.setChecked(False)
        self.enable_date_filter.setChecked(False)
        self.enable_visit_filter.setChecked(False)
        self.chrome_cb.setChecked(True)
        self.firefox_cb.setChecked(True)
        self.edge_cb.setChecked(True)
        self.sort_combo.setCurrentIndex(0)
        self.sort_ascending.setChecked(False)

        self.clear_triggered.emit()

    def get_search_params(self) -> dict:
        """Get search parameters"""
        params = {
            'keyword': self.keyword_input.text(),
            'case_sensitive': self.case_sensitive_cb.isChecked(),
            'use_regex': self.regex_cb.isChecked(),
            'url_pattern': self.url_pattern_input.text(),
        }

        # Date range
        if self.enable_date_filter.isChecked():
            params['start_date'] = self.start_date.dateTime().toPyDateTime()
            params['end_date'] = self.end_date.dateTime().toPyDateTime()

        # Visit count
        if self.enable_visit_filter.isChecked():
            params['min_visits'] = self.min_visits.value()
            params['max_visits'] = self.max_visits.value()

        # Browsers
        browsers = []
        if self.chrome_cb.isChecked():
            browsers.append('Chrome')
        if self.firefox_cb.isChecked():
            browsers.append('Firefox')
        if self.edge_cb.isChecked():
            browsers.append('Edge')
        params['browsers'] = browsers

        # Sort
        sort_map = {
            'Date': SortOptions.SORT_BY_DATE,
            'URL': SortOptions.SORT_BY_URL,
            'Title': SortOptions.SORT_BY_TITLE,
            'Domain': SortOptions.SORT_BY_DOMAIN,
            'Visit Count': SortOptions.SORT_BY_VISIT_COUNT,
            'Browser': SortOptions.SORT_BY_BROWSER,
        }
        params['sort_by'] = sort_map.get(self.sort_combo.currentText(), SortOptions.SORT_BY_DATE)
        params['sort_ascending'] = self.sort_ascending.isChecked()

        return params
