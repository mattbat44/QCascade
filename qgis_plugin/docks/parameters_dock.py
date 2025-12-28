"""
@brief Tabbed dock widget for D-CASCADE parameters and configuration
@author D-CASCADE Team
"""

from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QFormLayout, QLineEdit, QPushButton, 
    QComboBox, QSpinBox, QDoubleSpinBox, QFileDialog, QCheckBox, 
    QHBoxLayout, QLabel, QTabWidget, QListWidget, QVBoxLayout, QMessageBox,
    QSpacerItem, QSizePolicy
)
from qgis.PyQt.QtCore import pyqtSignal
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel
import os


class ParametersDock(QDockWidget):
    """Tabbed dock widget containing all configuration panels."""
    
    layer_selected = pyqtSignal(object)  # Emits QgsVectorLayer
    external_input_added = pyqtSignal(int, str)  # reach_idx, csv_path
    discharge_path_changed = pyqtSignal(str)
    run_requested = pyqtSignal()
    save_config_requested = pyqtSignal(str)
    load_config_requested = pyqtSignal(str)
    load_run_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__("D-CASCADE Parameters", parent)
        
        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Add tabs
        self.inputs_tab = self.create_inputs_tab()
        self.tabs.addTab(self.inputs_tab, "Inputs")
        
        self.physics_tab = self.create_physics_tab()
        self.tabs.addTab(self.physics_tab, "Physics")
        
        self.sediment_tab = self.create_sediment_tab()
        self.tabs.addTab(self.sediment_tab, "Sediment")
        
        self.time_tab = self.create_time_tab()
        self.tabs.addTab(self.time_tab, "Time")
        
        self.options_tab = self.create_options_tab()
        self.tabs.addTab(self.options_tab, "Options")
        
        self.external_inputs_tab = self.create_external_inputs_tab()
        self.tabs.addTab(self.external_inputs_tab, "External Inputs")
        
        self.main_layout.addWidget(self.tabs)
        self.setWidget(self.container)
        
        # Store external inputs mapping
        self.external_inputs_mapping = {}  # {reach_idx: [csv_paths]}
        self.selected_reach_idx = None
        
    def create_inputs_tab(self):
        """Create the inputs tab with layer selector and discharge file."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # River Network Layer (QGIS layer selector)
        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.layer_combo.layerChanged.connect(self.on_layer_changed)
        layout.addRow("River Network Layer:", self.layer_combo)
        
        # Layer info label
        self.layer_info_label = QLabel("Select a vector layer with FromN, ToN attributes")
        self.layer_info_label.setWordWrap(True)
        layout.addRow("", self.layer_info_label)
        
        # Discharge CSV
        csv_layout = QHBoxLayout()
        self.csv_path = QLineEdit()
        self.csv_path.setToolTip("CSV file with water discharge per reach per time step.\nFormat: rows = time steps, columns = reaches.")
        self.csv_btn = QPushButton("Browse...")
        self.csv_btn.clicked.connect(self.browse_csv)
        csv_layout.addWidget(self.csv_path)
        csv_layout.addWidget(self.csv_btn)
        layout.addRow("Discharge (.csv):", csv_layout)
        self.csv_path.textChanged.connect(lambda: self.discharge_path_changed.emit(self.csv_path.text()))
        
        # Output Name
        self.output_name = QLineEdit("simulation_output")
        self.output_name.setToolTip("Name of the output simulation files.")
        layout.addRow("Output Name:", self.output_name)
        
        # Output Directory
        out_layout = QHBoxLayout()
        self.output_dir = QLineEdit()
        self.output_dir.setToolTip("Directory to save simulation outputs (optional). If empty, a cascade_results folder next to the config will be used.")
        self.output_dir_btn = QPushButton("Browse...")
        self.output_dir_btn.clicked.connect(self.browse_output_dir)
        out_layout.addWidget(self.output_dir)
        out_layout.addWidget(self.output_dir_btn)
        layout.addRow("Output Directory:", out_layout)
        
        # Actions row
        actions_layout = QHBoxLayout()
        self.load_cfg_btn = QPushButton("Load Config...")
        self.load_cfg_btn.clicked.connect(self.on_load_config_clicked)
        self.load_run_btn = QPushButton("Load From Run...")
        self.load_run_btn.clicked.connect(self.on_load_run_clicked)
        self.save_btn = QPushButton("Save Config...")
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.run_btn = QPushButton("Run Simulation")
        self.run_btn.clicked.connect(lambda: self.run_requested.emit())
        for btn in (self.load_cfg_btn, self.load_run_btn, self.save_btn, self.run_btn):
            actions_layout.addWidget(btn)
        layout.addRow("Actions:", actions_layout)

        # Spacer to keep layout tidy if more widgets are added later
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        return tab
    
    def create_physics_tab(self):
        """Create the physics parameters tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
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
        
        return tab

    def on_save_clicked(self):
        """Ask for path and emit save request."""
        path, _ = QFileDialog.getSaveFileName(self, "Save D-CASCADE config", "config.json", "JSON Files (*.json)")
        if path:
            self.save_config_requested.emit(path)

    def on_load_config_clicked(self):
        """Ask for config json and emit load request."""
        path, _ = QFileDialog.getOpenFileName(self, "Load D-CASCADE config", "", "JSON Files (*.json)")
        if path:
            self.load_config_requested.emit(path)

    def on_load_run_clicked(self):
        """Ask for model run pickle and emit load request."""
        path, _ = QFileDialog.getOpenFileName(self, "Load from run file", "", "Run Results (*.p *.pkl *.pickle);;All Files (*.*)")
        if path:
            self.load_run_requested.emit(path)
    
    def create_sediment_tab(self):
        """Create the sediment parameters tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
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
        
        return tab
    
    def create_time_tab(self):
        """Create the time parameters tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
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
        
        return tab
    
    def create_options_tab(self):
        """Create the options tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
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
        
        return tab
    
    def create_external_inputs_tab(self):
        """Create the external inputs management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info label
        info_label = QLabel("Select a reach in the map canvas to add external input CSV files.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Selected reach info
        reach_layout = QHBoxLayout()
        reach_layout.addWidget(QLabel("Selected Reach:"))
        self.selected_reach_label = QLabel("None")
        reach_layout.addWidget(self.selected_reach_label)
        reach_layout.addStretch()
        layout.addLayout(reach_layout)
        
        # Add external input button
        self.add_ext_input_btn = QPushButton("Add External Input CSV...")
        self.add_ext_input_btn.setEnabled(False)
        self.add_ext_input_btn.clicked.connect(self.add_external_input)
        layout.addWidget(self.add_ext_input_btn)
        
        # List of external inputs for selected reach
        self.ext_inputs_list = QListWidget()
        layout.addWidget(QLabel("External Inputs for Selected Reach:"))
        layout.addWidget(self.ext_inputs_list)
        
        # Remove button
        self.remove_ext_input_btn = QPushButton("Remove Selected")
        self.remove_ext_input_btn.setEnabled(False)
        self.remove_ext_input_btn.clicked.connect(self.remove_external_input)
        layout.addWidget(self.remove_ext_input_btn)
        
        layout.addStretch()
        
        return tab
    
    def on_layer_changed(self, layer):
        """Handle layer selection change."""
        if layer is None:
            self.layer_info_label.setText("Select a vector layer with FromN, ToN attributes")
            return
        
        # Validate layer has required attributes
        required_fields = ['FromN', 'ToN']
        field_names = [field.name() for field in layer.fields()]
        missing_fields = [f for f in required_fields if f not in field_names]
        
        if missing_fields:
            self.layer_info_label.setText(
                f"<b>Warning:</b> Missing required fields: {', '.join(missing_fields)}"
            )
            self.layer_info_label.setStyleSheet("color: red;")
        else:
            self.layer_info_label.setText(f"Layer: {layer.name()}\nFields: {', '.join(field_names[:5])}...")
            self.layer_info_label.setStyleSheet("")
        
        self.layer_selected.emit(layer)
    
    def browse_csv(self):
        """Browse for discharge CSV file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Discharge CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self.csv_path.setText(path)
    
    def browse_output_dir(self):
        """Browse for output directory."""
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory", "")
        if path:
            self.output_dir.setText(path)
    
    def set_selected_reach(self, reach_idx):
        """Set the selected reach for external inputs management."""
        self.selected_reach_idx = reach_idx
        if reach_idx is not None:
            self.selected_reach_label.setText(f"Reach {reach_idx}")
            self.add_ext_input_btn.setEnabled(True)
            self.update_external_inputs_list()
        else:
            self.selected_reach_label.setText("None")
            self.add_ext_input_btn.setEnabled(False)
            self.ext_inputs_list.clear()
    
    def update_external_inputs_list(self):
        """Update the list of external inputs for the selected reach."""
        self.ext_inputs_list.clear()
        if self.selected_reach_idx is not None:
            inputs = self.external_inputs_mapping.get(self.selected_reach_idx, [])
            for csv_path in inputs:
                self.ext_inputs_list.addItem(os.path.basename(csv_path))
            self.remove_ext_input_btn.setEnabled(len(inputs) > 0)
    
    def add_external_input(self):
        """Add an external input CSV file to the selected reach."""
        if self.selected_reach_idx is None:
            return
        
        path, _ = QFileDialog.getOpenFileName(
            self, "Select External Input CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        
        if self.selected_reach_idx not in self.external_inputs_mapping:
            self.external_inputs_mapping[self.selected_reach_idx] = []
        
        self.external_inputs_mapping[self.selected_reach_idx].append(path)
        self.external_inputs_list.addItem(os.path.basename(path))
        self.remove_ext_input_btn.setEnabled(True)
        
        self.external_input_added.emit(self.selected_reach_idx, path)
    
    def remove_external_input(self):
        """Remove the selected external input from the list."""
        if self.selected_reach_idx is None:
            return
        
        current_item = self.ext_inputs_list.currentItem()
        if current_item is None:
            return
        
        row = self.ext_inputs_list.row(current_item)
        if self.selected_reach_idx in self.external_inputs_mapping:
            inputs = self.external_inputs_mapping[self.selected_reach_idx]
            if row < len(inputs):
                del inputs[row]
                self.ext_inputs_list.takeItem(row)
                self.remove_ext_input_btn.setEnabled(len(inputs) > 0)
    
    def get_layer_path(self):
        """Get the file path of the selected layer."""
        layer = self.layer_combo.currentLayer()
        if layer is None:
            return None
        return layer.source()

