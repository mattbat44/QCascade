"""
@brief Connectivity/heatmap tab component for D-CASCADE results viewer
@author Matt Adams
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QPushButton
)


class ConnectivityTab(QWidget):
    """Connectivity/heatmap tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        var_layout = QFormLayout()
        
        self.conn_variable_combo = QComboBox()
        self.conn_variable_combo.addItems([
            'Volume out [m^3]',
            'Volume in [m^3]',
            'Transport capacity [m^3]',
            'Sediment budget [m^3]'
        ])
        var_layout.addRow("Variable:", self.conn_variable_combo)
        
        layout.addLayout(var_layout)
        
        self.plot_btn = QPushButton("Generate Heatmap")
        layout.addWidget(self.plot_btn)
        
        layout.addStretch()
