"""
VirusTotal analysis panel and settings
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QDialog, QLineEdit, QDialogButtonBox,
    QMessageBox, QGroupBox, QScrollArea, QTableWidget,
    QTableWidgetItem, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from typing import Optional, Dict, Any
import json
from pathlib import Path

from ...utils.virustotal_api import VirusTotalAPI
from ...utils.ip2whois_api import IP2WHOISAPI


class VirusTotalSettingsDialog(QDialog):
    """Dialog for configuring VirusTotal API settings"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_key = self.load_api_key()
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("VirusTotal Settings")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Instructions
        info_label = QLabel(
            "Enter your VirusTotal API key. You can get a free API key by signing up at:\n"
            "https://www.virustotal.com/"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # API Key input
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your VirusTotal API key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self.api_key:
            self.api_key_input.setText(self.api_key)
        key_layout.addWidget(self.api_key_input)

        self.show_key_btn = QPushButton("Show")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.clicked.connect(self.toggle_api_key_visibility)
        key_layout.addWidget(self.show_key_btn)

        layout.addLayout(key_layout)

        # Test button
        self.test_btn = QPushButton("Test API Key")
        self.test_btn.clicked.connect(self.test_api_key)
        layout.addWidget(self.test_btn)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.show_key_btn.isChecked():
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_key_btn.setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn.setText("Show")

    def test_api_key(self):
        """Test the API key"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            self.status_label.setText("⚠️ Please enter an API key")
            self.status_label.setStyleSheet("color: orange;")
            return

        self.status_label.setText("Testing API key...")
        self.status_label.setStyleSheet("color: blue;")
        self.test_btn.setEnabled(False)

        try:
            vt = VirusTotalAPI(api_key)
            is_valid, message = vt.test_api_key()

            if is_valid:
                self.status_label.setText(f"✓ {message}")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText(f"✗ {message}")
                self.status_label.setStyleSheet("color: red;")

        except Exception as e:
            self.status_label.setText(f"✗ Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")

        self.test_btn.setEnabled(True)

    def get_api_key(self) -> str:
        """Get the API key"""
        return self.api_key_input.text().strip()

    def accept(self):
        """Save and close"""
        api_key = self.get_api_key()
        if api_key:
            self.save_api_key(api_key)
        super().accept()

    @staticmethod
    def load_api_key() -> str:
        """Load API key from config file"""
        try:
            config_file = Path.home() / ".browserhunter" / "config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get("virustotal_api_key", "")
        except:
            pass
        return ""

    @staticmethod
    def save_api_key(api_key: str):
        """Save API key to config file with secure permissions"""
        try:
            import os
            import stat

            config_dir = Path.home() / ".browserhunter"
            config_dir.mkdir(parents=True, exist_ok=True)

            # Set secure directory permissions (owner only: rwx------)
            try:
                os.chmod(config_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            except:
                pass  # Windows doesn't support chmod the same way

            config_file = config_dir / "config.json"

            # Load existing config
            config = {}
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)

            # Update API key
            config["virustotal_api_key"] = api_key

            # Save config with secure permissions
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)

            # Set secure file permissions (owner only: rw-------)
            try:
                os.chmod(config_file, stat.S_IRUSR | stat.S_IWUSR)
            except:
                pass  # Windows doesn't support chmod the same way

        except Exception as e:
            print(f"Failed to save API key: {e}")


class IP2WHOISSettingsDialog(QDialog):
    """Dialog for configuring IP2WHOIS API settings"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_key = self.load_api_key()
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("IP2WHOIS Settings")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Instructions
        info_label = QLabel(
            "Enter your IP2WHOIS API key for WHOIS lookups. You can get an API key at:\n"
            "https://www.ip2whois.com/"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # API Key input
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your IP2WHOIS API key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self.api_key:
            self.api_key_input.setText(self.api_key)
        key_layout.addWidget(self.api_key_input)

        self.show_key_btn = QPushButton("Show")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.clicked.connect(self.toggle_api_key_visibility)
        key_layout.addWidget(self.show_key_btn)

        layout.addLayout(key_layout)

        # Test button
        self.test_btn = QPushButton("Test API Key")
        self.test_btn.clicked.connect(self.test_api_key)
        layout.addWidget(self.test_btn)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.show_key_btn.isChecked():
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_key_btn.setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn.setText("Show")

    def test_api_key(self):
        """Test the API key"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            self.status_label.setText("⚠️ Please enter an API key")
            self.status_label.setStyleSheet("color: orange;")
            return

        self.status_label.setText("Testing API key...")
        self.status_label.setStyleSheet("color: blue;")
        self.test_btn.setEnabled(False)

        try:
            whois_api = IP2WHOISAPI(api_key)
            is_valid, message = whois_api.test_api_key()

            if is_valid:
                self.status_label.setText(f"✓ {message}")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText(f"✗ {message}")
                self.status_label.setStyleSheet("color: red;")

        except Exception as e:
            self.status_label.setText(f"✗ Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")

        self.test_btn.setEnabled(True)

    def get_api_key(self) -> str:
        """Get the API key"""
        return self.api_key_input.text().strip()

    def accept(self):
        """Save and close"""
        api_key = self.get_api_key()
        if api_key:
            self.save_api_key(api_key)
        super().accept()

    @staticmethod
    def load_api_key() -> str:
        """Load API key from config file"""
        try:
            config_file = Path.home() / ".browserhunter" / "config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get("ip2whois_api_key", "")
        except:
            pass
        return ""

    @staticmethod
    def save_api_key(api_key: str):
        """Save API key to config file with secure permissions"""
        try:
            import os
            import stat

            config_dir = Path.home() / ".browserhunter"
            config_dir.mkdir(parents=True, exist_ok=True)

            # Set secure directory permissions (owner only: rwx------)
            try:
                os.chmod(config_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            except:
                pass  # Windows doesn't support chmod the same way

            config_file = config_dir / "config.json"

            # Load existing config
            config = {}
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)

            # Update API key
            config["ip2whois_api_key"] = api_key

            # Save config with secure permissions
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)

            # Set secure file permissions (owner only: rw-------)
            try:
                os.chmod(config_file, stat.S_IRUSR | stat.S_IWUSR)
            except:
                pass  # Windows doesn't support chmod the same way

        except Exception as e:
            print(f"Failed to save API key: {e}")


class VirusTotalAnalysisThread(QThread):
    """Background thread for VirusTotal analysis and IP2WHOIS"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, vt_api_key: str, url: str, ip2whois_api_key: Optional[str] = None):
        super().__init__()
        self.vt_api_key = vt_api_key
        self.url = url
        self.ip2whois_api_key = ip2whois_api_key

    def run(self):
        """Run analysis"""
        try:
            # Get VirusTotal results
            vt = VirusTotalAPI(self.vt_api_key)
            result = vt.analyze_url(self.url)

            # If IP2WHOIS key is available, always try to get WHOIS (even if VT has error)
            if self.ip2whois_api_key:
                from urllib.parse import urlparse
                parsed = urlparse(self.url)
                domain = parsed.netloc

                # Remove www. prefix for WHOIS queries
                if domain.startswith('www.'):
                    domain = domain[4:]

                if domain:
                    try:
                        whois_api = IP2WHOISAPI(self.ip2whois_api_key)
                        whois_result = whois_api.get_whois(domain)

                        # Debug: Print WHOIS result
                        print(f"DEBUG: IP2WHOIS WHOIS result for {domain}: {whois_result}")

                        # Merge WHOIS data into result (prefer IP2WHOIS WHOIS)
                        if "error" not in whois_result and whois_result:
                            result["whois"] = whois_result
                            result["whois_source"] = "IP2WHOIS"
                            print(f"DEBUG: WHOIS data added to result")
                        else:
                            print(f"DEBUG: WHOIS data has error or is empty")
                    except Exception as e:
                        print(f"DEBUG: Exception getting WHOIS: {str(e)}")
                        # Don't fail the whole query if WHOIS fails
                        pass

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class VirusTotalPanel(QWidget):
    """Panel for displaying VirusTotal analysis results"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title bar with close button
        title_layout = QHBoxLayout()
        title = QLabel("<h2>VirusTotal Analysis</h2>")
        title_layout.addWidget(title)
        title_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setMaximumWidth(30)
        close_btn.setMaximumHeight(30)
        close_btn.setToolTip("Close panel")
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(close_btn)

        layout.addLayout(title_layout)

        # Scroll area for results
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)

        # Default message
        self.default_label = QLabel(
            "Right-click on a URL in the table and select\n"
            "'Query with VirusTotal' to analyze it."
        )
        self.default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.default_label.setStyleSheet("color: gray; padding: 20px;")
        self.results_layout.addWidget(self.default_label)

        scroll.setWidget(self.results_widget)
        layout.addWidget(scroll)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

    def show_loading(self, url: str):
        """Show loading state"""
        # Clear previous results
        self.clear_results()

        self.default_label.setText(f"Analyzing URL with VirusTotal...\n\n{url}")
        self.default_label.setStyleSheet("color: blue; padding: 20px;")
        self.progress_bar.show()

    def show_results(self, results: Dict[str, Any]):
        """Display analysis results"""
        self.progress_bar.hide()

        # Clear previous results
        self.clear_results()

        if results.get("error"):
            self.show_error(results["error"])
            return

        # URL
        url_group = QGroupBox("URL")
        url_layout = QVBoxLayout()
        url_label = QLabel(results.get("url", "N/A"))
        url_label.setWordWrap(True)
        url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        url_layout.addWidget(url_label)
        url_group.setLayout(url_layout)
        self.results_layout.addWidget(url_group)

        # Detection stats
        stats_group = QGroupBox("Detection Results")
        stats_layout = QVBoxLayout()

        stats = results.get("stats", {})
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        undetected = stats.get("undetected", 0)
        harmless = stats.get("harmless", 0)

        # Color-coded detection ratio
        detection_ratio = results.get("detection_ratio", "0/0")
        if malicious > 0:
            color = "red"
            status = "⚠️ MALICIOUS"
        elif suspicious > 0:
            color = "orange"
            status = "⚠️ SUSPICIOUS"
        else:
            color = "green"
            status = "✓ CLEAN"

        ratio_label = QLabel(f"<h2 style='color: {color};'>{status}</h2>")
        stats_layout.addWidget(ratio_label)

        stats_text = f"""
        <table>
        <tr><td><b>Detection Ratio:</b></td><td>{detection_ratio}</td></tr>
        <tr><td><b>Malicious:</b></td><td style='color: red;'>{malicious}</td></tr>
        <tr><td><b>Suspicious:</b></td><td style='color: orange;'>{suspicious}</td></tr>
        <tr><td><b>Undetected:</b></td><td>{undetected}</td></tr>
        <tr><td><b>Harmless:</b></td><td style='color: green;'>{harmless}</td></tr>
        <tr><td><b>Analysis Date:</b></td><td>{results.get('analysis_date', 'N/A')}</td></tr>
        </table>
        """
        stats_label = QLabel(stats_text)
        stats_layout.addWidget(stats_label)

        stats_group.setLayout(stats_layout)
        self.results_layout.addWidget(stats_group)

        # Detected engines
        detected_engines = results.get("detected_engines", [])
        if detected_engines:
            engines_group = QGroupBox("Detected By")
            engines_layout = QVBoxLayout()

            engines_table = QTableWidget()
            engines_table.setColumnCount(3)
            engines_table.setHorizontalHeaderLabels(["Engine", "Category", "Result"])
            engines_table.setRowCount(len(detected_engines))

            for row, engine in enumerate(detected_engines):
                engines_table.setItem(row, 0, QTableWidgetItem(engine.get("engine", "")))
                engines_table.setItem(row, 1, QTableWidgetItem(engine.get("category", "")))
                engines_table.setItem(row, 2, QTableWidgetItem(engine.get("result", "")))

            engines_table.resizeColumnsToContents()
            engines_layout.addWidget(engines_table)

            engines_group.setLayout(engines_layout)
            self.results_layout.addWidget(engines_group)

        # WHOIS data
        whois = results.get("whois", {})
        whois_source = results.get("whois_source", "")

        # Debug output
        print(f"DEBUG: WHOIS in results: {whois}")
        print(f"DEBUG: WHOIS source: {whois_source}")
        print(f"DEBUG: WHOIS bool check: {bool(whois)}")

        if whois:
            # Show source of WHOIS data if available
            title = "WHOIS Information"
            if whois_source:
                title += f" (Source: {whois_source})"

            whois_group = QGroupBox(title)
            whois_layout = QVBoxLayout()

            whois_text = "<table style='width: 100%; table-layout: fixed;'>"
            for key, value in whois.items():
                # Escape HTML to prevent XSS
                key_safe = str(key).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                value_safe = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                whois_text += f"<tr><td style='width: 40%; word-wrap: break-word;'><b>{key_safe}:</b></td><td style='width: 60%; word-wrap: break-word;'>{value_safe}</td></tr>"
            whois_text += "</table>"

            whois_label = QLabel(whois_text)
            whois_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            whois_label.setWordWrap(True)
            whois_layout.addWidget(whois_label)

            whois_group.setLayout(whois_layout)
            self.results_layout.addWidget(whois_group)

        self.results_layout.addStretch()

    def show_error(self, error: str):
        """Show error message"""
        self.progress_bar.hide()
        self.default_label.setText(f"Error:\n\n{error}")
        self.default_label.setStyleSheet("color: red; padding: 20px;")
        self.default_label.show()

    def clear_results(self):
        """Clear all results"""
        # Remove all widgets except the default label
        while self.results_layout.count() > 0:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Re-add default label
        self.default_label = QLabel()
        self.default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_layout.addWidget(self.default_label)
