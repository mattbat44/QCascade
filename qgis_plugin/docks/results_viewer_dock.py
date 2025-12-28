"""
@brief Dock widget for viewing and analyzing D-CASCADE simulation results
@author D-CASCADE Team
"""

from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QMessageBox,
    QFileDialog, QFormLayout, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTabWidget, QSlider
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from pathlib import Path
import pickle


class ResultsViewerDock(QDockWidget):
    """Advanced results viewer with multiple visualization options."""
    
    time_step_changed = pyqtSignal(int)  # Emitted when time slider changes
    reach_selected_for_graph = pyqtSignal(int)  # Emitted when user wants to graph a reach
    results_loaded = pyqtSignal()  # Emitted when results are successfully loaded
    animation_settings_changed = pyqtSignal()  # Emitted when ramp/width/variable changes
    
    def __init__(self, parent=None):
        super().__init__("Results Viewer", parent)
        
        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(8, 8, 8, 8)

        self.main_window = self._resolve_main_window(parent)
        self.canvas_dock = None
        
        self.results_data = None
        self.results_path = None
        self.reach_data = None
        self.selected_reaches = []
        self.data_ranges = {}
        
        self.init_ui()
        self.setWidget(self.container)
        self._init_canvas_dock()

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
        
        self.load_btn = QPushButton("Load Results (.p)")
        self.load_btn.clicked.connect(self.load_results)
        toolbar_layout.addWidget(self.load_btn)
        
        toolbar_layout.addStretch()
        
        self.main_layout.addLayout(toolbar_layout)
        
        # Info label
        self.info_label = QLabel("No results loaded. Run a simulation or load a .p file.")
        self.main_layout.addWidget(self.info_label)
        
        # Tabs for different visualization types
        self.tab_widget = QTabWidget()
        
        # Tab 1: Time Series Plots
        self.time_series_tab = self.create_time_series_tab()
        self.tab_widget.addTab(self.time_series_tab, "Time Series")
        
        # Tab 2: Spatial Plots
        self.spatial_tab = self.create_spatial_tab()
        self.tab_widget.addTab(self.spatial_tab, "Spatial Analysis")
        
        # Tab 3: Animation controls (map + plot)
        self.animation_tab = self.create_animation_tab()
        self.tab_widget.addTab(self.animation_tab, "Animation")
        
        # Tab 4: Statistics
        self.stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "Statistics")
        
        self.main_layout.addWidget(self.tab_widget)

        # Matplotlib canvas for plotting (hosted in its own dock)
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setContextMenuPolicy(Qt.CustomContextMenu)
        self.canvas.customContextMenuRequested.connect(self._show_canvas_menu)
        # Basic navigation toolbar for saving/zooming on right-click menu
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.show_empty_plot()
    
    def create_time_series_tab(self):
        """Create time series visualization tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Variable selection
        var_layout = QFormLayout()
        
        self.ts_variable_combo = QComboBox()
        self.ts_variable_combo.addItems([
            'Volume out [m^3]',
            'Volume in [m^3]',
            'Transport capacity [m^3]',
            'Sediment budget [m^3]',
            'D50 active layer [m]',
            'D50 volume out [m]'
        ])
        self.ts_variable_combo.currentTextChanged.connect(self.update_time_series_plot)
        var_layout.addRow("Variable:", self.ts_variable_combo)
        
        # Reach selection
        self.ts_reach_combo = QComboBox()
        self.ts_reach_combo.setEnabled(False)
        self.ts_reach_combo.currentIndexChanged.connect(self.update_time_series_plot)
        var_layout.addRow("Reach:", self.ts_reach_combo)
        
        # Multi-reach checkbox
        self.ts_multi_check = QCheckBox("Show all reaches")
        self.ts_multi_check.stateChanged.connect(self.update_time_series_plot)
        var_layout.addRow("", self.ts_multi_check)
        
        layout.addLayout(var_layout)
        
        # Plot button
        plot_btn = QPushButton("Generate Plot")
        plot_btn.clicked.connect(self.update_time_series_plot)
        layout.addWidget(plot_btn)
        
        layout.addStretch()
        
        return tab
    
    def create_spatial_tab(self):
        """Create spatial analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Variable selection
        var_layout = QFormLayout()
        
        self.spatial_variable_combo = QComboBox()
        self.spatial_variable_combo.addItems([
            'Volume out [m^3]',
            'Volume in [m^3]',
            'Transport capacity [m^3]',
            'Sediment budget [m^3]',
            'D50 active layer [m]',
            'D50 volume out [m]'
        ])
        self.spatial_variable_combo.currentTextChanged.connect(self.update_spatial_plot)
        var_layout.addRow("Variable:", self.spatial_variable_combo)
        
        # Aggregation method
        self.spatial_agg_combo = QComboBox()
        self.spatial_agg_combo.addItems(['Mean', 'Median', 'Sum', 'Max', 'Min'])
        self.spatial_agg_combo.currentTextChanged.connect(self.update_spatial_plot)
        var_layout.addRow("Aggregation:", self.spatial_agg_combo)
        
        # Year/time range
        self.spatial_year_spin = QSpinBox()
        self.spatial_year_spin.setRange(0, 1000)
        self.spatial_year_spin.setValue(0)
        self.spatial_year_spin.setSuffix(" (0 = all)")
        self.spatial_year_spin.valueChanged.connect(self.update_spatial_plot)
        var_layout.addRow("Year:", self.spatial_year_spin)
        
        layout.addLayout(var_layout)
        
        # Plot button
        plot_btn = QPushButton("Generate Spatial Plot")
        plot_btn.clicked.connect(self.update_spatial_plot)
        layout.addWidget(plot_btn)
        
        layout.addStretch()
        
        return tab

    def create_animation_tab(self):
        """Create animation tab to control map symbology and playback."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)

        # Variable and color ramp selection
        form = QFormLayout()
        self.dyn_variable_combo = QComboBox()
        self.dyn_variable_combo.addItems([
            'Volume out [m^3]',
            'Volume in [m^3]',
            'Transport capacity [m^3]',
            'Sediment budget [m^3]',
            'D50 active layer [m]',
            'D50 volume out [m]'
        ])
        self.dyn_variable_combo.currentTextChanged.connect(self._on_animation_setting_changed)
        form.addRow("Variable:", self.dyn_variable_combo)

        self.dyn_color_combo = QComboBox()
        self.dyn_color_combo.addItems([
            'Spectral', 'Viridis', 'Plasma', 'Magma', 'Inferno',
            'Blues', 'Greens', 'Reds', 'BuGn', 'YlOrRd'
        ])
        self.dyn_color_combo.currentTextChanged.connect(self._on_animation_setting_changed)
        form.addRow("Color ramp:", self.dyn_color_combo)

        self.dyn_width_spin = QDoubleSpinBox()
        self.dyn_width_spin.setRange(0.1, 10.0)
        self.dyn_width_spin.setSingleStep(0.1)
        self.dyn_width_spin.setValue(1.2)
        self.dyn_width_spin.valueChanged.connect(self._on_animation_setting_changed)
        form.addRow("Line width:", self.dyn_width_spin)

        layout.addLayout(form)

        # Time slider
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Time Step:"))
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(100)
        self.time_slider.setValue(0)
        self.time_slider.setEnabled(False)
        self.time_slider.valueChanged.connect(self.on_time_slider_changed)
        slider_layout.addWidget(self.time_slider, 1)
        self.time_label = QLabel("0 / 0")
        slider_layout.addWidget(self.time_label)
        layout.addLayout(slider_layout)

        # Play button
        play_layout = QHBoxLayout()
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.animate_results)
        play_layout.addWidget(self.play_btn)
        play_layout.addStretch()
        layout.addLayout(play_layout)

        #Animation frame duration
        duration_control_layout = QHBoxLayout()
        duration_control_layout.addWidget(QLabel("Frame Duration (ms):"))
        self.frame_duration_spin = QSpinBox()
        self.frame_duration_spin.setRange(50, 5000)
        self.frame_duration_spin.setValue(200)
        duration_control_layout.addWidget(self.frame_duration_spin)
        layout.addLayout(duration_control_layout)
        self.frame_duration_spin.valueChanged.connect(self._on_animation_setting_changed)

        layout.addStretch()
        return tab
    
    def on_time_slider_changed_wrapper(self, _):
        """Wrapper to handle variable change for animation."""
        self.on_time_slider_changed(self.time_slider.value())
    
    def _on_animation_setting_changed(self, *_):
        """Emit setting change and refresh current timestep."""
        self.animation_settings_changed.emit()
        self.on_time_slider_changed(self.time_slider.value())

    def create_stats_tab(self):
        """Create statistics summary tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info_label = QLabel("Summary statistics for loaded results:")
        layout.addWidget(info_label)
        
        self.stats_label = QLabel("No statistics available.")
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)
        
        refresh_btn = QPushButton("Refresh Statistics")
        refresh_btn.clicked.connect(self.update_statistics)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        
        return tab
    
    def show_empty_plot(self):
        """Show empty plot message."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'Load simulation results to visualize', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=16)
        ax.set_xticks([])
        ax.set_yticks([])
        self._apply_plot_margins()
        self.canvas.draw()
        if self.canvas_dock:
            self.canvas_dock.hide()
    
    def on_time_slider_changed(self, value):
        """Handle time slider change."""
        self.time_step_changed.emit(value)
        self.update_dynamic_plot()
    
    def load_results(self):
        """Load results from pickle file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Results File",
            "",
            "Pickle Files (*.p);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'rb') as f:
                self.results_data = pickle.load(f)
            
            self.results_path = file_path
            
            # Update UI
            self.update_ui_with_results()
            
            QMessageBox.information(
                self,
                "Success",
                f"Loaded results from {Path(file_path).name}\n"
                f"Available variables: {len(self.results_data)} fields"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load results: {str(e)}")
    
    def load_results_from_path(self, path):
        """Load results from a specific path (called externally)."""
        if Path(path).exists():
            self.results_path = path
            try:
                with open(path, 'rb') as f:
                    self.results_data = pickle.load(f)
                self.update_ui_with_results()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not load results: {str(e)}")
    
    def update_ui_with_results(self):
        """Update UI with loaded results."""
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
        
        # Update reach selector for time series
        if 'Volume out [m^3]' in self.results_data:
            num_reaches = self.results_data['Volume out [m^3]'].shape[1]
            self.ts_reach_combo.clear()
            for i in range(num_reaches):
                self.ts_reach_combo.addItem(f"Reach {i+1}")
            self.ts_reach_combo.setEnabled(True)
            
            # Update time slider
            num_timesteps = self.results_data['Volume out [m^3]'].shape[0]
            self.time_slider.setMaximum(num_timesteps - 1)
            self.time_slider.setEnabled(True)
            self.time_label.setText(f"0 / {num_timesteps - 1}")
            self.play_btn.setEnabled(True)
        
        # Generate initial plot
        self.update_time_series_plot()
        # Ensure canvas dock is visible when data is loaded
        if self.canvas_dock:
            self.canvas_dock.show()
        
        # Signal that results are loaded (e.g. to initialize animation layer)
        self.results_loaded.emit()

    def show_plot_dock(self):
        """Explicitly show the plot dock (used when user opens Results)."""
        if self.canvas_dock:
            if self.results_data is None:
                self.show_empty_plot()
            self.canvas_dock.show()
    
    def update_time_series_plot(self):
        """Update time series plot based on selections."""
        if self.results_data is None:
            return
        
        try:
            variable = self.ts_variable_combo.currentText()
            
            if variable not in self.results_data:
                self.show_empty_plot()
                return
            
            data = self.results_data[variable]
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            reach_list = []
            if self.selected_reaches:
                # Map FromN values to indices
                for rid in self.selected_reaches:
                    try:
                        idx = int(rid) - 1
                        if 0 <= idx < data.shape[1]:
                            reach_list.append(idx)
                    except Exception:
                        continue
            if not reach_list:
                if self.ts_multi_check.isChecked():
                    reach_list = list(range(min(10, data.shape[1])))
                else:
                    reach_list = [self.ts_reach_combo.currentIndex()] if self.ts_reach_combo.count() else []

            for idx in reach_list:
                if 0 <= idx < data.shape[1]:
                    ax.plot(data[:, idx], label=f'Reach {idx+1}', linewidth=2)
            
            ax.set_title(f"{variable} - Time Series")
            ax.set_xlabel("Time Step")
            ax.set_ylabel(variable)
            ax.legend()
            ax.grid(True, alpha=0.3)
            self._apply_plot_margins()
            self.canvas.draw()
            if self.canvas_dock:
                self.canvas_dock.show()
            
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
            
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            reach_labels = [f"R{i+1}" for i in range(len(spatial_data))]
            ax.bar(reach_labels, spatial_data, color='steelblue')
            
            ax.set_title(f"{variable} - {agg_method.title()} Along Reaches")
            ax.set_xlabel("Reach Index")
            ax.set_ylabel(f"{agg_method.title()} {variable}")
            ax.tick_params(axis='x', rotation=45)
            self._apply_plot_margins()
            self.canvas.draw()
            if self.canvas_dock:
                self.canvas_dock.show()
            
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
            
            reach_labels = [f"R{i+1}" for i in range(data.shape[1])]
            values = data[time_step, :]

            # If selection exists, show only selected reaches
            if self.selected_reaches:
                sel_indices = []
                for rid in self.selected_reaches:
                    try:
                        idx = int(rid) - 1
                        if 0 <= idx < len(values):
                            sel_indices.append(idx)
                    except Exception:
                        continue
                reach_labels = [reach_labels[i] for i in sel_indices]
                values = values[sel_indices]

            ax.bar(reach_labels, values)
            
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
    
    def update_statistics(self):
        """Update statistics view."""
        if self.results_data is None:
            self.stats_label.setText("No results loaded.")
            return
        
        try:
            stats_text = "<h3>Results Summary</h3><table border='1'><tr><th>Variable</th><th>Shape</th><th>Mean</th><th>Std</th><th>Min</th><th>Max</th></tr>"
            
            for var_name, var_data in self.results_data.items():
                if isinstance(var_data, np.ndarray) and var_data.ndim == 2:
                    stats_text += f"<tr>"
                    stats_text += f"<td>{var_name}</td>"
                    stats_text += f"<td>{var_data.shape}</td>"
                    stats_text += f"<td>{np.mean(var_data):.4f}</td>"
                    stats_text += f"<td>{np.std(var_data):.4f}</td>"
                    stats_text += f"<td>{np.min(var_data):.4f}</td>"
                    stats_text += f"<td>{np.max(var_data):.4f}</td>"
                    stats_text += f"</tr>"
            
            stats_text += "</table>"
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate statistics: {str(e)}")
    
    def graph_selected_reach(self, from_n_value):
        """Graph a specific reach (called externally when reach is selected).
        
        Args:
            from_n_value: The FromN attribute value of the selected reach
        """
        if self.results_data is None:
            return

        # Allow multiple selections
        if from_n_value is None:
            self.selected_reaches = []
        elif isinstance(from_n_value, (list, tuple)):
            self.selected_reaches = list(from_n_value)
        else:
            self.selected_reaches = [from_n_value]

        # Switch to time series tab and refresh
        self.tab_widget.setCurrentIndex(0)
        self.update_time_series_plot()

    def setVisible(self, visible):
        """Keep plot dock visibility in sync with the control dock."""
        super().setVisible(visible)
        if self.canvas_dock:
            # Show canvas dock whenever Results is shown (even if empty plot)
            if visible:
                if self.results_data is None:
                    self.show_empty_plot()
                self.canvas_dock.show()
            else:
                self.canvas_dock.hide()

    def closeEvent(self, event):
        """Ensure the canvas dock closes when the control dock closes."""
        self.stop_animation()
        if self.canvas_dock:
            self.canvas_dock.close()
        super().closeEvent(event)

