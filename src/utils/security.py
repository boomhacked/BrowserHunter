"""
Security utilities for input validation and sanitization
"""
import os
import html
from pathlib import Path
from typing import Optional


def validate_export_path(file_path: str, allowed_extensions: tuple = ('.csv', '.json', '.xlsx', '.html')) -> bool:
    """
    Validate export file path for security

    Args:
        file_path: Path to validate
        allowed_extensions: Tuple of allowed file extensions

    Returns:
        True if path is safe, False otherwise
    """
    try:
        # Convert to Path object
        path = Path(file_path)

        # Check for directory traversal attempts
        resolved_path = path.resolve()

        # Ensure the path doesn't contain dangerous patterns
        path_str = str(path)
        if '..' in path_str or path_str.startswith('/') or ':' in path_str[1:3]:  # Windows drive letter ok
            # Additional checks for Windows absolute paths
            if not (len(path_str) >= 3 and path_str[1] == ':' and path_str[2] in ['\\', '/']):
                return False

        # Validate file extension
        if allowed_extensions:
            if not any(path_str.lower().endswith(ext) for ext in allowed_extensions):
                return False

        # Check parent directory exists (if specified)
        parent = path.parent
        if parent != Path('.') and not parent.exists():
            return False

        # Path is safe
        return True

    except Exception:
        return False


def sanitize_path(file_path: str) -> str:
    """
    Sanitize file path by resolving and normalizing

    Args:
        file_path: Path to sanitize

    Returns:
        Sanitized absolute path
    """
    try:
        path = Path(file_path)
        # Resolve to absolute path and normalize
        resolved = path.resolve()
        return str(resolved)
    except Exception:
        return file_path


def escape_html(text: Optional[str]) -> str:
    """
    Escape HTML to prevent XSS

    Args:
        text: Text to escape

    Returns:
        HTML-escaped text
    """
    if text is None:
        return ""

    # Use html.escape for proper escaping
    return html.escape(str(text), quote=True)


def validate_database_path(db_path: str) -> bool:
    """
    Validate database file path for security

    Args:
        db_path: Path to database file

    Returns:
        True if path is safe, False otherwise
    """
    try:
        path = Path(db_path)

        # Must exist
        if not path.exists():
            return False

        # Must be a regular file (not directory, symlink, device, etc.)
        if not path.is_file():
            return False

        # Check resolved path doesn't lead to dangerous locations
        resolved = path.resolve()

        # Don't allow /etc, /sys, /proc, etc. on Unix
        if os.name != 'nt':  # Unix-like systems
            dangerous_prefixes = ['/etc', '/sys', '/proc', '/dev', '/boot']
            resolved_str = str(resolved)
            if any(resolved_str.startswith(prefix) for prefix in dangerous_prefixes):
                return False

        # Check file size is reasonable (< 10GB for database)
        MAX_DB_SIZE = 10 * 1024 * 1024 * 1024  # 10GB
        if path.stat().st_size > MAX_DB_SIZE:
            return False

        # Validate file extension
        allowed_extensions = ('.db', '.sqlite', '.sqlite3')
        if not any(str(path).lower().endswith(ext) for ext in allowed_extensions):
            return False

        return True

    except Exception:
        return False


def validate_storage_directory(storage_path: str, base_dir: Optional[str] = None) -> bool:
    """
    Validate storage directory path

    Args:
        storage_path: Path to validate
        base_dir: Base directory that storage_path must be under (optional)

    Returns:
        True if path is safe, False otherwise
    """
    try:
        path = Path(storage_path).resolve()

        # If base_dir specified, ensure path is under it
        if base_dir:
            base = Path(base_dir).resolve()
            try:
                path.relative_to(base)
            except ValueError:
                # Path is not relative to base_dir
                return False

        # Don't allow system directories
        if os.name != 'nt':  # Unix-like
            dangerous_prefixes = ['/etc', '/sys', '/proc', '/dev', '/boot', '/bin', '/sbin']
            path_str = str(path)
            if any(path_str.startswith(prefix) for prefix in dangerous_prefixes):
                return False

        return True

    except Exception:
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing dangerous characters

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove path separators and dangerous characters
    dangerous_chars = ['/', '\\', '..', '\0', '\n', '\r', '\t']
    sanitized = filename

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')

    # Limit length
    MAX_FILENAME_LENGTH = 255
    if len(sanitized) > MAX_FILENAME_LENGTH:
        # Keep extension if present
        if '.' in sanitized:
            name, ext = sanitized.rsplit('.', 1)
            sanitized = name[:MAX_FILENAME_LENGTH - len(ext) - 1] + '.' + ext
        else:
            sanitized = sanitized[:MAX_FILENAME_LENGTH]

    return sanitized
