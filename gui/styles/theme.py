"""
@brief Stylesheet and theme settings for D-CASCADE GUI
@author D-CASCADE GUI Team
"""

# Modern stylesheet inspired by Material Design
DCASCADE_STYLESHEET = """
QMainWindow {
    background-color: #f5f5f5;
}

QDockWidget::title {
    text-align: left;
    background-color: #2c3e50;
    color: white;
    padding: 5px;
    font-size: 11pt;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 10pt;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #21618c;
}

QPushButton:disabled {
    background-color: #bdc3c7;
    color: #7f8c8d;
}

QToolBar {
    background-color: #34495e;
    border: none;
    spacing: 3px;
    padding: 3px;
}

QLabel {
    color: #2c3e50;
    font-size: 10pt;
}

QLineEdit, QSpinBox, QDoubleSpinBox {
    border: 1px solid #bdc3c7;
    border-radius: 3px;
    padding: 4px;
    background-color: white;
    font-size: 10pt;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #3498db;
}

QComboBox {
    border: 1px solid #bdc3c7;
    border-radius: 3px;
    padding: 4px;
    background-color: white;
    font-size: 10pt;
}

QTableWidget {
    background-color: white;
    alternate-background-color: #ecf0f1;
    gridline-color: #bdc3c7;
    border: 1px solid #bdc3c7;
}

QTableWidget::item:selected {
    background-color: #3498db;
    color: white;
}

QHeaderView::section {
    background-color: #34495e;
    color: white;
    padding: 5px;
    border: none;
    font-weight: bold;
}

QTextEdit {
    border: 1px solid #bdc3c7;
    border-radius: 3px;
    background-color: white;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 9pt;
}

QCheckBox {
    spacing: 5px;
    font-size: 10pt;
}

QSlider::groove:horizontal {
    border: 1px solid #bdc3c7;
    height: 6px;
    background: #ecf0f1;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #3498db;
    border: 1px solid #2980b9;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QTabWidget::pane {
    border: 1px solid #bdc3c7;
    background-color: white;
}

QTabBar::tab {
    background-color: #ecf0f1;
    color: #2c3e50;
    padding: 8px 12px;
    border: 1px solid #bdc3c7;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: white;
    color: #3498db;
    font-weight: bold;
}

QTabBar::tab:hover {
    background-color: #d5dbdb;
}
"""

# Color palette
COLORS = {
    'primary': '#3498db',
    'secondary': '#2c3e50',
    'success': '#27ae60',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'info': '#16a085',
}
