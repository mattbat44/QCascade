"""
@brief Time parameters tab component for D-CASCADE parameters dock
@author D-CASCADE Team
"""

from qgis.PyQt.QtWidgets import QWidget, QFormLayout, QDoubleSpinBox, QSpinBox


class TimeTab(QWidget):
    """Time parameters tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QFormLayout(self)
        
        self.timescale = QSpinBox()
        self.timescale.setRange(1, 1000000)
        self.timescale.setValue(20)
        self.timescale.setToolTip("Total number of time steps to simulate.")
        layout.addRow("Time Steps:", self.timescale)
        
        self.ts_length = QDoubleSpinBox()
        self.ts_length.setRange(1, 31536000)  # 1 year max?
        self.ts_length.setValue(86400)
        self.ts_length.setToolTip("Length of each time step in seconds.\n86400 = 1 day\n3600 = 1 hour")
        layout.addRow("Step Length (s):", self.ts_length)
