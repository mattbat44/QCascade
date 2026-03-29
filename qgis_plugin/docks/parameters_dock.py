"""
@brief Tabbed dock widget for Q-Cascade parameters and configuration
@author Matt Adams
"""

from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QTabWidget
)
from qgis.PyQt.QtCore import pyqtSignal

from .parameters.inputs_tab import InputsTab
from .parameters.physics_tab import PhysicsTab
from .parameters.sediment_tab import SedimentTab
from .parameters.time_tab import TimeTab
from .parameters.options_tab import OptionsTab
from .parameters.external_inputs_tab import ExternalInputsTab


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
        super().__init__("Q-Cascade Parameters", parent)
        
        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tab components
        self.inputs_tab = InputsTab(self)
        self.physics_tab = PhysicsTab(self)
        self.sediment_tab = SedimentTab(self)
        self.time_tab = TimeTab(self)
        self.options_tab = OptionsTab(self)
        self.external_inputs_tab = ExternalInputsTab(self)
        
        # Add tabs to widget
        self.tabs.addTab(self.inputs_tab, "Inputs")
        self.tabs.addTab(self.physics_tab, "Physics")
        self.tabs.addTab(self.sediment_tab, "Sediment")
        self.tabs.addTab(self.time_tab, "Time")
        self.tabs.addTab(self.options_tab, "Options")
        self.tabs.addTab(self.external_inputs_tab, "External Inputs")
        
        self.main_layout.addWidget(self.tabs)
        self.setWidget(self.container)
        
        # Connect signals from tabs to dock signals
        self.inputs_tab.layer_selected.connect(self.layer_selected.emit)
        self.inputs_tab.discharge_path_changed.connect(self.discharge_path_changed.emit)
        self.inputs_tab.save_config_requested.connect(self.save_config_requested.emit)
        self.inputs_tab.load_config_requested.connect(self.load_config_requested.emit)
        self.inputs_tab.load_run_requested.connect(self.load_run_requested.emit)
        self.inputs_tab.run_requested.connect(self.run_requested.emit)
        self.external_inputs_tab.external_input_added.connect(self.external_input_added.emit)
        
        # Store references for backward compatibility
        self.external_inputs_mapping = self.external_inputs_tab.external_inputs_mapping
        self.selected_reach_idx = self.external_inputs_tab.selected_reach_idx
        
        # Expose commonly accessed widgets for backward compatibility
        self.layer_combo = self.inputs_tab.layer_combo
        self.csv_path = self.inputs_tab.csv_path
        self.overbank_csv_path = self.inputs_tab.overbank_csv_path
        self.output_name = self.inputs_tab.output_name
        self.output_dir = self.inputs_tab.output_dir
        self.tr_cap = self.physics_tab.tr_cap
        self.tr_part = self.physics_tab.tr_part
        self.flow_depth = self.physics_tab.flow_depth
        self.vel_formula = self.physics_tab.vel_formula
        self.slope_red = self.physics_tab.slope_red
        self.width_calc = self.physics_tab.width_calc
        self.update_slope = self.physics_tab.update_slope
        self.min_phi = self.sediment_tab.min_phi
        self.max_phi = self.sediment_tab.max_phi
        self.n_classes = self.sediment_tab.n_classes
        self.dep_layer = self.sediment_tab.dep_layer
        self.act_layer = self.sediment_tab.act_layer
        self.timescale = self.time_tab.timescale
        self.ts_length = self.time_tab.ts_length
        self.save_dep = self.options_tab.save_dep
        self.round_param = self.options_tab.round_param
        self.force_pass = self.options_tab.force_pass
    
    def set_selected_reach(self, reach_idx):
        """Set the selected reach for external inputs management."""
        self.external_inputs_tab.set_selected_reach(reach_idx)
        # Keep reference for backward compatibility
        self.selected_reach_idx = reach_idx
    
    def get_layer_path(self):
        """Get the file path of the selected layer."""
        return self.inputs_tab.get_layer_path()

