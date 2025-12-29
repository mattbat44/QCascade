"""
@brief Sediment parameters tab component for D-CASCADE parameters dock
@author D-CASCADE Team
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QFormLayout, QDoubleSpinBox, QSpinBox, 
    QLineEdit, QHBoxLayout, QLabel
)


class SedimentTab(QWidget):
    """Sediment parameters tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QFormLayout(self)
        
        # Range (Phi)
        range_layout = QHBoxLayout()
        self.min_phi = QDoubleSpinBox()
        self.min_phi.setRange(-20, 20)
        self.min_phi.setValue(-8)
        self.max_phi = QDoubleSpinBox()
        self.max_phi.setRange(-20, 20)
        self.max_phi.setValue(5)
        range_layout.addWidget(QLabel("Min:"))
        range_layout.addWidget(self.min_phi)
        range_layout.addWidget(QLabel("Max:"))
        range_layout.addWidget(self.max_phi)
        
        range_tooltip = "Sediment size range in Krumbein phi scale.\nCoarse (negative) to Fine (positive).\nExample: -8 to 5."
        self.min_phi.setToolTip(range_tooltip)
        self.max_phi.setToolTip(range_tooltip)
        layout.addRow("Phi Range:", range_layout)
        
        # N Classes
        self.n_classes = QSpinBox()
        self.n_classes.setRange(1, 100)
        self.n_classes.setValue(6)
        self.n_classes.setToolTip("Number of sediment classes to divide the range into.")
        layout.addRow("Number of Classes:", self.n_classes)
        
        # Deposit Layer Thickness
        self.dep_layer = QDoubleSpinBox()
        self.dep_layer.setRange(0, 1000000)
        self.dep_layer.setValue(100000)
        self.dep_layer.setToolTip("Initial deposit layer thickness in meters.\nWARNING: Overwrites the deposit column in the reach data.")
        layout.addRow("Deposit Layer (m):", self.dep_layer)
        
        # Active Layer Depth
        self.act_layer = QLineEdit("0.3")  # Can be string "2D90" or float
        self.act_layer.setToolTip("Depth of the active layer in meters (e.g., 0.3) or '2D90'.")
        layout.addRow("Active Layer Depth:", self.act_layer)
