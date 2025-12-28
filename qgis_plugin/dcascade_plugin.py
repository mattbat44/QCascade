"""
@brief D-CASCADE QGIS Plugin main class
@author D-CASCADE Team
"""

from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QFileDialog
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis, QgsGraduatedSymbolRenderer, QgsSymbol, QgsStyle, QgsStyle
from qgis.gui import QgsMapToolIdentifyFeature
import os
import json
from pathlib import Path

from .docks.parameters_dock import ParametersDock
from .docks.results_viewer_dock import ResultsViewerDock
from .core.config_manager import DCascadeConfig, PathsConfig, SedimentConfig, TimeConfig, PhysicsConfig, OptionsConfig, ExternalInputsConfig
from .core.runner_thread import RunnerThread


class DCascadePlugin:
    """Main plugin class for D-CASCADE QGIS plugin."""
    
    def __init__(self, iface):
        """Initialize the plugin."""
        self.iface = iface
        self.canvas = iface.mapCanvas()
        
        # Plugin components
        self.parameters_dock = None
        self.results_viewer_dock = None
        
        # Layer and selection tracking
        self.network_layer = None
        self.selected_reach_id = None
        self.results_data = None
        self.current_time_step = 0
        self.animation_field = None  # Field name used for animation
        
        # Initialize plugin
        self.init_plugin()
    
    def init_plugin(self):
        """Initialize plugin components."""
        # Create dock widgets
        self.parameters_dock = ParametersDock(self.iface.mainWindow())
        self.results_viewer_dock = ResultsViewerDock(self.iface.mainWindow())
        
        # Add docks to QGIS
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.parameters_dock)
        self.parameters_dock.setVisible(False)  # Hide by default
        
        self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.results_viewer_dock)
        self.results_viewer_dock.setVisible(False)  # Hide by default
        
        # Connect signals
        self.parameters_dock.layer_selected.connect(self.on_layer_selected)
        self.parameters_dock.external_input_added.connect(self.on_external_input_added)
        
        self.results_viewer_dock.time_step_changed.connect(self.on_time_step_changed)
        self.results_viewer_dock.reach_selected_for_graph.connect(self.graph_reach)
        
        # Connect map canvas selection
        self.canvas.selectionChanged.connect(self.on_map_selection_changed)
        
        # Add toolbar action
        self.action = QAction("D-CASCADE", self.iface.mainWindow())
        self.action.setObjectName("DCascadeAction")
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&D-CASCADE", self.action)
        
        QgsMessageLog.logMessage("D-CASCADE plugin initialized", "D-CASCADE", Qgis.Info)
    
    def unload(self):
        """Unload the plugin."""
        # Remove menu and toolbar
        self.iface.removePluginMenu("&D-CASCADE", self.action)
        self.iface.removeToolBarIcon(self.action)
        
        # Remove docks
        if self.parameters_dock:
            self.parameters_dock.close()
        if self.results_viewer_dock:
            self.results_viewer_dock.close()
        
        # Disconnect signals
        if self.canvas:
            self.canvas.selectionChanged.disconnect(self.on_map_selection_changed)
        
        QgsMessageLog.logMessage("D-CASCADE plugin unloaded", "D-CASCADE", Qgis.Info)
    
    def run(self):
        """Main entry point - show/hide docks."""
        # Toggle visibility of docks
        if self.parameters_dock:
            self.parameters_dock.setVisible(not self.parameters_dock.isVisible())
        if self.results_viewer_dock:
            self.results_viewer_dock.setVisible(not self.results_viewer_dock.isVisible())
        
        # If showing, add toolbar buttons
        if self.parameters_dock.isVisible():
            self.add_toolbar_actions()
    
    def add_toolbar_actions(self):
        """Add action buttons to toolbar."""
        # Run simulation action (can be added to plugin toolbar or menu)
        if not hasattr(self, 'run_action'):
            self.run_action = QAction("Run Simulation", self.iface.mainWindow())
            self.run_action.triggered.connect(self.run_simulation)
            self.iface.addToolBarIcon(self.run_action)
    
    def on_layer_selected(self, layer):
        """Handle network layer selection."""
        if layer is None:
            self.network_layer = None
            return
        
        # Validate it's a vector layer
        if not isinstance(layer, QgsVectorLayer):
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Invalid Layer",
                "Please select a vector layer."
            )
            return
        
        # Store reference
        self.network_layer = layer
        
        # Validate required fields
        field_names = [field.name() for field in layer.fields()]
        required = ['FromN', 'ToN']
        missing = [f for f in required if f not in field_names]
        
        if missing:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Missing Fields",
                f"Layer is missing required fields: {', '.join(missing)}"
            )
            return
        
        QgsMessageLog.logMessage(
            f"Network layer selected: {layer.name()}",
            "D-CASCADE",
            Qgis.Info
        )
    
    def on_map_selection_changed(self):
        """Handle map canvas feature selection change."""
        if self.network_layer is None:
            return
        
        selected_features = self.network_layer.selectedFeatures()
        if not selected_features:
            self.selected_reach_id = None
            self.parameters_dock.set_selected_reach(None)
            return
        
        # Get the first selected feature's FromN
        feature = selected_features[0]
        from_n_idx = self.network_layer.fields().indexFromName('FromN')
        if from_n_idx >= 0:
            self.selected_reach_id = feature.attribute(from_n_idx)
            self.parameters_dock.set_selected_reach(self.selected_reach_id)
            
            # Graph selected reach in results viewer
            if self.results_viewer_dock and self.results_viewer_dock.results_data is not None:
                self.results_viewer_dock.graph_selected_reach(self.selected_reach_id)
    
    def on_external_input_added(self, reach_idx, csv_path):
        """Handle external input CSV added to reach."""
        QgsMessageLog.logMessage(
            f"External input added to reach {reach_idx}: {csv_path}",
            "D-CASCADE",
            Qgis.Info
        )
    
    def on_time_step_changed(self, time_step):
        """Handle time step change in results viewer - update layer symbology."""
        self.current_time_step = time_step
        
        if self.network_layer is None or self.results_viewer_dock.results_data is None:
            return
        
        # Update layer symbology based on current time step
        self.update_layer_symbology(time_step)
    
    def update_layer_symbology(self, time_step):
        """Update network layer symbology based on results for given time step."""
        if self.network_layer is None or self.results_viewer_dock.results_data is None:
            return
        
        # Get the current variable from results viewer
        variable = self.results_viewer_dock.dyn_variable_combo.currentText()
        if variable not in self.results_viewer_dock.results_data:
            return
        
        data = self.results_viewer_dock.results_data[variable]
        if time_step >= data.shape[0]:
            return
        
        # Get field name for this variable (create if doesn't exist)
        field_name = f"result_{variable.replace(' ', '_').replace('[', '').replace(']', '')}"
        self.animation_field = field_name
        
        # Add field if it doesn't exist
        from qgis.core import QgsField
        from qgis.PyQt.QtCore import QVariant
        
        fields = self.network_layer.fields()
        field_idx = fields.indexFromName(field_name)
        
        if field_idx < 0:
            new_field = QgsField(field_name, QVariant.Double)
            self.network_layer.dataProvider().addAttributes([new_field])
            self.network_layer.updateFields()
            field_idx = self.network_layer.fields().indexFromName(field_name)
        
        # Update attribute values for current time step
        self.network_layer.startEditing()
        
        # Get FromN field index
        from_n_idx = self.network_layer.fields().indexFromName('FromN')
        if from_n_idx < 0:
            return
        
        for feature in self.network_layer.getFeatures():
            from_n = feature.attribute(from_n_idx)
            if from_n is not None:
                try:
                    # Convert FromN to integer index (assuming FromN starts at some value)
                    # This might need adjustment based on your data
                    reach_idx = int(from_n) - 1  # Adjust based on your indexing
                    if 0 <= reach_idx < data.shape[1]:
                        value = float(data[time_step, reach_idx])
                        self.network_layer.changeAttributeValue(
                            feature.id(),
                            field_idx,
                            value
                        )
                except (ValueError, IndexError):
                    pass
        
        self.network_layer.commitChanges()
        
        # Update symbology with graduated renderer
        if field_idx >= 0:
            symbol = QgsSymbol.defaultSymbol(self.network_layer.geometryType())
            
            # Create graduated renderer using factory method
            style = QgsStyle.defaultStyle()
            ramp = style.colorRamp('Spectral')
            
            renderer = QgsGraduatedSymbolRenderer.createRenderer(
                self.network_layer,
                field_name,
                nclasses=5,
                mode=QgsGraduatedSymbolRenderer.EqualInterval,
                symbol=symbol,
                ramp=ramp
            )
            
            self.network_layer.setRenderer(renderer)
            self.network_layer.triggerRepaint()
            self.canvas.refresh()
    
    def graph_reach(self, reach_idx):
        """Graph a specific reach in results viewer."""
        if self.results_viewer_dock:
            self.results_viewer_dock.graph_selected_reach(reach_idx)
    
    def run_simulation(self):
        """Run D-CASCADE simulation with current configuration."""
        try:
            # Collect configuration
            config = self.collect_config()
            
            if config is None:
                return  # User cancelled or error
            
            # Save to temporary JSON
            config_path = os.path.abspath("temp_config.json")
            config.to_json(config_path)
            
            QgsMessageLog.logMessage(
                f"Configuration saved to {config_path}",
                "D-CASCADE",
                Qgis.Info
            )
            
            # Start simulation thread
            self.runner = RunnerThread(config_path)
            self.runner.log_message.connect(self.on_log_message)
            self.runner.simulation_finished.connect(self.on_simulation_finished)
            self.runner.start()
            
            QMessageBox.information(
                self.iface.mainWindow(),
                "Simulation Started",
                "Simulation started in background. Check the QGIS message log for progress."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Configuration Error",
                str(e)
            )
    
    def collect_config(self):
        """Collect configuration from parameter dock."""
        if self.parameters_dock is None:
            return None
        
        # Get layer path
        layer = self.parameters_dock.layer_combo.currentLayer()
        if layer is None:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "No Layer",
                "Please select a network layer first."
            )
            return None
        
        layer_path = layer.source()
        
        # Paths
        paths = PathsConfig(
            river_network_shp=layer_path,
            discharge_csv=self.parameters_dock.csv_path.text(),
            output_name=self.parameters_dock.output_name.text(),
            output_dir=self.parameters_dock.output_dir.text() or None
        )
        
        # Sediment
        al_depth_text = self.parameters_dock.act_layer.text()
        try:
            al_depth_val = float(al_depth_text)
        except ValueError:
            al_depth_val = al_depth_text
        
        sediment = SedimentConfig(
            range=[self.parameters_dock.min_phi.value(), self.parameters_dock.max_phi.value()],
            n_classes=self.parameters_dock.n_classes.value(),
            deposit_layer_thickness=self.parameters_dock.dep_layer.value(),
            active_layer_depth=al_depth_val,
            active_layer_method=1
        )
        
        # Time
        time = TimeConfig(
            timescale=self.parameters_dock.timescale.value(),
            ts_length=self.parameters_dock.ts_length.value()
        )
        
        # Physics
        tr_cap_val = int(self.parameters_dock.tr_cap.currentText().split(":")[0])
        tr_part_val = int(self.parameters_dock.tr_part.currentText().split(":")[0])
        flow_depth_val = int(self.parameters_dock.flow_depth.currentText().split(":")[0])
        vel_formula_val = int(self.parameters_dock.vel_formula.currentText().split(":")[0])
        slope_red_val = int(self.parameters_dock.slope_red.currentText().split(":")[0])
        width_calc_val = int(self.parameters_dock.width_calc.currentText().split(":")[0])
        
        physics = PhysicsConfig(
            transport_capacity_formula=tr_cap_val,
            transport_partitioning=tr_part_val,
            flow_depth_formula=flow_depth_val,
            velocity_formula=vel_formula_val,
            velocity_partitioning=1,
            slope_reduction=slope_red_val,
            width_calculation=width_calc_val,
            update_slope=self.parameters_dock.update_slope.isChecked(),
            velocity_height="2D90"
        )
        
        # Options
        options = OptionsConfig(
            save_deposit_layer=self.parameters_dock.save_dep.currentText(),
            round_parameter=int(self.parameters_dock.round_param.value()),
            force_pass_external_inputs=self.parameters_dock.force_pass.isChecked()
        )
        
        # External inputs from parameters dock
        ext_cfg = None
        try:
            ext_mapping = self.parameters_dock.external_inputs_mapping
            if ext_mapping:
                from .core.config_manager import PerReachCSV
                per_reach = []
                for reach_str, paths_list in ext_mapping.items():
                    reach_idx = int(reach_str)
                    for p in paths_list:
                        per_reach.append(PerReachCSV(reach_idx=reach_idx, path=p))
                ext_cfg = ExternalInputsConfig(
                    per_reach_csvs=per_reach,
                    grain_unit="mm",
                    default_sigma_g=1.6
                )
        except Exception as e:
            QgsMessageLog.logMessage(
                f"External inputs config error: {e}",
                "D-CASCADE",
                Qgis.Warning
            )
        
        return DCascadeConfig(
            paths=paths,
            sediment=sediment,
            time=time,
            physics=physics,
            options=options,
            external_inputs=ext_cfg
        )
    
    def on_log_message(self, msg):
        """Handle log message from simulation thread."""
        QgsMessageLog.logMessage(msg, "D-CASCADE", Qgis.Info)
    
    def on_simulation_finished(self, success, msg):
        """Handle simulation completion."""
        if success:
            QMessageBox.information(
                self.iface.mainWindow(),
                "Simulation Finished",
                msg
            )
            # Auto-load results
            self.load_results_after_simulation()
        else:
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Simulation Failed",
                msg
            )
    
    def load_results_after_simulation(self):
        """Load simulation results after completion."""
        try:
            output_name = self.parameters_dock.output_name.text()
            output_dir = self.parameters_dock.output_dir.text() or "cascade_results"
            
            # Construct results path
            if Path(output_dir).is_absolute():
                results_path = Path(output_dir) / f"{output_name}.p"
            else:
                results_path = Path.cwd() / output_dir / f"{output_name}.p"
            
            if results_path.exists():
                self.results_viewer_dock.load_results_from_path(str(results_path))
                self.results_viewer_dock.setVisible(True)
                self.results_data = self.results_viewer_dock.results_data
        except Exception as e:
            QgsMessageLog.logMessage(
                f"Could not auto-load results: {e}",
                "D-CASCADE",
                Qgis.Warning
            )

