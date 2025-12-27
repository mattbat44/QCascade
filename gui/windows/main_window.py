from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QLabel, QToolBar, QTextEdit, QMessageBox, QStatusBar
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QKeySequence
import os

from gui.widgets.map_widget import MapWidget
from gui.widgets.plot_widget import PlotWidget
from gui.widgets.discharge_editor import DischargeEditor
from gui.widgets.results_viewer import ResultsViewer
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
        self.setWindowTitle("D-CASCADE - Sediment Transport Modeling")
        self.resize(1600, 1000)
        
        # Enable dock nesting to allow complex layouts
        self.setDockNestingEnabled(True)
        
        # Settings for persistence
        self.settings = QSettings('D-CASCADE', 'GUI')
        
        # Initialize UI
        self.init_ui()
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        # Restore state if available
        self.restore_state()
        
        # Status bar
        self.statusBar().showMessage("Ready")

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
        
        # --- Discharge Editor ---
        self.discharge_editor = DischargeEditor(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.discharge_editor)
        
        # --- Results Viewer ---
        self.results_viewer = ResultsViewer(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.results_viewer)
        
        # --- Plots (legacy, kept for compatibility) ---
        self.plot_widget = PlotWidget(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.plot_widget)
        
        # Tabify all right-side widgets
        self.tabifyDockWidget(self.map_widget, self.discharge_editor)
        self.tabifyDockWidget(self.discharge_editor, self.results_viewer)
        self.tabifyDockWidget(self.results_viewer, self.plot_widget)
        self.map_widget.raise_()
        
        # --- Logs ---
        self.log_dock = QDockWidget("Simulation Logs", self)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_dock.setWidget(self.log_text)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)

        # --- Connections ---
        self.paths_dock.shapefile_selected.connect(self.map_widget.load_shapefile)
        self.paths_dock.csv_path.textChanged.connect(self.discharge_editor.set_discharge_path)
        self.discharge_editor.discharge_updated.connect(self.on_discharge_updated)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Run action
        run_action = QAction("▶ Run Simulation", self)
        run_action.setStatusTip("Run the D-CASCADE simulation (Ctrl+R)")
        run_action.setShortcut(QKeySequence("Ctrl+R"))
        run_action.triggered.connect(self.run_simulation)
        toolbar.addAction(run_action)
        
        toolbar.addSeparator()
        
        # Load results action
        load_results_action = QAction("📊 Load Results", self)
        load_results_action.setStatusTip("Load simulation results from file (Ctrl+L)")
        load_results_action.setShortcut(QKeySequence("Ctrl+L"))
        load_results_action.triggered.connect(self.results_viewer.load_results)
        toolbar.addAction(load_results_action)
        
        toolbar.addSeparator()
        
        # Help action
        help_action = QAction("❓ Help", self)
        help_action.setStatusTip("Show help documentation (F1)")
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)
        
        # About action
        about_action = QAction("ℹ About", self)
        about_action.setStatusTip("About D-CASCADE")
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)
    
    def setup_shortcuts(self):
        """Setup additional keyboard shortcuts."""
        # Ctrl+S to save config/changes
        save_shortcut = QKeySequence("Ctrl+S")
        save_action = QAction("Save", self)
        save_action.setShortcut(save_shortcut)
        save_action.triggered.connect(self.save_all)
        self.addAction(save_action)
        
        # Ctrl+Q to quit
        quit_shortcut = QKeySequence("Ctrl+Q")
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(quit_shortcut)
        quit_action.triggered.connect(self.close)
        self.addAction(quit_action)

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
            output_name=self.paths_dock.output_name.text(),
            output_dir=self.paths_dock.output_dir.text() or None
        )
        
        # Sediment
        al_depth_text = self.sediment_dock.act_layer.text()
        try:
            al_depth_val = float(al_depth_text)
        except ValueError:
            al_depth_val = al_depth_text

        sediment = SedimentConfig(
            range=[self.sediment_dock.min_phi.value(), self.sediment_dock.max_phi.value()],
            n_classes=self.sediment_dock.n_classes.value(),
            deposit_layer_thickness=self.sediment_dock.dep_layer.value(),
            active_layer_depth=al_depth_val,
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
            round_parameter=int(self.options_dock.round_param.value()),
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
        # Also update status bar
        self.statusBar().showMessage(msg, 5000)

    def on_simulation_finished(self, success, msg):
        if success:
            QMessageBox.information(self, "Simulation Finished", msg)
            # Load results into viewer
            self.load_results_after_simulation()
        else:
            QMessageBox.critical(self, "Simulation Failed", msg)
    
    def load_results_after_simulation(self):
        """Load simulation results into the results viewer."""
        try:
            output_name = self.paths_dock.output_name.text()
            output_dir = self.paths_dock.output_dir.text() or "cascade_results"
            
            # Construct results path
            from pathlib import Path
            if Path(output_dir).is_absolute():
                results_path = Path(output_dir) / f"{output_name}.p"
            else:
                results_path = Path.cwd() / output_dir / f"{output_name}.p"
            
            if results_path.exists():
                self.results_viewer.load_results_from_path(str(results_path))
                self.results_viewer.raise_()  # Bring results viewer to front
            
        except Exception as e:
            print(f"Warning: Could not auto-load results: {e}")
    
    def on_discharge_updated(self, path):
        """Handle discharge data update."""
        self.paths_dock.csv_path.setText(path)

    def closeEvent(self, event):
        """Save state before closing."""
        self.save_state()
        super().closeEvent(event)
    
    def save_state(self):
        """Save window state and geometry."""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
    
    def restore_state(self):
        """Restore window state and geometry."""
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        window_state = self.settings.value('windowState')
        if window_state:
            self.restoreState(window_state)
    
    def save_all(self):
        """Save all current changes (map, discharge, etc.)."""
        saved_items = []
        
        # Save map changes if modified
        if self.map_widget.save_btn.isEnabled():
            self.map_widget.save_shapefile()
            saved_items.append("Shapefile")
        
        # Save discharge if modified
        if self.discharge_editor.save_btn.isEnabled():
            self.discharge_editor.save_discharge_csv()
            saved_items.append("Discharge data")
        
        if saved_items:
            QMessageBox.information(
                self,
                "Saved",
                f"Saved: {', '.join(saved_items)}"
            )
        else:
            self.statusBar().showMessage("No changes to save", 3000)
    
    def show_help(self):
        """Show help dialog."""
        help_text = """
        <h2>D-CASCADE GUI Help</h2>
        
        <h3>Quick Start:</h3>
        <ol>
            <li><b>Load Data:</b> Use the "Input Files" tab to load your river network shapefile and discharge CSV.</li>
            <li><b>Configure Model:</b> Set parameters in the Physics, Sediment, Time, and Options tabs.</li>
            <li><b>Run Simulation:</b> Click "▶ Run Simulation" or press Ctrl+R.</li>
            <li><b>View Results:</b> Switch to the "Results Analysis" tab to visualize outputs.</li>
        </ol>
        
        <h3>Features:</h3>
        <ul>
            <li><b>GIS Viewer:</b> Interactive map showing the river network. Click "Edit Selected Reach" to modify reach attributes.</li>
            <li><b>Discharge Editor:</b> View and edit discharge time series data.</li>
            <li><b>Results Analysis:</b> Multiple visualization types for simulation outputs.</li>
        </ul>
        
        <h3>Keyboard Shortcuts:</h3>
        <ul>
            <li><b>Ctrl+R:</b> Run simulation</li>
            <li><b>Ctrl+L:</b> Load results</li>
            <li><b>Ctrl+S:</b> Save all changes</li>
            <li><b>Ctrl+Q:</b> Quit</li>
            <li><b>F1:</b> Show this help</li>
        </ul>
        
        <h3>More Information:</h3>
        <p>Visit the D-CASCADE documentation for detailed information about the model and its parameters.</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("D-CASCADE Help")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(help_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def show_about(self):
        """Show about dialog."""
        about_text = """
        <h2>D-CASCADE v2.0.0</h2>
        <p><b>Dynamic CAtchment Sediment Connectivity And Delivery</b></p>
        
        <p>A Python-based modeling framework for sediment transport and connectivity analysis in large river networks.</p>
        
        <h3>Key Features:</h3>
        <ul>
            <li>Sediment transport simulation through river networks</li>
            <li>Multiple transport capacity formulas</li>
            <li>Grain size distribution tracking</li>
            <li>Interactive GIS-based interface</li>
            <li>Advanced result visualization</li>
        </ul>
        
        <p><b>Development Team:</b> D-CASCADE Contributors</p>
        <p><b>License:</b> See repository for details</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About D-CASCADE")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
