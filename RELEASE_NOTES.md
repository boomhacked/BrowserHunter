# Browser Hunter v1.0 - Release Notes

## Overview

Browser Hunter is a universal SQLite database browser designed for forensic analysis, with specialized support for browser history files.

---

## Key Features

### Core Capabilities
- **Universal SQLite Support** - Browse any SQLite database with dynamic table discovery
- **Browser History Analysis** - Specialized parsers for Chrome, Firefox, and Edge
- **Read-Only Mode** - Original evidence files never modified
- **SHA256 Verification** - File integrity hashing for chain of custody

### Threat Intelligence
- **VirusTotal Integration** - Scan URLs for threats directly from the interface
- **WHOIS Lookups** - Complete domain registration information via IP2WHOIS
- **Automated Analysis** - Batch query capabilities with rate limiting

### Forensic Tools
- **Timezone Conversion** - View timestamps in any timezone
- **Column Management** - Show/hide and reorder columns dynamically
- **Advanced Search** - Keyword search across all data
- **Pagination** - Efficient handling of large datasets (customizable rows per page)

### Export & Reporting
- **Multiple Formats** - CSV, JSON, Excel (.xlsx), HTML
- **Timezone-Aware** - All timestamps converted to selected timezone
- **Selective Export** - Export filtered results only

---

## Installation

### Option 1: Windows Executable (Recommended)
1. Download `BrowserHunter-v1.0-Windows.zip`
2. Extract the ZIP file
3. Run `BrowserHunter.exe`

### Option 2: From Source
```bash
git clone https://github.com/yourusername/BrowserHunter.git
cd BrowserHunter
pip install -r requirements.txt
python main.py
```

---

## System Requirements

- **OS**: Windows 10 or Windows 11
- **Python**: 3.11.x or 3.12.x (if running from source)
- **RAM**: 8GB minimum (16GB recommended for large databases)
- **Disk Space**: 50MB for application

---

## Security Features

- ✅ Read-only access to source files
- ✅ SHA256 file integrity verification
- ✅ Secure API key storage (0o600 permissions)
- ✅ No telemetry or external connections (except VirusTotal/WHOIS APIs)
- ✅ Air-gap compatible for offline analysis

---

## Documentation

- **README.md** - Feature overview and installation
- **USAGE.md** - Complete usage guide
- **SECURITY.md** - Security policy and best practices
- **BUILD_INSTRUCTIONS.md** - Build from source instructions

---

## License

MIT License - See LICENSE file for details

---

## Legal Disclaimer

**This tool is intended for authorized forensic analysis only.**

Users must have proper legal authorization before analyzing browser data and must comply with all applicable laws and regulations.

---

## Support

- **Issues**: GitHub Issues
- **Documentation**: See USAGE.md
- **Security**: See SECURITY.md

---

