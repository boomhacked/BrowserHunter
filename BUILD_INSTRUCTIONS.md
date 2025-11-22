# Browser Hunter - Build Instructions

Instructions for building Browser Hunter from source into a standalone Windows executable.

---

## Prerequisites

Before building, ensure you have:

- **Python 3.11.x or 3.12.x** (required)
  - Download from: https://www.python.org/downloads/
  - During installation, check "Add Python to PATH"
- **Windows 10 or Windows 11**
- **Internet connection** (for downloading dependencies)
- **5GB free disk space** (for build process)

---

## Quick Build

The easiest way to build Browser Hunter:

```bash
# Navigate to project folder
cd BrowserHunter-Clean

# Run the build script
build.bat
```

The script will automatically:
1. Check Python installation
2. Create virtual environment
3. Install all dependencies
4. Verify PyQt6 installation
5. Clean previous builds
6. Build the executable with PyInstaller
7. Verify the build succeeded

**Output Location:** `dist\BrowserHunter\BrowserHunter.exe`

---

## Build Process Details

### Step 1: Environment Setup

The build script creates a virtual environment to isolate dependencies:

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 2: Install Dependencies

All required packages are installed from `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller>=6.0
```

**Key Dependencies:**
- PyQt6 (GUI framework)
- pandas (data processing)
- requests (API calls)
- openpyxl (Excel export)
- matplotlib (visualization)
- And more...

### Step 3: PyInstaller Build

The `build_windows.spec` file defines the build configuration:

- **Entry point**: `main.py`
- **Output name**: `BrowserHunter.exe`
- **Mode**: Windowed (no console)
- **Compression**: UPX enabled
- **Hidden imports**: All dependencies explicitly listed

```bash
pyinstaller --clean --noconfirm build_windows.spec
```

### Step 4: Output Structure

After successful build:

```
dist/
└── BrowserHunter/
    ├── BrowserHunter.exe      # Main executable
    ├── *.dll                  # Required libraries
    ├── PyQt6/                 # Qt framework files
    └── ...                    # Other dependencies
```

---

## Manual Build (Advanced)

If the automated script doesn't work, build manually:

### 1. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Install PyInstaller

```bash
pip install pyinstaller>=6.0
```

### 4. Verify PyQt6

```bash
python -c "import PyQt6; print(PyQt6.QtCore.PYQT_VERSION_STR)"
```

Should output version number (e.g., "6.7.0").

### 5. Clean Previous Builds

```bash
rmdir /s /q build
rmdir /s /q dist
```

### 6. Run PyInstaller

```bash
pyinstaller --clean --noconfirm build_windows.spec
```

### 7. Test the Executable

```bash
dist\BrowserHunter\BrowserHunter.exe
```

---

## Build Configuration

### build_windows.spec

This file controls the PyInstaller build process:

**Key Settings:**
- `name='BrowserHunter'` - Executable filename
- `console=False` - GUI application (no console window)
- `upx=True` - Enable UPX compression
- `hiddenimports=[...]` - Explicitly list all dependencies

**Collected Data:**
- PyQt6 binaries and data files
- All Python packages from requirements.txt
- Hidden imports that PyInstaller might miss

---

## Troubleshooting

### Python Not Found

**Error:** "Python is not installed or not in PATH"

**Solution:**
1. Install Python 3.11 or 3.12
2. During installation, check "Add Python to PATH"
3. Restart command prompt after installation

### PyQt6 Installation Failed

**Error:** "Failed to install PyQt6"

**Solution:**
```bash
pip uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip
pip install PyQt6==6.7.0 PyQt6-Qt6==6.7.0 "PyQt6-sip<14,>=13.6"
```

### Build Failed - Missing Modules

**Error:** "ModuleNotFoundError" during build

**Solution:**
1. Check `requirements.txt` is complete
2. Verify all dependencies installed:
   ```bash
   pip list
   ```
3. Add missing modules to `hiddenimports` in `build_windows.spec`

### Executable Won't Run

**Error:** Executable crashes immediately

**Solution:**
1. Run from command line to see error:
   ```bash
   dist\BrowserHunter\BrowserHunter.exe
   ```
2. Check for missing DLLs
3. Verify PyQt6 installation
4. Rebuild with `--clean` flag

### Large Executable Size

**Note:** Executable will be 200-400MB due to PyQt6 and dependencies.

**To Reduce Size:**
- UPX compression (already enabled)
- Exclude unused packages (advanced)
- Use `--onefile` mode (slower startup)

---

## Distribution

### Creating Release Package

1. **Build the executable**:
   ```bash
   build.bat
   ```

2. **Test the executable**:
   ```bash
   dist\BrowserHunter\BrowserHunter.exe
   ```

3. **Create ZIP archive**:
   - Compress the entire `dist\BrowserHunter\` folder
   - Name: `BrowserHunter-v1.0-Windows.zip`

4. **Include files**:
   - Executable and all DLLs
   - README.md (optional)
   - LICENSE (optional)

### GitHub Release

1. Tag the release:
   ```bash
   git tag v1.0
   git push origin v1.0
   ```

2. Create GitHub release:
   - Go to repository → Releases → New Release
   - Select tag: v1.0
   - Upload ZIP file as asset
   - Add release notes

---

## Build Environment

### Recommended Setup

- **OS**: Windows 11 (Windows 10 also supported)
- **Python**: 3.11.x or 3.12.x (latest patch version)
- **RAM**: 8GB minimum
- **Disk**: 5GB free space
- **Internet**: Required for downloading dependencies

### Tested Configurations

- ✅ Windows 11 + Python 3.11.8
- ✅ Windows 11 + Python 3.12.2
- ✅ Windows 10 + Python 3.11.x

---

## Performance Notes

### Build Time

- **First build**: 5-15 minutes (downloading dependencies)
- **Subsequent builds**: 2-5 minutes (using cache)

### Executable Size

- **Typical size**: 250-350 MB
- **Includes**: Python runtime, PyQt6, all dependencies
- **Standalone**: No installation required

---

## Security Considerations

### Code Signing

For production releases, consider:
- Windows code signing certificate
- Authenticode signature
- Prevents "Unknown Publisher" warnings

### Antivirus False Positives

PyInstaller executables sometimes trigger antivirus:
- **Solution**: Submit to antivirus vendors
- **Or**: Distribute as Python source

---

## Support

For build issues:
- Check error messages carefully
- Verify Python version (3.11 or 3.12)
- Ensure all dependencies installed
- Try manual build process

---

**Happy Building!** 🔨
