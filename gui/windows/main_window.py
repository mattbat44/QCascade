from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QLabel, QToolBar, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
import os

from gui.widgets.map_widget import MapWidget
from gui.widgets.plot_widget import PlotWidget
from gui.widgets.config_docks import (
    PathsDock, PhysicsDock, SedimentDock, TimeDock, OptionsDock
)
from gui.core.config_manager import (
    DCascadeConfig, PathsConfig, SedimentConfig, TimeConfig, 
    PhysicsConfig, OptionsConfig
)
from gui.core.runner_thread import RunnerThread

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("D-CASCADE GUI")
        self.resize(1600, 1000)
        
        # Enable dock nesting to allow complex layouts
        self.setDockNestingEnabled(True)
        
        # Initialize UI
        self.init_ui()
        
        # Restore state if available (to be implemented later)
        # self.restore_state()

    def init_ui(self):
        # Central widget (hidden or minimal)
        central_widget = QLabel("D-CASCADE Workspace")
        central_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        central_widget.setStyleSheet("font-size: 24px; color: #888;")
        self.setCentralWidget(central_widget)
        
        # Add Docks
        self.add_dock_widgets()
        
        # Add Toolbar
        self.create_toolbar()

    def add_dock_widgets(self):
        # --- Configuration Docks ---
        self.paths_dock = PathsDock(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.paths_dock)
        
        self.physics_dock = PhysicsDock(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.physics_dock)
        
        self.sediment_dock = SedimentDock(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sediment_dock)
        
        self.time_dock = TimeDock(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.time_dock)
        
        self.options_dock = OptionsDock(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.options_dock)
        
        # Tabify config docks
        self.tabifyDockWidget(self.paths_dock, self.physics_dock)
        self.tabifyDockWidget(self.physics_dock, self.sediment_dock)
        self.tabifyDockWidget(self.sediment_dock, self.time_dock)
        self.tabifyDockWidget(self.time_dock, self.options_dock)
        self.paths_dock.raise_() # Show paths first
        
        # --- GIS Map ---
        self.map_widget = MapWidget(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.map_widget)
        
        # --- Plots ---
        self.plot_widget = PlotWidget(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.plot_widget)
        
        # Tabify Map and Plot
        self.tabifyDockWidget(self.map_widget, self.plot_widget)
        self.map_widget.raise_()
        
        # --- Logs ---
        self.log_dock = QDockWidget("Simulation Logs", self)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_dock.setWidget(self.log_text)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)

        # --- Connections ---
        self.paths_dock.shapefile_selected.connect(self.map_widget.load_shapefile)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        run_action = QAction("Run Simulation", self)
        run_action.setStatusTip("Run the D-CASCADE simulation")
        run_action.triggered.connect(self.run_simulation)
        toolbar.addAction(run_action)

    def run_simulation(self):
        try:
            # Collect Config
            config = self.collect_config()
            
            # Save to temporary JSON
            config_path = os.path.abspath("temp_config.json")
            config.to_json(config_path)
            
            self.log_text.append(f"Configuration saved to {config_path}")
            
            # Start Thread
            self.runner = RunnerThread(config_path)
            self.runner.log_message.connect(self.on_log_message)
            self.runner.simulation_finished.connect(self.on_simulation_finished)
            self.runner.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", str(e))

    def collect_config(self):
        # Paths
        paths = PathsConfig(
            river_network_shp=self.paths_dock.shp_path.text(),
            discharge_csv=self.paths_dock.csv_path.text(),
            output_name=self.paths_dock.output_name.text()
        )
        
        # Sediment
        sediment = SedimentConfig(
            range=[self.sediment_dock.min_phi.value(), self.sediment_dock.max_phi.value()],
            n_classes=self.sediment_dock.n_classes.value(),
            deposit_layer_thickness=self.sediment_dock.dep_layer.value(),
            active_layer_depth=self.sediment_dock.act_layer.text(), # Need to handle float conversion if needed
            active_layer_method=1 # Fixed for now or add widget
        )
        
        # Time
        time = TimeConfig(
            timescale=self.time_dock.timescale.value(),
            ts_length=self.time_dock.ts_length.value()
        )
        
        # Physics
        # Map combo box index to value (index 0 -> value 1, etc.)
        # Or parse the string "1: ..."
        tr_cap_val = int(self.physics_dock.tr_cap.currentText().split(":")[0])
        tr_part_val = int(self.physics_dock.tr_part.currentText().split(":")[0])
        
        physics = PhysicsConfig(
            transport_capacity_formula=tr_cap_val,
            transport_partitioning=tr_part_val,
            flow_depth_formula=1, # TODO: Add widget
            velocity_formula=2, # TODO: Add widget
            velocity_partitioning=1,
            slope_reduction=1, # TODO: Add widget
            width_calculation=1, # TODO: Add widget
            update_slope=self.physics_dock.update_slope.isChecked(),
            velocity_height="2D90"
        )
        
        # Options
        options = OptionsConfig(
            save_deposit_layer=self.options_dock.save_dep.currentText(),
            round_parameter=self.options_dock.round_param.value(),
            force_pass_external_inputs=self.options_dock.force_pass.isChecked()
        )
        
        return DCascadeConfig(
            paths=paths,
            sediment=sediment,
            time=time,
            physics=physics,
            options=options
        )

    def on_log_message(self, msg):
        self.log_text.append(msg)

    def on_simulation_finished(self, success, msg):
        if success:
            QMessageBox.information(self, "Simulation Finished", msg)
            # TODO: Load results into PlotWidget
            # self.plot_widget.load_results(...)
        else:
            QMessageBox.critical(self, "Simulation Failed", msg)

    def closeEvent(self, event):
        # Save state
        # self.save_state()
        super().closeEvent(event)
