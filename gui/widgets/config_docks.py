from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QFormLayout, QLineEdit, QPushButton, 
    QComboBox, QSpinBox, QDoubleSpinBox, QFileDialog, QCheckBox, QHBoxLayout, QLabel
)
from PyQt6.QtCore import pyqtSignal

class PathsDock(QDockWidget):
    shapefile_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__("Input Files", parent)
        self.container = QWidget()
        self.layout = QFormLayout(self.container)
        
        # River Network Shapefile
        self.shp_path = QLineEdit()
        self.shp_btn = QPushButton("Browse...")
        self.shp_btn.clicked.connect(self.browse_shp)
        shp_layout = QHBoxLayout()
        shp_layout.addWidget(self.shp_path)
        shp_layout.addWidget(self.shp_btn)
        self.layout.addRow("River Network (.shp):", shp_layout)
        
        # Discharge CSV
        self.csv_path = QLineEdit()
        self.csv_btn = QPushButton("Browse...")
        self.csv_btn.clicked.connect(self.browse_csv)
        csv_layout = QHBoxLayout()
        csv_layout.addWidget(self.csv_path)
        csv_layout.addWidget(self.csv_btn)
        self.layout.addRow("Discharge (.csv):", csv_layout)
        
        # Output Name
        self.output_name = QLineEdit("simulation_output")
        self.layout.addRow("Output Name:", self.output_name)
        
        self.setWidget(self.container)

    def browse_shp(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select River Network Shapefile", "", "Shapefiles (*.shp)")
        if path:
            self.shp_path.setText(path)
            self.shapefile_selected.emit(path)

    def browse_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Discharge CSV", "", "CSV Files (*.csv)")
        if path:
            self.csv_path.setText(path)

class PhysicsDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Physics Parameters", parent)
        self.container = QWidget()
        self.layout = QFormLayout(self.container)
        
        # Transport Capacity Formula
        self.tr_cap = QComboBox()
        self.tr_cap.addItems([
            "1: Parker-Klingeman", "2: Wilcock-Crowe", "3: Engelund-Hansen", 
            "4: Yang", "5: Wong-Parker", "6: Ackers-White", 
            "7: Rickenmann", "8: WC-Mueller"
        ])
        self.tr_cap.setCurrentIndex(1) # Default to 2: Wilcock-Crowe (index 1)
        self.layout.addRow("Transport Capacity:", self.tr_cap)
        
        # Transport Partitioning
        self.tr_part = QComboBox()
        self.tr_part.addItems([
            "1: Direct", "2: BMF", "3: Molinas", "4: Shear stress correction"
        ])
        self.tr_part.setCurrentIndex(3) # Default 4
        self.layout.addRow("Partitioning:", self.tr_part)
        
        # Flow Depth
        self.flow_depth = QComboBox()
        self.flow_depth.addItems(["1: Manning", "2: Ferguson"])
        self.layout.addRow("Flow Depth:", self.flow_depth)
        
        # Velocity Formula
        self.vel_formula = QComboBox()
        self.vel_formula.addItems(["1: Method 1", "2: Method 2"]) # Need better names if available
        self.vel_formula.setCurrentIndex(1)
        self.layout.addRow("Velocity Formula:", self.vel_formula)
        
        # Slope Reduction
        self.slope_red = QComboBox()
        self.slope_red.addItems(["1: No reduction", "2: Formula 2", "3: Formula 3", "4: Formula 4"])
        self.layout.addRow("Slope Reduction:", self.slope_red)
        
        # Width Calculation
        self.width_calc = QComboBox()
        self.width_calc.addItems(["1: Static", "2: Dynamic (Lugo)"])
        self.layout.addRow("Width Calculation:", self.width_calc)
        
        # Update Slope
        self.update_slope = QCheckBox("Update Slope")
        self.layout.addRow("Update Slope:", self.update_slope)
        
        self.setWidget(self.container)

class SedimentDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Sediment Parameters", parent)
        self.container = QWidget()
        self.layout = QFormLayout(self.container)
        
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
        self.layout.addRow("Phi Range:", range_layout)
        
        # N Classes
        self.n_classes = QSpinBox()
        self.n_classes.setRange(1, 100)
        self.n_classes.setValue(6)
        self.layout.addRow("Number of Classes:", self.n_classes)
        
        # Deposit Layer Thickness
        self.dep_layer = QDoubleSpinBox()
        self.dep_layer.setRange(0, 1000000)
        self.dep_layer.setValue(100000)
        self.layout.addRow("Deposit Layer (m):", self.dep_layer)
        
        # Active Layer Depth
        self.act_layer = QLineEdit("0.3") # Can be string "2D90" or float
        self.layout.addRow("Active Layer Depth:", self.act_layer)
        
        self.setWidget(self.container)

class TimeDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Time Parameters", parent)
        self.container = QWidget()
        self.layout = QFormLayout(self.container)
        
        self.timescale = QSpinBox()
        self.timescale.setRange(1, 1000000)
        self.timescale.setValue(20)
        self.layout.addRow("Time Steps:", self.timescale)
        
        self.ts_length = QDoubleSpinBox()
        self.ts_length.setRange(1, 31536000) # 1 year max?
        self.ts_length.setValue(86400)
        self.layout.addRow("Step Length (s):", self.ts_length)
        
        self.setWidget(self.container)

class OptionsDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Options", parent)
        self.container = QWidget()
        self.layout = QFormLayout(self.container)
        
        self.save_dep = QComboBox()
        self.save_dep.addItems(["never", "yearly", "always"])
        self.layout.addRow("Save Deposit:", self.save_dep)
        
        self.round_param = QDoubleSpinBox()
        self.round_param.setValue(0)
        self.layout.addRow("Round Parameter:", self.round_param)
        
        self.force_pass = QCheckBox("Force Pass External Inputs")
        self.layout.addRow("", self.force_pass)
        
        self.setWidget(self.container)
