"""
@brief Time series visualization tab component for D-CASCADE results viewer
@author D-CASCADE Team
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QCheckBox, QPushButton
)


class TimeSeriesTab(QWidget):
    """Time series visualization tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Variable selection
        var_layout = QFormLayout()
        
        self.ts_variable_combo = QComboBox()
        self.ts_variable_combo.addItems([
            'Volume out [m^3]',
            'Volume in [m^3]',
            'Transport capacity [m^3]',
            'Sediment budget [m^3]',
            'D50 active layer [m]',
            'D50 volume out [m]',
            'Elevation (Upstream) [m]',
            'Elevation (Downstream) [m]',
            'Elevation Change (Upstream) [m]'
        ])
        var_layout.addRow("Variable:", self.ts_variable_combo)
        
        # Reach selection
        self.ts_reach_combo = QComboBox()
        self.ts_reach_combo.setEnabled(False)
        var_layout.addRow("Reach:", self.ts_reach_combo)
        
        # Multi-reach checkbox
        self.ts_multi_check = QCheckBox("Show all reaches")
        var_layout.addRow("", self.ts_multi_check)

        # Grain size breakdown checkbox
        self.ts_grain_size_check = QCheckBox("Breakdown by Grain Size")
        var_layout.addRow("", self.ts_grain_size_check)
        
        layout.addLayout(var_layout)
        
        # Plot button
        self.plot_btn = QPushButton("Generate Plot")
        layout.addWidget(self.plot_btn)
        
        layout.addStretch()
