import sys
from PyQt5.QtWidgets import QApplication

# Import local modules from the project structure
from gui.main_window import MainWindow

# --- Main Application Entry Point ---

def main_gui_function():
    """GUI entry-point used by setup.py's gui_scripts."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main_gui_function()