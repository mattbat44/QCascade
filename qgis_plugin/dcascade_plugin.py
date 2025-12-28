"""
@brief D-CASCADE QGIS Plugin main class
@author D-CASCADE Team
"""

from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QFileDialog, QMenu, QToolButton
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis, QgsGraduatedSymbolRenderer, QgsSymbol, QgsStyle, QgsStyle
from qgis.gui import QgsMapToolIdentifyFeature
import os
import json
import pickle
from pathlib import Path
import numpy as np

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

        # Track initialization to keep init_plugin idempotent when QGIS calls initGui.
        self.initialized = False
        
        # Plugin components
        self.parameters_dock = None
        self.results_viewer_dock = None
        self.toolbar_button = None
        self.toolbar_widget_action = None
        self.parameters_action = None
        self.results_action = None
        self.animation_layer = None
        
        # Layer and selection tracking
        self.network_layer = None
        self.selected_reach_id = None
        self.results_data = None
        self.current_time_step = 0
        self.animation_field = None  # Field name used for animation
        
        # Initialize plugin
        self.init_plugin()

    def initGui(self):
        """QGIS hook: ensure plugin is initialized when loaded."""
        self.init_plugin()
    
    def init_plugin(self):
        """Initialize plugin components."""
        if self.initialized:
            return

        # Clean up any stale toolbar items from previous loads
        self.remove_toolbar_items()

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
        self.parameters_dock.run_requested.connect(self.run_simulation)
        self.parameters_dock.save_config_requested.connect(self.on_save_config_requested)
        self.parameters_dock.load_config_requested.connect(self.on_load_config_requested)
        self.parameters_dock.load_run_requested.connect(self.on_load_run_requested)
        
        self.results_viewer_dock.time_step_changed.connect(self.on_time_step_changed)
        self.results_viewer_dock.reach_selected_for_graph.connect(self.graph_reach)
        self.results_viewer_dock.results_loaded.connect(self.on_results_loaded)
        self.results_viewer_dock.animation_settings_changed.connect(lambda: self.on_time_step_changed(self.current_time_step))
        
        # Connect map canvas selection
        self.canvas.selectionChanged.connect(self.on_map_selection_changed)
        
        # Dropdown menu under a single D-CASCADE toolbar button
        self.parameters_action = QAction("Show Parameters", self.iface.mainWindow())
        self.parameters_action.setObjectName("DCascadeParametersAction")
        self.parameters_action.triggered.connect(self.show_parameters_dock)

        self.results_action = QAction("Show Results", self.iface.mainWindow())
        self.results_action.setObjectName("DCascadeResultsAction")
        self.results_action.triggered.connect(self.show_results_dock)

        menu = QMenu()
        menu.addAction(self.parameters_action)
        menu.addAction(self.results_action)

        self.toolbar_button = QToolButton()
        self.toolbar_button.setText("D-CASCADE")
        self.toolbar_button.setMenu(menu)
        self.toolbar_button.setPopupMode(QToolButton.InstantPopup)
        self.toolbar_button.setToolTip("D-CASCADE tools")

        # Place the dropdown button on the toolbar in order
        self.toolbar_widget_action = self.iface.addToolBarWidget(self.toolbar_button)

        # Add plugin menu entries
        self.iface.addPluginToMenu("&D-CASCADE", self.parameters_action)
        self.iface.addPluginToMenu("&D-CASCADE", self.results_action)
        
        # Force initial layer selection from parameters dock
        if self.parameters_dock and self.parameters_dock.layer_combo:
            current_layer = self.parameters_dock.layer_combo.currentLayer()
            if current_layer:
                self.on_layer_selected(current_layer)
                # Also check for existing selection
                self.on_map_selection_changed()
        
        QgsMessageLog.logMessage("D-CASCADE plugin initialized", "D-CASCADE", Qgis.Info)
        self.initialized = True
    
    def unload(self):
        """Unload the plugin."""
        # Remove menu entries
        if self.parameters_action:
            self.iface.removePluginMenu("&D-CASCADE", self.parameters_action)
        if self.results_action:
            self.iface.removePluginMenu("&D-CASCADE", self.results_action)

        # Remove toolbar items
        self.remove_toolbar_items()
        
        # Remove docks
        if self.parameters_dock:
            self.parameters_dock.close()
        if self.results_viewer_dock:
            try:
                self.results_viewer_dock.stop_animation()
            except Exception:
                pass
            self.results_viewer_dock.close()
        # Remove temporary animation layer if present
        if self.animation_layer:
            from qgis.core import QgsProject
            QgsProject.instance().removeMapLayer(self.animation_layer.id())
            self.animation_layer = None
        
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

    def show_parameters_dock(self):
        """Show parameters dock from toolbar action."""
        if self.parameters_dock:
            self.parameters_dock.setVisible(True)
            self.parameters_dock.raise_()

    def show_results_dock(self):
        """Show results dock from toolbar action."""
        if self.results_viewer_dock:
            self.results_viewer_dock.setVisible(True)
            self.results_viewer_dock.raise_()
            # Ensure plot dock is shown alongside controls
            self.results_viewer_dock.show_plot_dock()

    def remove_toolbar_items(self):
        """Remove any toolbar items we may have added (dropdown or legacy)."""
        # Remove dropdown widget if present
        if self.toolbar_widget_action:
            self.iface.removeToolBarIcon(self.toolbar_widget_action)
            self.toolbar_widget_action = None
        self.toolbar_button = None

        # Remove any legacy actions if still around
        for act in [getattr(self, "action", None), self.parameters_action, self.results_action, getattr(self, "run_action", None)]:
            if act:
                try:
                    self.iface.removeToolBarIcon(act)
                except Exception:
                    pass
    
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
            if self.results_viewer_dock:
                self.results_viewer_dock.graph_selected_reach(None)
            return

        from_n_idx = self.network_layer.fields().indexFromName('FromN')
        if from_n_idx < 0:
            return

        reach_ids = []
        for feature in selected_features:
            reach_ids.append(feature.attribute(from_n_idx))

        # Track first for params dock; pass all to results viewer
        self.selected_reach_id = reach_ids[0] if reach_ids else None
        self.parameters_dock.set_selected_reach(self.selected_reach_id)

        if self.results_viewer_dock and self.results_viewer_dock.results_data is not None:
            self.results_viewer_dock.graph_selected_reach(reach_ids)
    
    def on_external_input_added(self, reach_idx, csv_path):
        """Handle external input CSV added to reach."""
        QgsMessageLog.logMessage(
            f"External input added to reach {reach_idx}: {csv_path}",
            "D-CASCADE",
            Qgis.Info
        )
    
    def on_results_loaded(self):
        """Handle results loaded signal."""
        # Initialize animation layer at time step 0
        self.on_time_step_changed(0)

    def on_time_step_changed(self, time_step):
        """Handle time step change in results viewer - update layer symbology."""
        self.current_time_step = time_step
        
        if self.network_layer is None or self.results_viewer_dock.results_data is None:
            return
        
        # Update layer symbology based on current time step
        self.update_layer_symbology(time_step)
    
    def update_layer_symbology(self, time_step):
        """Update network layer symbology based on results for given time step."""
        if self.network_layer is None:
            QgsMessageLog.logMessage("Cannot update symbology: No network layer selected", "D-CASCADE", Qgis.Warning)
            return
            
        if self.results_viewer_dock.results_data is None:
            return
        
        # Get the current variable from results viewer
        variable = self.results_viewer_dock.dyn_variable_combo.currentText()
        if variable not in self.results_viewer_dock.results_data:
            QgsMessageLog.logMessage(f"Cannot update symbology: Variable '{variable}' not found in results", "D-CASCADE", Qgis.Warning)
            return
        
        data = self.results_viewer_dock.results_data[variable]
        if time_step >= data.shape[0]:
            return
        
        from qgis.core import (
            QgsVectorLayer,
            QgsField,
            QgsFeature,
            QgsProject,
            QgsWkbTypes,
            QgsGraduatedSymbolRenderer,
            QgsSymbol,
            QgsStyle,
            QgsRendererRange,
        )
        from qgis.PyQt.QtCore import QVariant

        geom_type = QgsWkbTypes.displayString(self.network_layer.wkbType())
        crs_authid = self.network_layer.crs().authid()

        # Create or reuse in-memory animation layer
        if self.animation_layer is None:
            uri = f"{geom_type}?crs={crs_authid}"
            self.animation_layer = QgsVectorLayer(uri, "D-CASCADE Animation", "memory")
            prov = self.animation_layer.dataProvider()
            prov.addAttributes([
                QgsField("FromN", QVariant.String),
                QgsField("ToN", QVariant.String),
                QgsField("value", QVariant.Double),
            ])
            self.animation_layer.updateFields()
            QgsProject.instance().addMapLayer(self.animation_layer)
            # Move animation layer above network layer for visibility
            root = QgsProject.instance().layerTreeRoot()
            net_node = root.findLayer(self.network_layer.id())
            anim_node = root.findLayer(self.animation_layer.id())
            if net_node and anim_node:
                parent = net_node.parent() or root
                anim_parent = anim_node.parent() or root
                try:
                    # QgsLayerTreeGroup does not have indexOfChild, use children().index()
                    idx = parent.children().index(net_node)
                    parent.insertChildNode(idx, anim_node.clone())
                    anim_parent.removeChildNode(anim_node)
                except ValueError:
                    pass
        else:
            prov = self.animation_layer.dataProvider()
            prov.truncate()

        # Build features with current timestep values
        from_n_idx = self.network_layer.fields().indexFromName('FromN')
        to_n_idx = self.network_layer.fields().indexFromName('ToN')
        if from_n_idx < 0:
            return

        features = []
        for feature in self.network_layer.getFeatures():
            from_n = feature.attribute(from_n_idx)
            to_n = feature.attribute(to_n_idx) if to_n_idx >= 0 else None
            try:
                reach_idx = int(from_n) - 1
            except Exception:
                continue
            if reach_idx < 0 or reach_idx >= data.shape[1]:
                continue

            value = float(data[time_step, reach_idx])
            f = QgsFeature(self.animation_layer.fields())
            f.setGeometry(feature.geometry())
            f.setAttribute("FromN", str(from_n) if from_n is not None else "")
            f.setAttribute("ToN", str(to_n) if to_n is not None else "")
            f.setAttribute("value", value)
            features.append(f)

        if features:
            prov.addFeatures(features)
            self.animation_layer.updateExtents()

        # Build or reuse renderer once per variable/ramp/width using global data range
        if not hasattr(self, "_animation_renderer_variable"):
            self._animation_renderer_variable = None
            self._animation_renderer_ramp = None
            self._animation_renderer_width = None

        ramp_name = None
        line_width = 1.2
        try:
            ramp_name = self.results_viewer_dock.dyn_color_combo.currentText()
        except Exception:
            ramp_name = "Spectral"
        try:
            line_width = float(self.results_viewer_dock.dyn_width_spin.value())
        except Exception:
            line_width = 1.2

        needs_renderer = (
            self._animation_renderer_variable != variable
            or self._animation_renderer_ramp != ramp_name
            or self._animation_renderer_width != line_width
            or self.animation_layer.renderer() is None
        )

        if needs_renderer:
            symbol = QgsSymbol.defaultSymbol(self.animation_layer.geometryType())
            style = QgsStyle.defaultStyle()
            ramp = style.colorRamp(ramp_name) or style.defaultColorRamp()
            if ramp is None:
                ramp = style.defaultColorRamp()

            vmin, vmax = self.results_viewer_dock.data_ranges.get(
                variable,
                (np.nanmin(data), np.nanmax(data)),
            )
            if vmax == vmin:
                vmax = vmin + 1.0
            classes = 5
            step = (vmax - vmin) / classes
            ranges = []
            for i in range(classes):
                lower = vmin + i * step
                upper = vmin + (i + 1) * step if i < classes - 1 else vmax
                sym = symbol.clone()
                try:
                    if hasattr(sym, "setWidth"):
                        sym.setWidth(line_width)
                    elif hasattr(sym, "setSize"):
                        sym.setSize(line_width)
                except Exception:
                    pass
                if ramp:
                    t = i / max(classes - 1, 1)
                    sym.setColor(ramp.color(t))
                ranges.append(QgsRendererRange(lower, upper, sym, f"{lower:.3g}–{upper:.3g}"))

            renderer = QgsGraduatedSymbolRenderer("value", ranges)
            renderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)
            self.animation_layer.setRenderer(renderer)
            self._animation_renderer_variable = variable
            self._animation_renderer_ramp = ramp_name
            self._animation_renderer_width = line_width
        self.animation_layer.triggerRepaint()
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

    def on_save_config_requested(self, path):
        """Save current configuration to user-selected path."""
        config = self.collect_config()
        if config is None:
            return
        try:
            config.to_json(path)
            QMessageBox.information(
                self.iface.mainWindow(),
                "Configuration Saved",
                f"Saved configuration to:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Save Failed",
                str(e)
            )

    def on_load_config_requested(self, path):
        """Load parameters from a config JSON into the UI."""
        try:
            with open(path, "r") as f:
                data = json.load(f)
            cfg = DCascadeConfig(**data)
            self.apply_config_to_ui(cfg)
            QMessageBox.information(
                self.iface.mainWindow(),
                "Configuration Loaded",
                f"Loaded configuration from:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Load Failed",
                str(e)
            )

    def on_load_run_requested(self, path):
        """Attempt to extract config from a run results file and load it."""
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)

            config_dict = None
            if isinstance(data, dict):
                if "config" in data and isinstance(data["config"], dict):
                    config_dict = data["config"]
                elif "config_path" in data and Path(data["config_path"]).exists():
                    with open(data["config_path"], "r") as cf:
                        config_dict = json.load(cf)

            if config_dict is None:
                raise ValueError("No embedded config found in run file")

            cfg = DCascadeConfig(**config_dict)
            self.apply_config_to_ui(cfg)
            QMessageBox.information(
                self.iface.mainWindow(),
                "Configuration Loaded",
                f"Loaded configuration from run file:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self.iface.mainWindow(),
                "Load Failed",
                str(e)
            )

    def apply_config_to_ui(self, cfg: DCascadeConfig):
        """Populate parameter dock fields from a DCascadeConfig model."""
        pdock = self.parameters_dock
        if pdock is None:
            return

        # Paths
        pdock.csv_path.setText(cfg.paths.discharge_csv or "")
        pdock.output_name.setText(cfg.paths.output_name or "")
        pdock.output_dir.setText(cfg.paths.output_dir or "")

        # Sediment
        if hasattr(pdock, "min_phi"):
            pdock.min_phi.setValue(cfg.sediment.range[0])
        if hasattr(pdock, "max_phi"):
            pdock.max_phi.setValue(cfg.sediment.range[1])
        if hasattr(pdock, "n_classes"):
            pdock.n_classes.setValue(cfg.sediment.n_classes)
        if hasattr(pdock, "dep_layer"):
            pdock.dep_layer.setValue(cfg.sediment.deposit_layer_thickness)
        if hasattr(pdock, "act_layer"):
            pdock.act_layer.setText(str(cfg.sediment.active_layer_depth))

        # Time
        if hasattr(pdock, "timescale"):
            pdock.timescale.setValue(cfg.time.timescale)
        if hasattr(pdock, "ts_length"):
            pdock.ts_length.setValue(cfg.time.ts_length)

        # Physics combos are stored as "N: Name"; select by leading number
        self._select_combo_by_prefix(pdock.tr_cap, cfg.physics.transport_capacity_formula)
        self._select_combo_by_prefix(pdock.tr_part, cfg.physics.transport_partitioning)
        self._select_combo_by_prefix(pdock.flow_depth, cfg.physics.flow_depth_formula)
        self._select_combo_by_prefix(pdock.vel_formula, cfg.physics.velocity_formula)
        self._select_combo_by_prefix(pdock.slope_red, cfg.physics.slope_reduction)
        self._select_combo_by_prefix(pdock.width_calc, cfg.physics.width_calculation)

        if hasattr(pdock, "update_slope"):
            pdock.update_slope.setChecked(bool(cfg.physics.update_slope))

        # Options
        if hasattr(pdock, "save_dep"):
            idx = pdock.save_dep.findText(cfg.options.save_deposit_layer)
            if idx >= 0:
                pdock.save_dep.setCurrentIndex(idx)
        if hasattr(pdock, "round_param"):
            pdock.round_param.setValue(cfg.options.round_parameter)
        if hasattr(pdock, "force_pass"):
            pdock.force_pass.setChecked(bool(cfg.options.force_pass_external_inputs))

        # External inputs (best-effort for simple fields)
        if cfg.external_inputs and hasattr(pdock, "ext_inputs_dir"):
            pdock.ext_inputs_dir.setText(cfg.external_inputs.dir or "")
            if hasattr(pdock, "ext_inputs_npy"):
                pdock.ext_inputs_npy.setText(cfg.external_inputs.tensor_npy or "")
            if hasattr(pdock, "ext_inputs_csv") and cfg.external_inputs.csv_files:
                pdock.ext_inputs_csv.setText(cfg.external_inputs.csv_files[0] or "")

    def _select_combo_by_prefix(self, combo, value):
        """Select first entry whose text starts with 'value:'"""
        if combo is None:
            return
        target = f"{value}:"
        for i in range(combo.count()):
            if combo.itemText(i).startswith(target):
                combo.setCurrentIndex(i)
                return
    
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

