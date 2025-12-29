"""
@brief Statistics summary tab component for D-CASCADE results viewer
@author D-CASCADE Team
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel
)


class StatsTab(QWidget):
    """Statistics summary tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        info_label = QLabel("Summary statistics for loaded results:")
        layout.addWidget(info_label)
        
        self.stats_label = QLabel("No statistics available.")
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)
        
        self.refresh_btn = QPushButton("Refresh Statistics")
        layout.addWidget(self.refresh_btn)
        
        layout.addStretch()
