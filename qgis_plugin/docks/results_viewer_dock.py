"""
@brief Dock widget for viewing and analyzing D-CASCADE simulation results
@author D-CASCADE Team
"""

from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox,
    QFileDialog, QTabWidget
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.core import Qgis, QgsMessageLog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import sys
import numpy as np
from pathlib import Path

# Add src folder to path for imports
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from json_serializer import load_from_json, save_to_json

from .results_viewer.time_series_tab import TimeSeriesTab
from .results_viewer.spatial_tab import SpatialTab
from .results_viewer.connectivity_tab import ConnectivityTab
from .results_viewer.long_profile_tab import LongProfileTab
from .results_viewer.animation_tab import AnimationTab
from .results_viewer.stats_tab import StatsTab


class ResultsViewerDock(QDockWidget):
    """Advanced results viewer with multiple visualization options."""
    
    time_step_changed = pyqtSignal(int)  # Emitted when time slider changes
    reach_selected_for_graph = pyqtSignal(int)  # Emitted when user wants to graph a reach
    results_loaded = pyqtSignal()  # Emitted when results are successfully loaded
    animation_settings_changed = pyqtSignal()  # Emitted when ramp/width/variable changes
    pane_state_changed = pyqtSignal(str, dict)  # Emitted with (pane_name, state_dict)
    
    def __init__(self, parent=None):
        super().__init__("Results Viewer", parent)
        
        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(8, 8, 8, 8)

        self.main_window = self._resolve_main_window(parent)
        self.canvas_dock = None
        
        self.results_data = None
        self.results_data_ext = None
        self.results_path = None
        self.reach_data = None
        self.network_layer = None
        self.selected_reaches = []
        self.data_ranges = {}
        
        self.init_ui()
        self.setWidget(self.container)
        self._init_canvas_dock()

    def set_network_layer(self, layer):
        """Set the network layer for topology queries."""
        self.network_layer = layer

    def _resolve_main_window(self, candidate):
        """Best-effort helper to find the QMainWindow to attach secondary docks."""
        if candidate and hasattr(candidate, "addDockWidget"):
            return candidate
        return None

    def _init_canvas_dock(self):
        """Create a separate dock to host the matplotlib canvas."""
        if not self.main_window:
            return

        self.canvas_dock = QDockWidget("Results Plot", self.main_window)
        self.canvas_dock.setObjectName("DCascadeResultsPlotDock")
        self.canvas_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        # Container so we can include toolbar + canvas
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(12, 12, 12, 12)
        vbox.addWidget(self.toolbar)
        vbox.addWidget(self.canvas)
        self.canvas_dock.setWidget(container)
        self.main_window.addDockWidget(Qt.BottomDockWidgetArea, self.canvas_dock)
        self.canvas_dock.hide()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("Load Results (.json)")
        self.load_btn.clicked.connect(self.load_results)
        toolbar_layout.addWidget(self.load_btn)

        self.load_q_btn = QPushButton("Load Discharge CSV")
        self.load_q_btn.setToolTip(
            "Load a discharge CSV (rows = time steps, columns = reaches) and add it as "
            "'Discharge [m^3/s]' to the current results so it can be plotted."
        )
        self.load_q_btn.clicked.connect(self.load_discharge_csv)
        toolbar_layout.addWidget(self.load_q_btn)

        toolbar_layout.addStretch()

        self.show_graph_btn = QPushButton("Show Graph")
        self.show_graph_btn.setToolTip("Open the graph panel to view plots.")
        self.show_graph_btn.clicked.connect(self.show_plot_dock)
        toolbar_layout.addWidget(self.show_graph_btn)
        
        self.main_layout.addLayout(toolbar_layout)
        
        # Info label
        self.info_label = QLabel("No results loaded. Run a simulation or load a .json file.")
        self.main_layout.addWidget(self.info_label)
        
        # Tabs for different visualization types
        self.tab_widget = QTabWidget()
        
        # Create tab components
        self.time_series_tab = TimeSeriesTab(self)
        self.spatial_tab = SpatialTab(self)
        self.connectivity_tab = ConnectivityTab(self)
        self.long_profile_tab = LongProfileTab(self)
        self.animation_tab = AnimationTab(self)
        self.stats_tab = StatsTab(self)
        
        # Add tabs to widget
        self.tab_widget.addTab(self.time_series_tab, "Time Series")
        self.tab_widget.addTab(self.spatial_tab, "Spatial Analysis")
        self.tab_widget.addTab(self.connectivity_tab, "Connectivity")
        self.tab_widget.addTab(self.long_profile_tab, "Long Profile")
        self.tab_widget.addTab(self.animation_tab, "Animation")
        self.tab_widget.addTab(self.stats_tab, "Statistics")
        
        self.main_layout.addWidget(self.tab_widget)

        # Matplotlib canvas for plotting (hosted in its own dock)
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setContextMenuPolicy(Qt.CustomContextMenu)
        self.canvas.customContextMenuRequested.connect(self._show_canvas_menu)
        # Basic navigation toolbar for saving/zooming on right-click menu
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # Connect signals from tabs
        self.time_series_tab.ts_variable_combo.currentTextChanged.connect(self.update_time_series_plot)
        self.time_series_tab.ts_reach_combo.currentIndexChanged.connect(self.update_time_series_plot)
        self.time_series_tab.ts_multi_check.stateChanged.connect(self.update_time_series_plot)
        self.time_series_tab.ts_grain_size_check.stateChanged.connect(self.update_time_series_plot)
        self.time_series_tab.plot_btn.clicked.connect(self.update_time_series_plot)
        
        self.spatial_tab.spatial_variable_combo.currentTextChanged.connect(self.update_spatial_plot)
        self.spatial_tab.spatial_agg_combo.currentTextChanged.connect(self.update_spatial_plot)
        self.spatial_tab.spatial_year_spin.valueChanged.connect(self.update_spatial_plot)
        self.spatial_tab.spatial_yearly_check.stateChanged.connect(self.update_spatial_plot)
        self.spatial_tab.plot_btn.clicked.connect(self.update_spatial_plot)

        # Connect signals from other tabs
        self.connectivity_tab.conn_variable_combo.currentTextChanged.connect(self.update_connectivity_plot)
        self.connectivity_tab.plot_btn.clicked.connect(self.update_connectivity_plot)
        
        self.long_profile_tab.lp_update_btn.clicked.connect(lambda: self.update_long_profile_plot(use_slider=False))
        self.long_profile_tab.lp_time_slider.valueChanged.connect(self.on_lp_time_slider_changed)
        
        self.animation_tab.dyn_variable_combo.currentTextChanged.connect(self._on_animation_setting_changed)
        self.animation_tab.dyn_color_combo.currentTextChanged.connect(self._on_animation_setting_changed)
        self.animation_tab.dyn_width_spin.valueChanged.connect(self._on_animation_setting_changed)
        self.animation_tab.time_slider.valueChanged.connect(self.on_time_slider_changed)
        self.animation_tab.play_btn.clicked.connect(self.animate_results)
        self.animation_tab.frame_duration_spin.valueChanged.connect(self._on_animation_setting_changed)

        # Refresh the appropriate plot whenever the user switches tabs
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Expose commonly accessed widgets for backward compatibility
        self.ts_variable_combo = self.time_series_tab.ts_variable_combo
        self.ts_reach_combo = self.time_series_tab.ts_reach_combo
        self.ts_multi_check = self.time_series_tab.ts_multi_check
        self.ts_grain_size_check = self.time_series_tab.ts_grain_size_check
        self.spatial_variable_combo = self.spatial_tab.spatial_variable_combo
        self.spatial_agg_combo = self.spatial_tab.spatial_agg_combo
        self.spatial_year_spin = self.spatial_tab.spatial_year_spin
        self.spatial_yearly_check = self.spatial_tab.spatial_yearly_check
        self.conn_variable_combo = self.connectivity_tab.conn_variable_combo
        self.lp_update_btn = self.long_profile_tab.lp_update_btn
        self.lp_time_slider = self.long_profile_tab.lp_time_slider
        self.lp_time_label = self.long_profile_tab.lp_time_label
        self.dyn_variable_combo = self.animation_tab.dyn_variable_combo
        self.dyn_color_combo = self.animation_tab.dyn_color_combo
        self.dyn_width_spin = self.animation_tab.dyn_width_spin
        self.time_slider = self.animation_tab.time_slider
        self.time_label = self.animation_tab.time_label
        self.play_btn = self.animation_tab.play_btn
        self.frame_duration_spin = self.animation_tab.frame_duration_spin
        self.connectivity_check = self.animation_tab.connectivity_check
        self.stats_label = self.stats_tab.stats_label

        self.show_empty_plot()

    def current_tab_name(self):
        """Get the name of the currently active tab."""
        return self.tab_widget.tabText(self.tab_widget.currentIndex())

    def _on_tab_changed(self, index):
        """Refresh the plot for the newly activated tab."""
        if self.results_data is None:
            return
        tab = self.tab_widget.tabText(index)
        if tab == "Time Series":
            self.update_time_series_plot()
        elif tab == "Animation":
            self.update_dynamic_plot()
        elif tab == "Spatial Analysis":
            self.update_spatial_plot()
        elif tab == "Connectivity":
            self.update_connectivity_plot()
        elif tab == "Long Profile":
            self.update_long_profile_plot(use_slider=True)

    def show_plot_dock(self):
        """Explicitly show the plot dock (used when user opens Results)."""
        if self.canvas_dock:
            if self.results_data is None:
                self.show_empty_plot()
            self.canvas_dock.show()

    def show_empty_plot(self):
        """Show empty plot message when no results are loaded."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(
            0.5,
            0.5,
            "Load simulation results to visualize",
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
            fontsize=16,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        self._apply_plot_margins()
        self.canvas.draw()
        if self.canvas_dock:
            self.canvas_dock.hide()

    def _load_with_fallback(self, file_path):
        """Load results, falling back to legacy pickle if needed.

        Also offers optional conversion of legacy pickle files to JSON.
        """
        try:
            return load_from_json(file_path)
        except Exception:
            # Try legacy pickle load
            try:
                import pickle

                with open(file_path, "rb") as f:
                    data = pickle.load(f)

                # Ask user to convert
                reply = QMessageBox.question(
                    self,
                    "Legacy File Detected",
                    f"The file '{Path(file_path).name}' appears to be in a legacy binary format (pickle).\n\n"
                    "Would you like to convert it to the new JSON format for better compatibility?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if reply == QMessageBox.Yes:
                    try:
                        p = Path(file_path)
                        if p.suffix == ".json":
                            new_path = p
                        else:
                            new_path = p.with_suffix(".json")

                        save_to_json(data, new_path)
                        QMessageBox.information(
                            self,
                            "Success",
                            f"Converted and saved to:\n{new_path}",
                        )
                    except Exception as save_err:
                        QMessageBox.warning(
                            self,
                            "Conversion Failed",
                            f"Could not save JSON: {save_err}",
                        )

                return data
            except Exception:
                # Re-raise so caller can handle
                raise

    def load_results(self):
        """Load results from a JSON file chosen by the user."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Results File",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if not file_path:
            return

        try:
            self.results_data = self._load_with_fallback(file_path)

            # Try to load extended results
            p = Path(file_path)
            ext_candidates = [
                p.with_name(p.stem + "_ext.json"),
                p.with_name(p.stem + "_ext.p"),
            ]

            self.results_data_ext = None
            for ext_path in ext_candidates:
                if ext_path.exists():
                    try:
                        self.results_data_ext = self._load_with_fallback(str(ext_path))
                        break
                    except Exception:
                        continue

            self.results_path = file_path

            # Update UI and notify listeners
            self.update_ui_with_results()

            msg = (
                f"Loaded results from {Path(file_path).name}\n"
                f"Available variables: {len(self.results_data)} fields"
            )
            if self.results_data_ext:
                msg += "\nExtended results loaded."

            QgsMessageLog.logMessage(msg, "D-CASCADE", Qgis.Info)
            self.results_loaded.emit()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load results: {str(e)}")

    def load_results_from_path(self, path):
        """Load results from a specific path (called externally)."""
        p = Path(path)
        if not p.exists():
            return

        try:
            self.results_data = self._load_with_fallback(str(p))

            # Try to load extended results
            ext_candidates = [
                p.with_name(p.stem + "_ext.json"),
                p.with_name(p.stem + "_ext.p"),
            ]

            self.results_data_ext = None
            for ext_path in ext_candidates:
                if ext_path.exists():
                    try:
                        self.results_data_ext = self._load_with_fallback(str(ext_path))
                        break
                    except Exception:
                        continue

            self.results_path = str(p)
            self.update_ui_with_results()
            self.results_loaded.emit()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load results: {str(e)}")

    def load_discharge_csv(self):
        """Load a discharge CSV file and add it to the current results as 'Discharge [m^3/s]'.

        The CSV must have rows = time steps and columns = reaches (one column per reach,
        ordered the same as the reach IDs in the loaded results).
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Discharge CSV", "", "CSV files (*.csv);;All files (*)"
        )
        if not file_path:
            return

        try:
            import pandas as pd
            df = pd.read_csv(file_path, header=None)
            # Drop any header row that is non-numeric
            try:
                df = df.apply(pd.to_numeric, errors='coerce')
                df = df.dropna(how='all')
            except Exception:
                pass
            q_array = df.values.astype(float)

            if self.results_data is None:
                self.results_data = {}

            self.results_data['Discharge [m^3/s]'] = q_array

            # Refresh data ranges and UI
            if q_array.size > 0:
                self.data_ranges['Discharge [m^3/s]'] = (float(np.nanmin(q_array)), float(np.nanmax(q_array)))

            # Rebuild reach IDs if not already set
            if not self.reach_ids and q_array.ndim == 2:
                n = q_array.shape[1]
                self.reach_ids = [str(i + 1) for i in range(n)]
                self.reach_id_map = {str(i + 1): i for i in range(n)}
                self.ts_reach_combo.clear()
                for rid in self.reach_ids:
                    self.ts_reach_combo.addItem(f"Reach {rid}")
                self.ts_reach_combo.setEnabled(True)

            # Enable time slider if not already
            if q_array.ndim == 2 and not self.time_slider.isEnabled():
                num_timesteps = q_array.shape[0]
                self.time_slider.setMaximum(num_timesteps - 1)
                self.time_slider.setEnabled(True)
                self.time_label.setText(f"0 / {num_timesteps - 1}")
                self.play_btn.setEnabled(True)

            QgsMessageLog.logMessage(
                f"Loaded discharge CSV: {Path(file_path).name} ({q_array.shape})",
                "D-CASCADE", Qgis.Info
            )
            self.info_label.setText(
                (self.info_label.text().rstrip() +
                 f" | Q loaded: {Path(file_path).name}")
            )
            # Switch to Time Series tab on the Discharge variable and refresh
            idx = self.ts_variable_combo.findText("Discharge [m^3/s]")
            if idx >= 0:
                self.ts_variable_combo.setCurrentIndex(idx)
            self.tab_widget.setCurrentIndex(0)
            self.update_time_series_plot()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load discharge CSV: {str(e)}")

    def update_ui_with_results(self):
        """Update controls and cached metadata after loading results."""
        if self.results_data is None:
            return

        # Update info label
        available_vars = list(self.results_data.keys())
        self.info_label.setText(
            f"Loaded: {Path(self.results_path).name if self.results_path else 'Unknown'} | "
            f"Variables: {len(available_vars)}"
        )

        # Cache data ranges for dynamic plots
        self.data_ranges = {}
        for name, arr in self.results_data.items():
            if isinstance(arr, np.ndarray) and arr.size > 0:
                self.data_ranges[name] = (np.nanmin(arr), np.nanmax(arr))

        # Build reach ID map
        self.reach_ids = []
        self.reach_id_map = {}

        if "reach_id" in self.results_data:
            r_ids = self.results_data["reach_id"]
            if isinstance(r_ids, np.ndarray):
                r_ids = r_ids.tolist()
            self.reach_ids = [str(x) for x in r_ids]
            self.reach_id_map = {str(x): i for i, x in enumerate(r_ids)}
        else:
            inferred = False
            if self.network_layer:
                try:
                    from_n_idx = self.network_layer.fields().indexFromName("FromN")
                    # Use the first 2-D result array to determine expected reach count
                    _ref_key = next(
                        (k for k in ("Volume out [m^3]", "Discharge [m^3/s]")
                         if k in self.results_data and isinstance(self.results_data[k], np.ndarray)
                         and self.results_data[k].ndim == 2),
                        None,
                    )
                    if from_n_idx >= 0 and _ref_key is not None:
                        from_ns = []
                        for f in self.network_layer.getFeatures():
                            val = f.attribute(from_n_idx)
                            if val is not None:
                                from_ns.append(int(val))
                        sorted_ids = sorted(from_ns)
                        if len(sorted_ids) == self.results_data[_ref_key].shape[1]:
                            self.reach_ids = [str(x) for x in sorted_ids]
                            self.reach_id_map = {
                                str(x): i for i, x in enumerate(sorted_ids)
                            }
                            inferred = True
                            QgsMessageLog.logMessage(
                                "Inferred reach IDs from network layer.",
                                "D-CASCADE",
                                Qgis.Info,
                            )
                except Exception as e:
                    QgsMessageLog.logMessage(
                        f"Could not infer IDs: {e}", "D-CASCADE", Qgis.Warning
                    )

            # Determine n_reaches from the first available 2-D array
            _ref_key = next(
                (k for k in ("Volume out [m^3]", "Discharge [m^3/s]")
                 if k in self.results_data and isinstance(self.results_data[k], np.ndarray)
                 and self.results_data[k].ndim == 2),
                None,
            )
            if not inferred and _ref_key is not None:
                num_reaches = self.results_data[_ref_key].shape[1]
                self.reach_ids = [str(i + 1) for i in range(num_reaches)]
                self.reach_id_map = {str(i + 1): i for i in range(num_reaches)}

        # Update reach selector and time slider for time series
        # Use Volume out as the canonical shape source; fall back to Discharge if absent
        _shape_key = None
        for _candidate in ("Volume out [m^3]", "Discharge [m^3/s]"):
            if _candidate in self.results_data and isinstance(self.results_data[_candidate], np.ndarray):
                _shape_key = _candidate
                break
        if _shape_key:
            self.ts_reach_combo.clear()
            for rid in self.reach_ids:
                self.ts_reach_combo.addItem(f"Reach {rid}")
            self.ts_reach_combo.setEnabled(True)

            num_timesteps = self.results_data[_shape_key].shape[0]
            self.time_slider.setMaximum(num_timesteps - 1)
            self.time_slider.setEnabled(True)
            self.time_label.setText(f"0 / {num_timesteps - 1}")
            self.play_btn.setEnabled(True)

        # Populate statistics variable list
        if hasattr(self, "stats_tab"):
            self.stats_tab.var_combo.clear()
            all_vars = []
            if self.results_data:
                all_vars.extend(
                    sorted(
                        [
                            k
                            for k, v in self.results_data.items()
                            if isinstance(v, np.ndarray)
                        ]
                    )
                )
            if self.results_data_ext:
                all_vars.extend(
                    sorted(
                        [
                            k
                            for k, v in self.results_data_ext.items()
                            if isinstance(v, np.ndarray)
                        ]
                    )
                )
            self.stats_tab.var_combo.addItems(all_vars)

        # Generate an initial plot
        self.update_time_series_plot()

    def on_time_slider_changed(self, value):
        """Handle time slider change from the animation tab."""
        self.time_step_changed.emit(value)
        self.update_dynamic_plot()

    def _on_animation_setting_changed(self, *_):
        """Emit setting change and refresh current timestep."""
        self.animation_settings_changed.emit()
        self.on_time_slider_changed(self.time_slider.value())
        if hasattr(self, 'animation_timer') and self.animation_timer.isActive():
            self.animation_timer.setInterval(self.frame_duration_spin.value())
    
    def update_time_series_plot(self):
        """Update time series plot based on selections."""
        if self.results_data is None:
            return
        
        try:
            variable = self.ts_variable_combo.currentText()
            
            # Handle Grain Size Breakdown
            if hasattr(self, 'ts_grain_size_check') and self.ts_grain_size_check.isChecked():
                if self.results_data_ext is None:
                    QMessageBox.warning(self, "Warning", "Extended results (_ext.p) not found. Cannot show grain size breakdown.")
                    self.ts_grain_size_check.setChecked(False)
                else:
                    # Map variable to extended key
                    ext_key = None
                    if variable == 'Volume out [m^3]':
                        ext_key = 'Volume out per grain sizes [m^3]'
                    elif variable == 'Transport capacity [m^3]':
                        ext_key = 'Tr_cap per class [m^3]'
                    elif variable == 'Volume in [m^3]':
                        ext_key = 'Volume in per grain sizes [m^3]'
                    elif variable == 'Sediment budget [m^3]':
                        ext_key = 'Sediment budget per class [m^3]'
                    
                    if ext_key and ext_key in self.results_data_ext:
                        data_ext = self.results_data_ext[ext_key]
                        # data_ext shape: (time, reach, classes)
                        
                        reach_idx = self.ts_reach_combo.currentIndex()
                        if reach_idx >= 0 and reach_idx < data_ext.shape[1]:
                            self.figure.clear()
                            ax = self.figure.add_subplot(111)
                            
                            y_data = []
                            labels = []
                            num_classes = data_ext.shape[2]
                            
                            # Try to get psi from results if available
                            psi_labels = [f"Class {i+1}" for i in range(num_classes)]
                            psi = None
                            if 'psi' in self.results_data:
                                psi = self.results_data['psi']
                            elif 'Simulation parameters' in self.results_data and 'psi' in self.results_data['Simulation parameters']:
                                psi = self.results_data['Simulation parameters']['psi']
                                
                            if psi is not None and len(psi) == num_classes:
                                psi_labels = [f"Psi {p:.1f}" for p in psi]

                            for i in range(num_classes):
                                y_data.append(data_ext[:, reach_idx, i])
                            
                            ax.stackplot(range(data_ext.shape[0]), *y_data, labels=psi_labels)
                            
                            ax.set_title(f"{variable} - Grain Size Breakdown - Reach {reach_idx+1}")
                            ax.set_xlabel("Time Step")
                            ax.set_ylabel(variable)
                            ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
                            self._apply_plot_margins()
                            self.canvas.draw()
                            if self.canvas_dock:
                                self.canvas_dock.show()
                            return
                    else:
                         QMessageBox.warning(self, "Warning", f"Extended data for {variable} not available.")

            # Handle Elevation (Upstream/Downstream)
            if variable.startswith('Elevation'):
                if self.results_data_ext is None or 'Node_el [m]' not in self.results_data_ext:
                    QMessageBox.warning(self, "Warning", "Extended results with 'Node_el [m]' required for elevation plots.")
                    return
                
                node_el = self.results_data_ext['Node_el [m]']
                # node_el shape: (time, nodes)
                
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                
                reach_list = []
                if self.selected_reaches:
                    for rid in self.selected_reaches:
                        if rid in self.reach_id_map:
                            reach_list.append(self.reach_id_map[rid])
                
                if not reach_list:
                    reach_list = [self.ts_reach_combo.currentIndex()] if self.ts_reach_combo.count() else []
                
                for idx in reach_list:
                    # Assumption: Reach i starts at Node i
                    node_idx = idx
                    if 'Downstream' in variable:
                        node_idx = idx + 1
                        if node_idx >= node_el.shape[1]:
                            node_idx = idx # Fallback
                    
                    if 0 <= node_idx < node_el.shape[1]:
                        y_vals = node_el[:, node_idx]
                        
                        if 'Change' in variable:
                            # Calculate change relative to initial time step
                            y_vals = y_vals - y_vals[0]
                            label_suffix = "Change"
                        else:
                            label_suffix = ""
                            
                        rid_label = self.reach_ids[idx] if idx < len(self.reach_ids) else str(idx+1)
                        ax.plot(y_vals, label=f'Reach {rid_label} {label_suffix}', linewidth=2)
                
                ax.set_title(f"{variable} - Time Series")
                ax.set_xlabel("Time Step")
                ax.set_ylabel("Elevation [m]" if 'Change' not in variable else "Elevation Change [m]")
                ax.legend()
                ax.grid(True, alpha=0.3)
                self._apply_plot_margins()
                self.canvas.draw()
                if self.canvas_dock:
                    self.canvas_dock.show()
                # Emit pane state for listeners
                try:
                    self.pane_state_changed.emit(
                        "time_series",
                        {
                            "variable": variable,
                            "mode": "grain_size",
                            "reach_index": reach_idx,
                        },
                    )
                except Exception:
                    pass
                try:
                    self.pane_state_changed.emit(
                        "time_series",
                        {
                            "variable": variable,
                            "mode": "elevation",
                            "reaches": reach_list,
                        },
                    )
                except Exception:
                    pass
                return

            if variable not in self.results_data:
                self.show_empty_plot()
                return
            
            data = self.results_data[variable]
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            reach_list = []
            if self.selected_reaches:
                # Map FromN values to indices using reach_id_map
                for rid in self.selected_reaches:
                    if rid in self.reach_id_map:
                        reach_list.append(self.reach_id_map[rid])
            
            if not reach_list:
                if self.ts_multi_check.isChecked():
                    reach_list = list(range(min(10, data.shape[1])))
                else:
                    reach_list = [self.ts_reach_combo.currentIndex()] if self.ts_reach_combo.count() else []

            for idx in reach_list:
                if 0 <= idx < data.shape[1]:
                    rid_label = self.reach_ids[idx] if idx < len(self.reach_ids) else str(idx+1)
                    ax.plot(data[:, idx], label=f'Reach {rid_label}', linewidth=2)
            
            ax.set_title(f"{variable} - Time Series")
            ax.set_xlabel("Time Step")
            ax.set_ylabel(variable)
            ax.legend()
            ax.grid(True, alpha=0.3)
            self._apply_plot_margins()
            self.canvas.draw()
            if self.canvas_dock:
                self.canvas_dock.show()
            try:
                self.pane_state_changed.emit(
                    "time_series",
                    {
                        "variable": variable,
                        "mode": "standard",
                        "reaches": reach_list,
                    },
                )
            except Exception:
                pass
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to plot: {str(e)}")

    
    def update_spatial_plot(self):
        """Update spatial plot (along reach index)."""
        if self.results_data is None:
            return
        
        try:
            variable = self.spatial_variable_combo.currentText()
            
            if variable not in self.results_data:
                return
            
            data = self.results_data[variable]
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Check for Yearly Profiles
            if hasattr(self, 'spatial_yearly_check') and self.spatial_yearly_check.isChecked():
                # Assume daily time steps if not specified
                steps_per_year = 365
                if 'ts_length' in self.results_data:
                    # ts_length is in days usually? Or seconds?
                    # In D-CASCADE, ts_length is usually 1 (day) or similar.
                    # If ts_length is available, we can calculate steps per year.
                    # But let's just assume 365 for now or try to find it.
                    pass
                
                num_timesteps = data.shape[0]
                num_years = num_timesteps // steps_per_year
                
                reach_indices = range(data.shape[1])
                
                # Use a colormap
                cm = plt.get_cmap('viridis')
                
                for y in range(num_years + 1):
                    t_idx = y * steps_per_year
                    if t_idx < num_timesteps:
                        color = cm(y / (num_years + 1)) if num_years > 0 else 'blue'
                        ax.plot(reach_indices, data[t_idx, :], color=color, alpha=0.7)
                
                # Add colorbar
                sm =  self.figure.colorbar(plt.cm.ScalarMappable(cmap=cm, norm=plt.Normalize(vmin=0, vmax=num_years)), ax=ax)
                sm.set_label('Year')
                
                ax.set_title(f"{variable} - Yearly Profiles")
                ax.set_xlabel("Reach Index")
                ax.set_ylabel(variable)
                
            else:
                agg_method = self.spatial_agg_combo.currentText().lower()
                
                # Aggregate over time
                if agg_method == 'mean':
                    spatial_data = np.mean(data, axis=0)
                elif agg_method == 'median':
                    spatial_data = np.median(data, axis=0)
                elif agg_method == 'sum':
                    spatial_data = np.sum(data, axis=0)
                elif agg_method == 'max':
                    spatial_data = np.max(data, axis=0)
                elif agg_method == 'min':
                    spatial_data = np.min(data, axis=0)
                else:
                    spatial_data = np.mean(data, axis=0)
                
                reach_labels = [f"R{self.reach_ids[i]}" if i < len(self.reach_ids) else f"R{i+1}" for i in range(len(spatial_data))]
                ax.bar(reach_labels, spatial_data, color='steelblue')
                
                ax.set_title(f"{variable} - {agg_method.title()} Along Reaches")
                ax.set_xlabel("Reach Index")
                ax.set_ylabel(f"{agg_method.title()} {variable}")
                ax.tick_params(axis='x', rotation=45)
            
            self._apply_plot_margins()
            self.canvas.draw()
            if self.canvas_dock:
                self.canvas_dock.show()
            try:
                self.pane_state_changed.emit(
                    "spatial",
                    {
                        "variable": variable,
                        "agg_method": self.spatial_agg_combo.currentText(),
                        "yearly": bool(getattr(self, 'spatial_yearly_check', None) and self.spatial_yearly_check.isChecked()),
                    },
                )
            except Exception:
                pass
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to plot: {str(e)}")
    
    def update_dynamic_plot(self):
        """Update dynamic plot based on time slider."""
        if self.results_data is None:
            return
        
        try:
            variable = self.dyn_variable_combo.currentText()
            
            if variable not in self.results_data:
                return
            
            data = self.results_data[variable]
            time_step = self.time_slider.value()
            
            self.time_label.setText(f"{time_step} / {data.shape[0] - 1}")
            
            # Create bar chart for current time step
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            reach_labels = [f"R{self.reach_ids[i]}" if i < len(self.reach_ids) else f"R{i+1}" for i in range(data.shape[1])]
            values = data[time_step, :]

            # Highlight selected reaches without hiding the rest
            sel_indices = set()
            if self.selected_reaches:
                for rid in self.selected_reaches:
                    if rid in self.reach_id_map:
                        idx = self.reach_id_map[rid]
                        if 0 <= idx < len(values):
                            sel_indices.add(idx)

            colors = [
                "#e05c2a" if i in sel_indices else "#4d9de0"
                for i in range(len(values))
            ]
            ax.bar(reach_labels, values, color=colors)
            
            ax.set_title(f"{variable} - Time Step {time_step}")
            ax.set_xlabel("Reach Index")
            ax.set_ylabel(variable)
            ax.tick_params(axis='x', rotation=45)
            # Fix axis to global min/max if available
            vmin, vmax = self.data_ranges.get(variable, (np.nanmin(data), np.nanmax(data)))
            ax.set_ylim(vmin, vmax)
            self._apply_plot_margins()
            self.canvas.draw()
            if self.canvas_dock:
                self.canvas_dock.show()
            try:
                self.pane_state_changed.emit(
                    "animation",
                    {
                        "variable": variable,
                        "time_step": int(time_step),
                        "color_ramp": self.dyn_color_combo.currentText(),
                        "width_factor": float(self.dyn_width_spin.value()),
                    },
                )
            except Exception:
                pass
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to plot: {str(e)}")
    
    def update_connectivity_plot(self):
        """Update connectivity heatmap (Time vs Reach)."""
        if self.results_data is None:
            return
        
        try:
            variable = self.conn_variable_combo.currentText()
            if variable not in self.results_data:
                return
            
            data = self.results_data[variable]
            # data shape: (time, reach)
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Plot heatmap
            # x: Reach, y: Time
            im = ax.imshow(data, aspect='auto', cmap='viridis', origin='lower')
            
            ax.set_title(f"{variable} - Spatiotemporal Heatmap")
            ax.set_xlabel("Reach Index")
            ax.set_ylabel("Time Step")
            
            cbar = self.figure.colorbar(im, ax=ax)
            cbar.set_label(variable)
            
            self._apply_plot_margins()
            self.canvas.draw()
            if self.canvas_dock:
                self.canvas_dock.show()
            try:
                self.pane_state_changed.emit(
                    "connectivity",
                    {
                        "variable": variable,
                    },
                )
            except Exception:
                pass
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to plot: {str(e)}")

    def animate_results(self):
        """Animate through time steps."""
        from qgis.PyQt.QtCore import QTimer
        
        if not hasattr(self, 'animation_timer'):
            self.animation_timer = QTimer()
            self.animation_timer.timeout.connect(self._advance_animation)
        
        if self.animation_timer.isActive():
            self.animation_timer.stop()
            self.play_btn.setText("▶ Play")
        else:
            self.animation_timer.start(self.frame_duration_spin.value())  # Use value from spin box
            self.play_btn.setText("⏸ Pause")
            if self.canvas_dock:
                self.canvas_dock.show()

    def stop_animation(self):
        """Stop animation timer if running and reset button label."""
        if hasattr(self, "animation_timer") and self.animation_timer.isActive():
            self.animation_timer.stop()
        if hasattr(self, "play_btn"):
            self.play_btn.setText("▶ Play")
    
    def on_lp_time_slider_changed(self, value):
        """Handle long profile time slider change."""
        self.lp_time_label.setText(f"{value} / {self.lp_time_slider.maximum()}")
        self.update_long_profile_plot(use_slider=True)

    def update_long_profile_plot(self, use_slider=False):
        """Update long profile plot."""
        if self.results_data_ext is None or 'Node_el [m]' not in self.results_data_ext:
            if not use_slider: # Only warn if explicitly requested
                QMessageBox.warning(self, "Warning", "Extended results with 'Node_el [m]' required for long profile.")
            return
        
        if not self.selected_reaches:
            if not use_slider:
                QMessageBox.warning(self, "Warning", "No reaches selected.")
            return
            
        if not self.network_layer:
            if not use_slider:
                QMessageBox.warning(self, "Warning", "Network layer not available for topology.")
            return

        try:
            # Get topology for selected reaches
            # We need to order them.
            # 1. Get FromN, ToN, Length for all selected reaches
            reaches_info = {} # reach_id -> {from_n, to_n, length}
            
            from_n_idx = self.network_layer.fields().indexFromName('FromN')
            to_n_idx = self.network_layer.fields().indexFromName('ToN')
            len_idx = self.network_layer.fields().indexFromName('Length_m') # Assuming Length_m or similar
            if len_idx == -1:
                len_idx = self.network_layer.fields().indexFromName('Length')
            
            # Debug logging
            QgsMessageLog.logMessage(f"Long Profile: Selected reaches: {self.selected_reaches}", "D-CASCADE", Qgis.Info)
            
            for feature in self.network_layer.getFeatures():
                from_n = feature.attribute(from_n_idx)
                if str(from_n) in self.selected_reaches:
                    to_n = feature.attribute(to_n_idx)
                    length = feature.attribute(len_idx) if len_idx >= 0 else 1000.0 # Default or calc geometry
                    
                    # Resolve reach index using map
                    reach_idx = -1
                    if str(from_n) in self.reach_id_map:
                        reach_idx = self.reach_id_map[str(from_n)]
                    
                    if reach_idx >= 0:
                        reaches_info[str(from_n)] = {
                            'from': str(from_n),
                            'to': str(to_n),
                            'length': float(length),
                            'reach_idx': reach_idx
                        }
            
            if not reaches_info:
                QgsMessageLog.logMessage("Long Profile: No matching features found in layer.", "D-CASCADE", Qgis.Warning)
                return

            # Sort reaches into a chain
            # Find start node (a node that is not a 'to' node in the set)
            all_from = set(r['from'] for r in reaches_info.values())
            all_to = set(r['to'] for r in reaches_info.values())
            start_nodes = all_from - all_to
            
            if not start_nodes:
                # Cycle or single reach? Pick one.
                start_node = list(all_from)[0]
            else:
                start_node = list(start_nodes)[0] # Pick first start
            
            sorted_reaches = []
            current_from = start_node
            
            # Traverse
            while current_from in reaches_info:
                r = reaches_info[current_from]
                sorted_reaches.append(r)
                current_from = r['to']
                if len(sorted_reaches) > len(reaches_info):
                    break # Loop protection
            
            QgsMessageLog.logMessage(f"Long Profile: Sorted chain: {[r['from'] for r in sorted_reaches]}", "D-CASCADE", Qgis.Info)
            
            # Prepare data for plotting
            node_el = self.results_data_ext['Node_el [m]']
            time_step = self.lp_time_slider.value()
            
            # Update slider range if needed
            if self.lp_time_slider.maximum() != node_el.shape[0] - 1:
                self.lp_time_slider.setMaximum(node_el.shape[0] - 1)
                self.lp_time_slider.setEnabled(True)
                self.lp_time_label.setText(f"{time_step} / {node_el.shape[0] - 1}")

            dist = [0]
            elev = []
            
            current_dist = 0
            plot_dist = []
            plot_elev = []
            
            for r in sorted_reaches:
                r_idx = r['reach_idx']
                if r_idx < node_el.shape[1]:
                    # Upstream point
                    el_up = node_el[time_step, r_idx]
                    plot_dist.append(current_dist)
                    plot_elev.append(el_up)
                    
                    current_dist += r['length']
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            ax.plot(plot_dist, plot_elev, 'o-', label=f'Time {time_step}')
            
            ax.set_title("Longitudinal Profile")
            ax.set_xlabel("Distance [m]")
            ax.set_ylabel("Elevation [m]")
            ax.grid(True)
            
            self._apply_plot_margins()
            self.canvas.draw()
            if self.canvas_dock:
                self.canvas_dock.show()

            try:
                self.pane_state_changed.emit(
                    "long_profile",
                    {
                        "time_step": int(time_step),
                        "reaches": [r['from'] for r in sorted_reaches],
                    },
                )
            except Exception:
                pass

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to plot profile: {str(e)}")

    def _show_canvas_menu(self, pos):
        """Provide right-click menu with save option via toolbar."""
        if not self.toolbar:
            return
        actions = [a for a in self.toolbar.actions() if a.isVisible()]
        if not actions:
            return
        from qgis.PyQt.QtWidgets import QMenu
        menu = QMenu(self)
        for act in actions:
            menu.addAction(act)
        menu.exec_(self.canvas.mapToGlobal(pos))

    def _apply_plot_margins(self):
        """Apply consistent margins so labels/legends are fully visible."""
        try:
            self.figure.tight_layout(pad=1.8)
            self.figure.subplots_adjust(left=2, right=2, top=2, bottom=2)
        except Exception:
            pass
    
    def _advance_animation(self):
        """Advance animation by one frame."""
        current = self.time_slider.value()
        maximum = self.time_slider.maximum()
        
        if current >= maximum:
            self.time_slider.setValue(0)
        else:
            self.time_slider.setValue(current + 1)
    
    def graph_selected_reach(self, from_n_value, from_map=False):
        """Graph a specific reach (called externally when reach is selected).
        
        Args:
            from_n_value: The FromN attribute value of the selected reach
            from_map: Whether the selection came from the map; if so, only refresh
                      the currently active tab without switching away from it.
        """
        if self.results_data is None:
            return

        # Always store the selection so every tab can use it
        if from_n_value is None:
            self.selected_reaches = []
        elif isinstance(from_n_value, (list, tuple)):
            self.selected_reaches = [str(x) for x in from_n_value]
        else:
            self.selected_reaches = [str(from_n_value)]

        if from_map:
            # Refresh whichever tab is currently visible without forcing a switch
            tab = self.current_tab_name()
            if tab == "Time Series":
                self.update_time_series_plot()
            elif tab == "Animation":
                self.update_dynamic_plot()
            # Other tabs don't use selected_reaches, so no refresh needed
        else:
            # Programmatic selection: switch to Time Series and refresh
            self.tab_widget.setCurrentIndex(0)
            self.update_time_series_plot()

    def setVisible(self, visible):
        """Keep plot dock visibility in sync with the control dock."""
        super().setVisible(visible)
        if self.canvas_dock and not visible:
            self.canvas_dock.hide()

    def closeEvent(self, event):
        """Ensure the canvas dock closes when the control dock closes."""
        self.stop_animation()
        if self.canvas_dock:
            self.canvas_dock.close()
        super().closeEvent(event)

