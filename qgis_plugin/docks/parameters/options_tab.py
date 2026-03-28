"""
@brief Options tab component for D-CASCADE parameters dock
@author Matt Adams
"""

from qgis.PyQt.QtWidgets import QWidget, QFormLayout, QComboBox, QDoubleSpinBox, QCheckBox


class OptionsTab(QWidget):
    """Options tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QFormLayout(self)
        
        self.save_dep = QComboBox()
        self.save_dep.addItems(["never", "yearly", "always"])
        self.save_dep.setToolTip("When to save the deposit layer matrix to disk.")
        layout.addRow("Save Deposit:", self.save_dep)
        
        self.round_param = QDoubleSpinBox()
        self.round_param.setValue(0)
        self.round_param.setToolTip("Minimum volume for mobilization (decimal digit).\n0 means >= 1m3; 1 means >= 10m3.")
        layout.addRow("Round Parameter:", self.round_param)
        
        self.force_pass = QCheckBox("Force Pass External Inputs")
        self.force_pass.setToolTip("If checked, forces external sediment input to entirely pass to the next reach.")
        layout.addRow("", self.force_pass)
