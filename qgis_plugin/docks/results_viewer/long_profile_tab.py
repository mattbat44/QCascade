"""
@brief Long profile visualization tab component for D-CASCADE results viewer
@author D-CASCADE Team
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QSlider
)
from qgis.PyQt.QtCore import Qt


class LongProfileTab(QWidget):
    """Long profile visualization tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        info_label = QLabel("Select a sequence of connected reaches in the map to view the long profile.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.lp_update_btn = QPushButton("Update Profile from Selection")
        controls_layout.addWidget(self.lp_update_btn)
        
        layout.addLayout(controls_layout)
        
        # Time slider for long profile animation
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Time Step:"))
        self.lp_time_slider = QSlider(Qt.Horizontal)
        self.lp_time_slider.setMinimum(0)
        self.lp_time_slider.setMaximum(100)
        self.lp_time_slider.setValue(0)
        self.lp_time_slider.setEnabled(False)
        slider_layout.addWidget(self.lp_time_slider, 1)
        self.lp_time_label = QLabel("0 / 0")
        slider_layout.addWidget(self.lp_time_label)
        layout.addLayout(slider_layout)
        
        layout.addStretch()
