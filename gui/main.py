import sys
import os

# Add the project root to sys.path to allow imports from src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.windows.main_window import MainWindow

# Import stylesheet
try:
    from gui.styles.theme import DCASCADE_STYLESHEET
except ImportError:
    DCASCADE_STYLESHEET = ""

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("D-CASCADE")
    app.setOrganizationName("D-CASCADE Team")
    
    # Apply custom stylesheet
    if DCASCADE_STYLESHEET:
        app.setStyleSheet(DCASCADE_STYLESHEET)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
