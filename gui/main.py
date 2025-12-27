import sys
import os

# Add the project root to sys.path to allow imports from src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from PyQt6.QtWidgets import QApplication
from gui.windows.main_window import MainWindow
# from qt_material import apply_stylesheet

def main():
    app = QApplication(sys.argv)
    
    # Optional: Apply theme
    # try:
    #     from qt_material import apply_stylesheet
    #     apply_stylesheet(app, theme='dark_teal.xml')
    # except ImportError:
    #     pass
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
