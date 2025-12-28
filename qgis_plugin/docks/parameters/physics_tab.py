"""
@brief Physics parameters tab component for D-CASCADE parameters dock
@author D-CASCADE Team
"""

from qgis.PyQt.QtWidgets import QWidget, QFormLayout, QComboBox, QCheckBox


class PhysicsTab(QWidget):
    """Physics parameters tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QFormLayout(self)
        
        # Transport Capacity Formula
        self.tr_cap = QComboBox()
        self.tr_cap.addItems([
            "1: Parker-Klingeman", "2: Wilcock-Crowe", "3: Engelund-Hansen", 
            "4: Yang", "5: Wong-Parker", "6: Ackers-White", 
            "7: Rickenmann", "8: WC-Mueller"
        ])
        self.tr_cap.setCurrentIndex(1)  # Default to 2: Wilcock-Crowe
        self.tr_cap.setToolTip(
            "Formula to calculate sediment transport capacity.\n"
            "2: Wilcock and Crowe (2003)\n"
            "3: Engelund and Hansen (1967)\n"
            "6: Ackers and White (1973)"
        )
        layout.addRow("Transport Capacity:", self.tr_cap)
        
        # Transport Partitioning
        self.tr_part = QComboBox()
        self.tr_part.addItems([
            "1: Direct", "2: BMF", "3: Molinas", "4: Shear stress correction"
        ])
        self.tr_part.setCurrentIndex(3)  # Default 4
        self.tr_part.setToolTip(
            "Method for partitioning transport capacity among grain sizes.\n"
            "1: Direct calculation summing fractional load\n"
            "2: BMF: Bed Material Fraction weighting\n"
            "3: Molinas rates: weighting on total load\n"
            "4: Shear stress correction (only for partitioned formulas like W&C)"
        )
        layout.addRow("Partitioning:", self.tr_part)
        
        # Flow Depth
        self.flow_depth = QComboBox()
        self.flow_depth.addItems(["1: Manning", "2: Ferguson"])
        self.flow_depth.setToolTip("Formula for flow depth calculation.\n1: Manning (default)\n2: Ferguson (2007)")
        layout.addRow("Flow Depth:", self.flow_depth)
        
        # Velocity Formula
        self.vel_formula = QComboBox()
        self.vel_formula.addItems(["1: Individual Cascades", "2: Whole Active Layer"])
        self.vel_formula.setCurrentIndex(1)
        self.vel_formula.setToolTip(
            "Method for calculating velocity.\n"
            "1: Computed on each cascade individually\n"
            "2: Computed on the whole active layer (default)"
        )
        layout.addRow("Velocity Formula:", self.vel_formula)
        
        # Slope Reduction
        self.slope_red = QComboBox()
        self.slope_red.addItems(["1: No reduction", "2: Formula 2", "3: Formula 3", "4: Formula 4"])
        self.slope_red.setToolTip("Slope reduction factor for mountain stream roughness.\n1: No reduction (default)")
        layout.addRow("Slope Reduction:", self.slope_red)
        
        # Width Calculation
        self.width_calc = QComboBox()
        self.width_calc.addItems(["1: Static", "2: Dynamic (Lugo)"])
        self.width_calc.setToolTip("Method for channel width variation.\n1: Static (constant)\n2: Dynamic (Lugo)")
        layout.addRow("Width Calculation:", self.width_calc)
        
        # Update Slope
        self.update_slope = QCheckBox("Update Slope")
        self.update_slope.setToolTip("If checked, channel slope changes dynamically based on sediment deposition/erosion.")
        layout.addRow("Update Slope:", self.update_slope)
