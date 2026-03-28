"""
@brief Spatial analysis tab component for D-CASCADE results viewer
@author Matt Adams
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, 
    QSpinBox, QCheckBox, QPushButton
)


class SpatialTab(QWidget):
    """Spatial analysis tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Variable selection
        var_layout = QFormLayout()
        
        self.spatial_variable_combo = QComboBox()
        self.spatial_variable_combo.addItems([
            'Volume out [m^3]',
            'Volume in [m^3]',
            'Transport capacity [m^3]',
            'Sediment budget [m^3]',
            'D50 active layer [m]',
            'D50 volume out [m]'
        ])
        var_layout.addRow("Variable:", self.spatial_variable_combo)
        
        # Aggregation method
        self.spatial_agg_combo = QComboBox()
        self.spatial_agg_combo.addItems(['Mean', 'Median', 'Sum', 'Max', 'Min'])
        var_layout.addRow("Aggregation:", self.spatial_agg_combo)
        
        # Year/time range
        self.spatial_year_spin = QSpinBox()
        self.spatial_year_spin.setRange(0, 1000)
        self.spatial_year_spin.setValue(0)
        self.spatial_year_spin.setSuffix(" (0 = all)")
        var_layout.addRow("Year:", self.spatial_year_spin)
        
        # Yearly profiles checkbox
        self.spatial_yearly_check = QCheckBox("Show Yearly Profiles")
        var_layout.addRow("", self.spatial_yearly_check)

        layout.addLayout(var_layout)
        
        # Plot button
        self.plot_btn = QPushButton("Generate Spatial Plot")
        layout.addWidget(self.plot_btn)
        
        layout.addStretch()
