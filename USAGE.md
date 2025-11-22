# Browser Hunter - Usage Guide

Complete guide to using Browser Hunter for forensic analysis and database browsing.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Loading Databases](#loading-databases)
- [Browsing Data](#browsing-data)
- [Searching & Filtering](#searching--filtering)
- [Threat Intelligence](#threat-intelligence)
- [Exporting Data](#exporting-data)
- [Advanced Features](#advanced-features)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Tips & Tricks](#tips--tricks)

---

## Getting Started

### First Launch

1. **Run the application**:
   - From executable: Double-click `BrowserHunter.exe`
   - From source: Run `python main.py`

2. **Main window opens** with:
   - Menu bar (File, Settings, Help)
   - Toolbar with "Load Database" button
   - Empty table area
   - Status bar at bottom

### Understanding the Interface

**Main Components:**
- **Table Dropdown** - Select which database table to view
- **Column Manager** - Show/hide and reorder columns
- **Search Box** - Quick keyword search
- **Pagination Controls** - Navigate through large datasets
- **Statistics Tab** - View data overview and top items
- **VirusTotal Panel** - Threat intelligence results (right side)

---

## Loading Databases

### Method 1: Load Button

1. Click **"Load Database"** button in toolbar
2. Navigate to your SQLite database file
3. Select the file and click **Open**
4. Database loads in read-only mode

### Method 2: Drag & Drop

1. Locate your SQLite database file in Windows Explorer
2. Drag the file into the Browser Hunter window
3. Drop it anywhere in the window
4. Database loads automatically

### Common Database Locations

**Chrome:**
```
C:\Users\[Username]\AppData\Local\Google\Chrome\User Data\Default\History
```

**Firefox:**
```
C:\Users\[Username]\AppData\Roaming\Mozilla\Firefox\Profiles\[ProfileName]\places.sqlite
```

**Edge:**
```
C:\Users\[Username]\AppData\Local\Microsoft\Edge\User Data\Default\History
```

**Note:** The `History` file has no extension - select "All Files (*)" in the file dialog.

---

## Browsing Data

### Selecting Tables

1. **Table Dropdown** - Located near top of window
2. Click dropdown to see all available tables
3. Select a table to view its data

**Common Tables:**
- **urls** - Chrome/Edge browsing history
- **visits** - Chrome/Edge visit records
- **moz_places** - Firefox browsing history
- **moz_historyvisits** - Firefox visit records

### Managing Columns

**Show/Hide Columns:**
1. Click **"Manage Columns"** button
2. Check/uncheck columns to show/hide
3. Click **OK** to apply changes

**Reorder Columns:**
1. In Column Manager dialog
2. Select a column
3. Click **Up** or **Down** to reorder

**Resize Columns:**
- Drag column header borders to resize
- Double-click border for auto-fit

### Sorting Data

- Click any **column header** to sort
- First click: **Ascending** order
- Second click: **Descending** order
- Third click: **Remove sort**

### Pagination

**Controls:**
- **< Previous** - Go to previous page
- **Next >** - Go to next page
- **Page indicator** - Shows current page and total
- **Rows Per Page** - Choose 50, 100, 500, or 1000 rows

---

## Searching & Filtering

### Quick Keyword Search

1. Enter search term in **Search box**
2. Press **Enter** or click **Search**
3. Table filters to matching rows
4. Searches across all visible columns

### Copy Cell Data

**Single Cell:**
1. Click to select a cell
2. Press **Ctrl+C** to copy

**Multiple Cells:**
1. Click and drag to select cells
2. Press **Ctrl+C** to copy
3. Paste into Excel/Notepad (tab-delimited)

---

## Threat Intelligence

### VirusTotal Integration

**Setup (One-time):**
1. Go to **Settings → VirusTotal Settings**
2. Enter your VirusTotal API key
   - Get free key at: https://www.virustotal.com/
   - Free tier: 4 requests/minute, 500/day
3. Click **"Test API Key"** to verify
4. Click **"Save"**

**Scan a URL:**
1. Right-click any URL in the table
2. Select **"Query with VirusTotal"**
3. Wait for analysis (5-10 seconds)
4. Results appear in right-side panel

**Results Include:**
- **Detection Ratio** - e.g., "2/89" (2 engines detected threats)
- **Analysis Date** - When URL was last scanned
- **Detection Engines** - List of engines that flagged the URL
- **Reputation Score** - Community reputation rating
- **Categories** - URL categorization

### WHOIS Lookups

**Setup (One-time):**
1. Go to **Settings → IP2WHOIS Settings**
2. Enter your IP2WHOIS API key
   - Get key at: https://www.ip2whois.com/
3. Click **"Test API Key"** to verify
4. Click **"Save"**

**View WHOIS Data:**
- WHOIS information appears automatically below VirusTotal results
- Shows when querying a URL with VirusTotal

**WHOIS Information Includes:**
- **Domain** - Domain name
- **Creation/Update/Expiration Dates**
- **Domain Age** - Age in years and days
- **Registrar** - Domain registrar name
- **Registrant** - Name, organization, country (if public)
- **Admin Contact** - Admin contact details (if public)
- **Name Servers** - DNS servers
- **Status** - Domain status

---

## Exporting Data

### Export Current View

1. Click **File → Export** (or press Ctrl+E)
2. **Select Format:**
   - **CSV** - For Excel, spreadsheets
   - **JSON** - For programming, APIs
   - **XLSX** - Excel workbook with formatting
   - **HTML** - Formatted report for viewing

3. **Choose Timezone** (optional):
   - Select timezone for timestamp conversion
   - All timestamps converted to selected timezone

4. **Select Save Location**
5. Click **Save**

---

## Advanced Features

### Statistics Analysis

1. Click **Statistics** tab
2. View:
   - **Overview** - Total rows, column statistics
   - **Top Domains** - Most visited domains
   - **Top URLs** - Most visited URLs

**Features:**
- **Copy Data** - Select rows and press Ctrl+C
- **Query URLs** - Right-click domain/URL → "Query with VirusTotal"

### URL Decoding

**For Encoded URLs:**
1. Right-click on encoded URL
2. Select **"Decode URL"**
3. View decoded URL in dialog
4. Click **"Copy Decoded URL"** to copy

### Viewing Logs

**For Debugging:**
1. Go to **Help → View Logs**
2. See all debug output
3. Click **Refresh** to update
4. Click **Copy to Clipboard** to save

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+O** | Open/Load database |
| **Ctrl+E** | Export data |
| **Ctrl+C** | Copy selected cells |
| **Ctrl+F** | Focus search box |
| **Ctrl+Q** | Quit application |
| **F5** | Refresh current view |

---

## Tips & Tricks

### Performance Optimization

**For Large Databases:**
1. Use pagination (100-500 rows per page)
2. Apply filters to reduce dataset
3. Hide unused columns
4. Export filtered data instead of full database

### Forensic Best Practices

**1. Create Working Copy:**
- Always work on a copy of evidence
- Never load original evidence file
- Calculate hash of original first

**2. Document Everything:**
- Export results with timestamps
- Include file hash in reports
- Note timezone used for analysis
- Save VirusTotal results

**3. Chain of Custody:**
- Record source file path
- Note file hash (SHA256)
- Document analysis date/time
- Include timezone in reports

### VirusTotal Rate Limits

**Free Tier Limits:**
- 4 requests per minute
- 500 requests per day

**Tips:**
- Space out bulk queries
- Save results immediately
- Export threat intelligence to CSV

---

## Support

- **Documentation**: See README.md for features
- **Security**: See SECURITY.md for security policy
- **Issues**: Report bugs on GitHub

---

**Happy Hunting!** 🔍
