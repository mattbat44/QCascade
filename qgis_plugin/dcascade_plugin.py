"""
@brief D-CASCADE QGIS Plugin main class
@author D-CASCADE Team
"""

from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QFileDialog, QMenu, QToolButton
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis, QgsGraduatedSymbolRenderer, QgsSymbol, QgsStyle
from qgis.gui import QgsMapToolIdentifyFeature
import os
import sys
import json
from pathlib import Path
import numpy as np

# Add src folder to path for imports
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from json_serializer import load_from_json

from .compat import (
    QVariant,
    Qt_RightDockWidgetArea,
    Qt_BottomDockWidgetArea,
    Qt_Checked,
)
from .docks.parameters_dock import ParametersDock
from .docks.results_viewer_dock import ResultsViewerDock
from .core.config_manager import DCascadeConfig, PathsConfig, SedimentConfig, TimeConfig, PhysicsConfig, OptionsConfig, ExternalInputsConfig
from .core.runner_thread import RunnerThread

# Constants for connectivity curves
CONNECTIVITY_DATA_KEY = 'Direct connectivity [m^3]'
MIN_DISTANCE_THRESHOLD = 1e-6
CURVE_OFFSET_FACTOR = 0.3
BEZIER_CURVE_POINTS = 20
CONNECTIVITY_WIDTH_CLASSES = 8  # Number of width classes
CONNECTIVITY_MIN_WIDTH = 0.3  # Minimum line width in mm
CONNECTIVITY_MAX_WIDTH = 3.0  # Maximum line width in mm
CONNECTIVITY_COLOR = '#2E86AB'  # Single color for connectivity curves (blue)


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
        self.connectivity_layer = None  # Layer for connectivity curves
        
        # Layer and selection tracking
        self.network_layer = None
        self.selected_reach_id = None
        self.results_data = None
        self.current_time_step = 0
        self.animation_field = None  # Field name used for animation
        self.connectivity_enabled = False  # Toggle for connectivity curves
        self.connectivity_width_ranges = None  # Global width ranges for consistent animation
        
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
        self.iface.addDockWidget(Qt_RightDockWidgetArea, self.parameters_dock)
        self.parameters_dock.setVisible(False)  # Hide by default
        
        self.iface.addDockWidget(Qt_BottomDockWidgetArea, self.results_viewer_dock)
        self.results_viewer_dock.setVisible(False)  # Hide by default
        
        # Connect signals
        self.parameters_dock.layer_selected.connect(self.on_layer_selected)
        self.parameters_dock.external_input_added.connect(self.on_external_input_added)
        self.parameters_dock.run_requested.connect(self.run_simulation)
        self.parameters_dock.save_config_requested.connect(self.on_save_config_requested)
        self.parameters_dock.load_config_requested.connect(self.on_load_config_requested)
        self.parameters_dock.load_run_requested.connect(self.on_load_run_requested)
        
        self.results_viewer_dock.time_step_changed.connect(self.on_time_step_changed)
        #self.results_viewer_dock.reach_selected_for_graph.connect(self.graph_reach)
        self.results_viewer_dock.results_loaded.connect(self.on_results_loaded)
        self.results_viewer_dock.animation_settings_changed.connect(lambda: self.on_time_step_changed(self.current_time_step))
        if hasattr(self.results_viewer_dock, 'connectivity_check'):
            self.results_viewer_dock.connectivity_check.stateChanged.connect(self.on_connectivity_toggled)
        
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
            try:
                from qgis.core import QgsProject
                if not self.animation_layer.isValid():
                    self.animation_layer = None
                else:
                    QgsProject.instance().removeMapLayer(self.animation_layer.id())
                    self.animation_layer = None
            except (RuntimeError, AttributeError):
                # Layer already deleted by QGIS
                self.animation_layer = None
        
        # Remove connectivity curves layer if present
        if self.connectivity_layer:
            try:
                from qgis.core import QgsProject
                if not self.connectivity_layer.isValid():
                    self.connectivity_layer = None
                else:
                    QgsProject.instance().removeMapLayer(self.connectivity_layer.id())
                    self.connectivity_layer = None
            except (RuntimeError, AttributeError):
                # Layer already deleted by QGIS
                self.connectivity_layer = None
        
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
    
    _REQUIRED_LAYER_FIELDS = ['FromN', 'ToN']

    def _missing_required_fields(self, layer):
        """Return a list of required field names absent from *layer*."""
        field_names = [field.name() for field in layer.fields()]
        return [f for f in self._REQUIRED_LAYER_FIELDS if f not in field_names]

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
        
        # Pass layer to results viewer
        if self.results_viewer_dock:
            self.results_viewer_dock.set_network_layer(layer)
        
        # Log the selected layer; field validation is shown in the inputs tab
        # label and enforced when the user runs the simulation via collect_config.
        missing = self._missing_required_fields(layer)
        if missing:
            QgsMessageLog.logMessage(
                f"Network layer '{layer.name()}' is missing required fields: {', '.join(missing)}",
                "D-CASCADE",
                Qgis.Warning
            )
        else:
            QgsMessageLog.logMessage(
                f"Network layer selected: {layer.name()}",
                "D-CASCADE",
                Qgis.Info
            )
    
    def on_map_selection_changed(self):
        """Handle map canvas feature selection change.

        Responds to selections on either the animated layer or the original
        network layer, whichever is currently active / has selected features.
        """
        if self.network_layer is None:
            return

        # Prefer the animation layer when it has an active selection so that
        # users can select reaches directly on the animated layer and still
        # drive the plots.
        selected_features = []
        active_layer = None

        try:
            if (self.animation_layer is not None
                    and self.animation_layer.isValid()
                    and self.animation_layer.selectedFeatureCount() > 0):
                selected_features = self.animation_layer.selectedFeatures()
                active_layer = self.animation_layer
        except RuntimeError:
            # Underlying C++ object has been deleted; clean up reference
            self.animation_layer = None

        # Fall back to the original network layer
        if not selected_features:
            if self.network_layer.selectedFeatureCount() > 0:
                selected_features = self.network_layer.selectedFeatures()
                active_layer = self.network_layer

        if not selected_features:
            self.selected_reach_id = None
            self.parameters_dock.set_selected_reach(None)
            if self.results_viewer_dock:
                QgsMessageLog.logMessage("No reach selected", "D-CASCADE", Qgis.Info)
                #self.results_viewer_dock.graph_selected_reach(None)
            return

        from_n_idx = active_layer.fields().indexFromName('FromN')
        if from_n_idx < 0:
            return

        reach_ids = []
        for feature in selected_features:
            reach_ids.append(feature.attribute(from_n_idx))

        # Track first for params dock; pass all to results viewer
        self.selected_reach_id = reach_ids[0] if reach_ids else None
        self.parameters_dock.set_selected_reach(self.selected_reach_id)

        if self.results_viewer_dock and self.results_viewer_dock.results_data is not None:
            # results viewer handles tab check via from_map=True
            self.results_viewer_dock.graph_selected_reach(reach_ids, from_map=True)

            print(f"Selected reach(s) with FromN: {reach_ids} (via {'animation' if active_layer is self.animation_layer else 'network'} layer)")



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
    
    def on_connectivity_toggled(self, state):
        """Handle connectivity curves checkbox toggle."""
        enabled = (int(state) == int(Qt_Checked))  # Qt.Checked = 2
        self.toggle_connectivity_curves(enabled)

    def on_time_step_changed(self, time_step):
        """Handle time step change in results viewer - update layer symbology."""
        self.current_time_step = time_step
        
        if self.network_layer is None or self.results_viewer_dock.results_data is None:
            return
        
        # Update layer symbology based on current time step
        self.update_layer_symbology(time_step)
        
        # Update connectivity curves if enabled
        if self.connectivity_enabled:
            self.update_connectivity_curves(time_step)
    
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
    
    def update_connectivity_curves(self, time_step):
        """Update connectivity curves layer based on Direct connectivity data for given time step."""
        if self.network_layer is None:
            QgsMessageLog.logMessage("Cannot update connectivity: No network layer selected", "D-CASCADE", Qgis.Warning)
            return
        
        if self.results_viewer_dock.results_data is None:
            return
        
        # Check if Direct connectivity data exists
        if CONNECTIVITY_DATA_KEY not in self.results_viewer_dock.results_data:
            QgsMessageLog.logMessage(f"Cannot update connectivity: '{CONNECTIVITY_DATA_KEY}' not found in results", "D-CASCADE", Qgis.Warning)
            return
        
        direct_connectivity = self.results_viewer_dock.results_data[CONNECTIVITY_DATA_KEY]
        
        if time_step >= direct_connectivity.shape[0]:
            return
        
        from qgis.core import (
            QgsVectorLayer,
            QgsField,
            QgsFeature,
            QgsProject,
            QgsGeometry,
            QgsPoint,
            QgsLineString,
            QgsSymbol,
            QgsGraduatedSymbolRenderer,
            QgsRendererRange,
            QgsStyle
        )
        import numpy as np
        
        # Create or reuse connectivity layer
        if self.connectivity_layer is None:
            uri = "LineString?crs=" + self.network_layer.crs().authid()
            self.connectivity_layer = QgsVectorLayer(uri, "D-CASCADE Connectivity", "memory")
            prov = self.connectivity_layer.dataProvider()
            prov.addAttributes([
                QgsField("from_reach", QVariant.Int),
                QgsField("to_reach", QVariant.Int),
                QgsField("volume", QVariant.Double),
                QgsField("to_outlet", QVariant.Int),  # 1 if going to outlet, 0 otherwise
            ])
            self.connectivity_layer.updateFields()
            QgsProject.instance().addMapLayer(self.connectivity_layer)
            
            # Move connectivity layer above animation layer for visibility
            root = QgsProject.instance().layerTreeRoot()
            anim_node = root.findLayer(self.animation_layer.id()) if self.animation_layer else None
            conn_node = root.findLayer(self.connectivity_layer.id())
            if anim_node and conn_node:
                parent = anim_node.parent() or root
                conn_parent = conn_node.parent() or root
                try:
                    idx = parent.children().index(anim_node)
                    parent.insertChildNode(idx, conn_node.clone())
                    conn_parent.removeChildNode(conn_node)
                except (ValueError, AttributeError):
                    pass
        else:
            prov = self.connectivity_layer.dataProvider()
            prov.truncate()
        
        # Extract sediment transport data for given timestep
        transport_data = direct_connectivity[time_step, :, :-1]  # Sediment depositing in reaches
        qout_data = direct_connectivity[time_step, :, -1]  # Sediment passing the outlet
        
        # Build position map for reach centroids
        pos = {}
        reach_fromn = []
        from_n_idx = self.network_layer.fields().indexFromName('FromN')
        
        for feature in self.network_layer.getFeatures():
            from_n = feature.attribute(from_n_idx)
            geom = feature.geometry()
            if geom and not geom.isEmpty():
                centroid = geom.centroid().asPoint()
                pos[int(from_n)] = (centroid.x(), centroid.y())
                reach_fromn.append(int(from_n))
        
        reach_fromn = sorted(reach_fromn)
        
        # Find outlet reach (last reach in the network)
        # Identify outlet as reach with no downstream connection
        to_n_idx = self.network_layer.fields().indexFromName('ToN')
        outlet_coords = None
        outlet_fromn = None
        
        if to_n_idx >= 0:
            all_to_n = set()
            all_from_n = set()
            
            for feature in self.network_layer.getFeatures():
                from_n = feature.attribute(from_n_idx)
                to_n = feature.attribute(to_n_idx)
                if from_n is not None:
                    all_from_n.add(int(from_n))
                if to_n is not None and to_n != -1 and to_n != 0:
                    all_to_n.add(int(to_n))
            
            # Outlet is a node that is not in the to_n set
            potential_outlets = all_from_n - all_to_n
            if potential_outlets:
                outlet_fromn = max(potential_outlets)  # Use the largest FromN as outlet
                
                # Get the downstream end of the outlet reach
                for feature in self.network_layer.getFeatures():
                    from_n = feature.attribute(from_n_idx)
                    if from_n == outlet_fromn:
                        geom = feature.geometry()
                        if geom and not geom.isEmpty():
                            # Get the last point of the geometry
                            if geom.isMultipart():
                                parts = geom.asMultiPolyline()
                                if parts:
                                    outlet_coords = parts[-1][-1]
                            else:
                                line = geom.asPolyline()
                                if line:
                                    outlet_coords = line[-1]
                        break
        
        # Generate arc features
        features = []
        
        # Arcs between reaches
        for i in range(transport_data.shape[0]):
            for j in range(transport_data.shape[1]):
                volume = transport_data[i, j]
                if volume > 0:
                    start_reach = reach_fromn[i] if i < len(reach_fromn) else None
                    dest_reach = reach_fromn[j] if j < len(reach_fromn) else None
                    
                    if start_reach is not None and dest_reach is not None:
                        if start_reach in pos and dest_reach in pos:
                            start_pos = pos[start_reach]
                            dest_pos = pos[dest_reach]
                            
                            # Create curved line geometry
                            line_geom = self._create_arc_geometry(start_pos, dest_pos, -0.6)
                            
                            f = QgsFeature(self.connectivity_layer.fields())
                            f.setGeometry(line_geom)
                            f.setAttribute("from_reach", start_reach)
                            f.setAttribute("to_reach", dest_reach)
                            f.setAttribute("volume", float(volume))
                            f.setAttribute("to_outlet", 0)
                            features.append(f)
        
        # Arcs to outlet
        if outlet_coords is not None:
            for i, vol in enumerate(qout_data):
                if vol > 0:
                    reach_id = reach_fromn[i] if i < len(reach_fromn) else None
                    if reach_id is not None and reach_id in pos:
                        start_pos = pos[reach_id]
                        dest_pos = (outlet_coords.x(), outlet_coords.y())
                        
                        # Create curved line geometry with opposite curvature
                        line_geom = self._create_arc_geometry(start_pos, dest_pos, 0.35)
                        
                        f = QgsFeature(self.connectivity_layer.fields())
                        f.setGeometry(line_geom)
                        f.setAttribute("from_reach", reach_id)
                        f.setAttribute("to_reach", -1)  # -1 indicates outlet
                        f.setAttribute("volume", float(vol))
                        f.setAttribute("to_outlet", 1)
                        features.append(f)
        
        if features:
            prov.addFeatures(features)
            self.connectivity_layer.updateExtents()
        
        # Calculate or reuse global width ranges for consistent animation
        if self.connectivity_width_ranges is None:
            self.connectivity_width_ranges = self._calculate_global_width_ranges()
        
        # Apply width-based graduated symbology
        if self.connectivity_width_ranges:
            from qgis.PyQt.QtGui import QColor
            
            symbol = QgsSymbol.defaultSymbol(self.connectivity_layer.geometryType())
            base_color = QColor(CONNECTIVITY_COLOR)
            
            ranges = []
            for i, (lower, upper, width) in enumerate(self.connectivity_width_ranges):
                sym = symbol.clone()
                
                # Set width based on class
                try:
                    if hasattr(sym, "setWidth"):
                        sym.setWidth(width)
                except Exception:
                    pass
                
                # Use consistent color for all classes
                sym.setColor(base_color)
                
                # Format label based on magnitude
                if lower < 0.01:
                    label = f"{lower:.2e}–{upper:.2e} m³"
                elif lower < 1:
                    label = f"{lower:.3f}–{upper:.3f} m³"
                elif lower < 1000:
                    label = f"{lower:.1f}–{upper:.1f} m³"
                else:
                    label = f"{lower:.2g}–{upper:.2g} m³"
                
                ranges.append(QgsRendererRange(lower, upper, sym, label))
            
            renderer = QgsGraduatedSymbolRenderer("volume", ranges)
            renderer.setMode(QgsGraduatedSymbolRenderer.Custom)
            self.connectivity_layer.setRenderer(renderer)
        
        self.connectivity_layer.triggerRepaint()
        self.canvas.refresh()
    
    def _calculate_global_width_ranges(self):
        """Calculate global width ranges from all timesteps for consistent animation.
        
        Returns:
            List of tuples (lower_bound, upper_bound, width_mm) for each class,
            or None if data not available.
        """
        if self.results_viewer_dock.results_data is None:
            return None
        
        if CONNECTIVITY_DATA_KEY not in self.results_viewer_dock.results_data:
            return None
        
        import numpy as np
        
        direct_connectivity = self.results_viewer_dock.results_data[CONNECTIVITY_DATA_KEY]
        
        # Get all non-zero volumes across all timesteps
        all_volumes = direct_connectivity[direct_connectivity > 0]
        
        if len(all_volumes) == 0:
            return None
        
        # Use logarithmic scale for better distribution
        vmin = max(1e-6, np.min(all_volumes))
        vmax = np.max(all_volumes)
        
        log_min = np.log10(vmin)
        log_max = np.log10(vmax)
        log_step = (log_max - log_min) / CONNECTIVITY_WIDTH_CLASSES
        
        # Calculate width range
        width_step = (CONNECTIVITY_MAX_WIDTH - CONNECTIVITY_MIN_WIDTH) / CONNECTIVITY_WIDTH_CLASSES
        
        ranges = []
        for i in range(CONNECTIVITY_WIDTH_CLASSES):
            lower = 10 ** (log_min + i * log_step)
            upper = 10 ** (log_min + (i + 1) * log_step) if i < CONNECTIVITY_WIDTH_CLASSES - 1 else vmax
            width = CONNECTIVITY_MIN_WIDTH + (i + 1) * width_step  # Width increases with class
            ranges.append((lower, upper, width))
        
        return ranges
    
    def _create_arc_geometry(self, start_pos, end_pos, curvature):
        """Create a curved arc geometry between two points using Bezier curve approximation.
        
        Args:
            start_pos: Tuple (x, y) for start point
            end_pos: Tuple (x, y) for end point
            curvature: Curvature factor (positive curves right, negative curves left)
        
        Returns:
            QgsGeometry: Line geometry representing the arc
        """
        from qgis.core import QgsGeometry, QgsPoint, QgsLineString
        import math
        
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Calculate midpoint
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        # Calculate perpendicular offset for control point
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx**2 + dy**2)
        
        if length < MIN_DISTANCE_THRESHOLD:
            # Points are too close, return straight line
            points = [QgsPoint(x1, y1), QgsPoint(x2, y2)]
            return QgsGeometry(QgsLineString(points))
        
        # Perpendicular direction (rotated 90 degrees)
        perp_x = -dy / length
        perp_y = dx / length
        
        # Control point offset
        offset = curvature * length * CURVE_OFFSET_FACTOR
        ctrl_x = mid_x + perp_x * offset
        ctrl_y = mid_y + perp_y * offset
        
        # Generate points along quadratic Bezier curve
        points = []
        for i in range(BEZIER_CURVE_POINTS + 1):
            t = i / BEZIER_CURVE_POINTS
            # Quadratic Bezier formula: B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2
            s = 1 - t
            x = s*s*x1 + 2*s*t*ctrl_x + t*t*x2
            y = s*s*y1 + 2*s*t*ctrl_y + t*t*y2
            points.append(QgsPoint(x, y))
        
        return QgsGeometry(QgsLineString(points))
    
    def toggle_connectivity_curves(self, enabled):
        """Toggle visibility of connectivity curves."""
        self.connectivity_enabled = enabled
        
        if enabled:
            # Recalculate width ranges when enabling
            self.connectivity_width_ranges = None
            # Show connectivity layer and update it
            if self.connectivity_layer:
                self.connectivity_layer.setVisible(True)
            self.update_connectivity_curves(self.current_time_step)
        else:
            # Hide connectivity layer
            if self.connectivity_layer:
                self.connectivity_layer.setVisible(False)
        
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
            
            QgsMessageLog.logMessage(
                "Simulation started in background. Check the QGIS message log for progress.",
                "D-CASCADE",
                Qgis.Info
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
        
        # Validate that the chosen layer has the required fields
        missing = self._missing_required_fields(layer)
        if missing:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Missing Fields",
                f"The selected layer '{layer.name()}' is missing required fields: {', '.join(missing)}"
            )
            return None
        
        layer_path = layer.source()
        
        # Paths
        paths = PathsConfig(
            river_network_shp=layer_path,
            discharge_csv=self.parameters_dock.csv_path.text(),
            output_name=self.parameters_dock.output_name.text(),
            output_dir=self.parameters_dock.output_dir.text() or None,
            overbank_q_csv=getattr(self.parameters_dock, "overbank_csv_path", None) and self.parameters_dock.overbank_csv_path.text() or None,
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
            QgsMessageLog.logMessage(
                f"Configuration saved to:\n{path}",
                "D-CASCADE",
                Qgis.Info
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
            QgsMessageLog.logMessage(
                f"Configuration loaded from:\n{path}",
                "D-CASCADE",
                Qgis.Info
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
            data = load_from_json(path)

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
            QgsMessageLog.logMessage(
                f"Configuration loaded from run file:\n{path}",
                "D-CASCADE",
                Qgis.Info
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
        if hasattr(pdock, "overbank_csv_path"):
            pdock.overbank_csv_path.setText(getattr(cfg.paths, "overbank_q_csv", "") or "")

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
            QgsMessageLog.logMessage(
                msg,
                "D-CASCADE",
                Qgis.Info
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
                results_path = Path(output_dir) / f"{output_name}.json"
            else:
                results_path = Path.cwd() / output_dir / f"{output_name}.json"
            
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

