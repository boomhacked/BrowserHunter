# Security Policy

## Security Best Practices

### For Users

1. **File Integrity**
   - Always verify SHA256 hashes of source files
   - Hashes are displayed in the status bar and included in exports
   - Record hashes in case documentation

2. **Evidence Handling**
   - Work on copies, never original evidence
   - Files are automatically copied to temp directory (read-only mode)
   - Original files are never modified

3. **Network Security**
   - Application is able to run completely offline (threat intelligence naturally won't work)
   - No network connections initiated
   - Safe for air-gapped environments

4. **Export Security**
   - Use trusted export locations only
   - Verify export file paths before exporting
   - HTML exports escape all user data

## Dependencies Security

### Current Dependencies
All dependencies are from trusted sources (PyPI):
- PyQt6: Official Qt bindings
- pandas: NumFOCUS project
- numpy: NumFOCUS project
- pytz: Standard timezone library
- openpyxl: Trusted Excel library

### Dependency Management
- Regular updates for security patches
- Vulnerability scanning with `pip-audit`
- Pinned versions in `requirements.txt`
