"""
Browser Hunter - Main Entry Point
Professional Browser Forensic Analysis Tool
"""
import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.gui.main_window import MainWindow


def exception_hook(exc_type, exc_value, exc_traceback):
    """Global exception handler to catch uncaught exceptions"""
    # Format the exception
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    print("=" * 80)
    print("UNHANDLED EXCEPTION:")
    print("=" * 80)
    print(error_msg)
    print("=" * 80)

    # Show error dialog
    try:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Unexpected Error")
        msg.setText("An unexpected error occurred:")
        msg.setDetailedText(error_msg)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    except:
        pass

    # Call the default handler
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def main():
    """Main application entry point"""
    # Install global exception handler
    sys.excepthook = exception_hook

    try:
        app = QApplication(sys.argv)

        # Set application metadata
        app.setApplicationName("Browser Hunter")
        app.setApplicationDisplayName("Browser Hunter")
        app.setOrganizationName("Forensic Tools")
        app.setApplicationVersion("1.0")

        # Create and show main window
        window = MainWindow()
        window.show()

        sys.exit(app.exec())

    except Exception as e:
        error_msg = f"Failed to start application:\n\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)

        try:
            QMessageBox.critical(
                None,
                "Application Error",
                error_msg
            )
        except:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
