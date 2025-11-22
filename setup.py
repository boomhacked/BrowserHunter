from setuptools import setup, find_packages

setup(
    name="BrowserHunter",
    version="1.0",
    description="Professional Browser Forensic Analysis Tool",
    author="Forensic Tools Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "PyQt6>=6.7.0",
        "pandas>=2.2.3",
        "numpy>=1.26.4",
        "pytz>=2024.1",
        "python-dateutil>=2.9.0",
        "openpyxl>=3.1.5",
        "xlsxwriter>=3.2.0",
        "matplotlib>=3.9.0",
        "plotly>=5.24.0",
        "tqdm>=4.66.5",
        "requests>=2.32.3",
    ],
    entry_points={
        "console_scripts": [
            "browserhunter=main:main",
        ],
    },
)
