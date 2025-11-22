# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Browser Hunter
Requires: Python 3.11+ or 3.12, PyInstaller 6.0+, PyQt6
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# Collect PyQt6 data files and binaries
pyqt6_datas = collect_data_files('PyQt6')
pyqt6_binaries = collect_dynamic_libs('PyQt6')
pyqt6_modules = collect_submodules('PyQt6')

# Hidden imports
hiddenimports = [
    # PyQt6
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    'PyQt6.QtPrintSupport',

    # Data processing
    'pandas',
    'numpy',

    # Timezone
    'pytz',
    'dateutil',

    # Export
    'openpyxl',
    'xlsxwriter',

    # Visualization
    'matplotlib',
    'plotly',

    # Standard library
    'sqlite3',
    'json',
    'csv',
    'datetime',
    'pathlib',
    'html',
    'logging',
]

# Add all PyQt6 submodules
hiddenimports.extend(pyqt6_modules)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=pyqt6_binaries,
    datas=pyqt6_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BrowserHunter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BrowserHunter',
)
