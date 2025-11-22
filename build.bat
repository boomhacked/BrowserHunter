@echo off
REM Build script for BrowserHunter Windows executable

echo ========================================
echo Building BrowserHunter
echo ========================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or later from https://www.python.org/
    pause
    exit /b 1
)

echo.
echo Step 1: Setting up virtual environment
echo ========================================

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo Step 2: Installing dependencies
echo ========================================

REM Upgrade pip first
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install/upgrade dependencies
echo Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo Installing PyInstaller...
pip install pyinstaller>=6.0
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo Step 3: Verifying PyQt6 installation
echo ========================================
python -c "import PyQt6; print(f'PyQt6 version: {PyQt6.QtCore.PYQT_VERSION_STR}')"
if errorlevel 1 (
    echo ERROR: PyQt6 is not properly installed
    echo Attempting to reinstall PyQt6...
    pip uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip
    pip install PyQt6==6.6.1 PyQt6-Qt6==6.6.1 "PyQt6-sip<14,>=13.6"
    if errorlevel 1 (
        echo ERROR: Failed to install PyQt6
        pause
        exit /b 1
    )
)

echo.
echo Step 4: Cleaning previous builds
echo ========================================
if exist "build\" (
    echo Removing build directory...
    rmdir /s /q build
)
if exist "dist\" (
    echo Removing dist directory...
    rmdir /s /q dist
)

echo.
echo Step 5: Building executable
echo ========================================
echo Using spec file: build_windows.spec
echo.
pyinstaller --clean --noconfirm build_windows.spec

echo.
echo Step 6: Verifying build
echo ========================================
if exist "dist\BrowserHunter\BrowserHunter.exe" (
    echo.
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo.
    echo Executable location: dist\BrowserHunter\BrowserHunter.exe
    echo.
    echo To run the application:
    echo   dist\BrowserHunter\BrowserHunter.exe
    echo.
    echo Or double-click the .exe file in Windows Explorer
    echo.
) else (
    echo.
    echo ========================================
    echo Build FAILED!
    echo ========================================
    echo.
    echo The .exe file was not created. Possible issues:
    echo   1. PyQt6 is not properly installed
    echo   2. PyInstaller version is too old (need 6.0+)
    echo   3. Build errors occurred (check output above)
    echo.
    echo Try the alternative build method:
    echo   build_alternative.bat
    echo.
    echo Or use the simple spec file:
    echo   pyinstaller build_windows_simple.spec
    echo.
)

pause
