# Browser Hunter 🔍

**Universal SQLite Database Browser for Forensic Analysis**

A portable powerful desktop application for forensic analysts that can analyze **any SQLite database**, with specialized support for browser history files. Features dynamic table browsing, threat intelligence integration, and comprehensive export capabilities.

![Version](https://img.shields.io/badge/version-1.0-blue)
![Python](https://img.shields.io/badge/python-3.11%20|%203.12-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## 🎯 Key Features

### Universal Database Support
- **Browse Any SQLite Database** - Works with any SQLite file, not just browser history
- **Dynamic Table Discovery** - Automatically detects all tables and columns
- **Column Management** - Show/hide columns, reorder, and resize as needed
- **Smart Detection** - Auto-identifies Chrome, Firefox, and Edge databases

### Threat Intelligence Integration
- **VirusTotal Integration** - Scan URLs directly from the interface
  - Real-time threat detection
  - Detailed analysis results
  - Detection engine breakdown
- **WHOIS Lookup** - Complete domain registration information
  - Powered by IP2WHOIS API
  - Registrant and admin contact details
  - Domain age, creation date, expiration
  - Name servers and status

### Forensic Analysis Tools
- **Read-Only Mode** - Original files never modified
- **File Integrity** - SHA256 hash verification
- **Timezone Conversion** - View timestamps in any timezone
- **Keyword Search** - Fast search across all columns
- **Advanced Filtering** - Date ranges, patterns, and custom queries

### Data Export & Reporting
- **Multiple Formats** - CSV, JSON, Excel (.xlsx)
- **Timezone-Aware** - All timestamps converted to selected timezone
- **Selective Export** - Export filtered results only
- **Formatted Reports** - Professional JSON reports with styling

### User Interface
- **Pagination** - Handle large databases efficiently
- **Rows Per Page** - Customizable (50, 100, 500, 1000 rows)
- **Sortable Columns** - Click headers to sort
- **Context Menus** - Right-click for quick actions
- **URL Decoding** - Decode encoded URLs easily
- **Drag & Drop** - Drop database files directly into window

---

## ⚙️ System Requirements

- **Operating System**: Windows 10 or Windows 11
- **Python**: 3.11.x or 3.12.x (if running from source)
- **RAM**: 8GB minimum (16GB recommended for large databases)
- **Disk Space**: 50MB for application + space for temporary database copies

---

## 🚀 Installation

### Option 1: Windows Executable (Recommended)

1. Download the latest release from GitHub
2. Extract the ZIP file
3. Run `BrowserHunter.exe`

No Python installation required!

### Option 2: Run from Source

**Prerequisites:**
- Python 3.11 or 3.12
- Git (optional)

**Steps:**

```bash
# Clone the repository
git clone https://github.com/yourusername/BrowserHunter.git
cd BrowserHunter

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

---

## 📖 Usage Guide

### Loading a Database

1. Click **"Load Database"** button
2. Navigate to your SQLite file:
   - **Chrome**: `C:\Users\[Username]\AppData\Local\Google\Chrome\User Data\Default\History`
   - **Firefox**: `C:\Users\[Username]\AppData\Roaming\Mozilla\Firefox\Profiles\[ProfileName]\places.sqlite`
   - **Edge**: `C:\Users\[Username]\AppData\Local\Microsoft\Edge\User Data\Default\History`
   - **Any SQLite**: Select any `.db` or `.sqlite` file
3. File loads in read-only mode (original never modified)

**Tip:** You can also drag & drop database files directly into the window!

### Browsing Tables

1. **Select Table** - Use dropdown to choose which table to view
2. **Manage Columns** - Click "Manage Columns" to show/hide/reorder
3. **Adjust Display** - Resize columns by dragging headers
4. **Sort Data** - Click column headers to sort ascending/descending

### Searching Data

1. **Keyword Search** - Enter search term in search box
2. **Apply Filters** - Use date range, visit count, or other filters
3. **View Results** - Paginate through matches
4. **Copy Data** - Select cells and press Ctrl+C to copy

### VirusTotal Scanning

**Setup:**
1. Go to **Settings → VirusTotal Settings**
2. Enter your VirusTotal API key ([Get one free](https://www.virustotal.com/))
3. Click "Test API Key" to verify

**Usage:**
1. Right-click any URL in the table
2. Select **"Query with VirusTotal"**
3. View real-time threat analysis results
4. See WHOIS information (if IP2WHOIS key configured)

### WHOIS Lookups

**Setup:**
1. Go to **Settings → IP2WHOIS Settings**
2. Enter your IP2WHOIS API key ([Get one](https://www.ip2whois.com/))
3. Click "Test API Key" to verify

**Usage:**
- WHOIS data appears automatically when scanning URLs with VirusTotal
- Shows registrant, admin contact, domain age, and more

### Exporting Data

1. Click **File → Export**
2. Choose format:
   - **CSV** - For Excel/spreadsheet analysis
   - **JSON** - For programmatic processing
   - **XLSX** - Formatted Excel workbook
3. Select timezone for timestamp conversion
4. Choose save location

### Statistics & Analysis

1. Click **Statistics** tab
2. View:
   - Top domains visited
   - Top URLs
   - Data overview and column statistics
3. Right-click domains/URLs to query with VirusTotal

---

## 🔒 Security Features

### Evidence Integrity
- ✅ **Read-Only Access** - Original files never modified
- ✅ **Temporary Copies** - All analysis done on secure copies
- ✅ **SHA256 Verification** - File integrity hashing
- ✅ **Secure Permissions** - Temp files created with 0o600 permissions

### API Key Security
- ✅ **Local Storage** - API keys stored locally only (never transmitted)
- ✅ **Secure Permissions** - Config file protected with 0o600 (owner read/write only)
- ✅ **No Telemetry** - No data sent anywhere except VirusTotal/WHOIS APIs

### Privacy
- ✅ **Offline Capable** - Works without internet (except API features)
- ✅ **Air-Gap Compatible** - Core features work offline
- ✅ **No Cloud Storage** - All data stays on your machine

---

## 🎓 Use Cases

- **Digital Forensics** - Investigate browser history in criminal/civil cases
- **Incident Response** - Analyze malware infections and data exfiltration
- **Threat Hunting** - Identify malicious URLs and C2 communications
- **Compliance Audits** - Review employee browsing activity
- **Data Recovery** - Extract data from damaged browser profiles
- **Security Research** - Study browsing patterns and behaviors

---

## 🛠️ Building from Source

To create a standalone Windows executable:

```bash
# Run the build script
build.bat
```

The executable will be created in `dist\BrowserHunter\BrowserHunter.exe`

**Build Requirements:**
- Python 3.11 or 3.12
- PyInstaller 6.0+
- All dependencies from requirements.txt

---

## 📂 Supported Database Types

### Browser Databases
| Browser | Database File | Location |
|---------|--------------|----------|
| **Chrome** | `History` | `%LOCALAPPDATA%\Google\Chrome\User Data\Default\` |
| **Edge** | `History` | `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\` |
| **Firefox** | `places.sqlite` | `%APPDATA%\Mozilla\Firefox\Profiles\[Profile]\` |

### Generic SQLite
- **Any SQLite database** with standard table structure
- Automatically adapts to discovered schema
- Supports custom applications and tools

---

## 🔧 Configuration

### API Keys

API keys are stored in: `~/.browserhunter/config.json`

This file is automatically created with secure permissions (0o600 on Unix systems).

### Temporary Files

Temporary database copies are stored in:
- Windows: `%TEMP%\BrowserHunter\`

These files are automatically cleaned up when the application closes.

---

## 📝 Tips & Best Practices

### Performance
- **Large Databases**: Use pagination (100-500 rows per page)
- **Filtering**: Apply filters before exporting to reduce file size
- **Memory**: Close unused tabs to free memory

### Forensic Workflow
1. Create working copy of evidence file
2. Calculate hash of original file first
3. Load working copy in Browser Hunter
4. Document findings with annotations
5. Export results with timezone-aware timestamps
6. Include file hash in final report

### VirusTotal Best Practices
- **Free Tier**: 4 requests per minute, 500 per day
- **Batch Processing**: Space out queries to avoid rate limits
- **Save Results**: Export threat intelligence findings to CSV

---

## ⚠️ Known Limitations

- Very large databases (>1M entries) may have slower initial load
- VirusTotal free tier has rate limits (4 req/min, 500/day)
- Some browser extensions may store data in separate databases

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details

---

## ⚠️ Legal Disclaimer

**This tool is intended for authorized forensic analysis only.**

Users must:
- Have proper legal authorization before analyzing browser data
- Comply with all applicable laws and regulations
- Respect privacy rights and data protection laws
- Use this tool ethically and responsibly

The developers assume no liability for misuse of this tool.

---

## 🤝 Contributing

Contributions are welcome! Please:
- Fork the repository
- Create a feature branch
- Submit a pull request with clear description

For bug reports and feature requests, please open an issue on GitHub.

---



