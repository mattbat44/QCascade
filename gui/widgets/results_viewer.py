"""
@brief Widget for viewing and analyzing D-CASCADE simulation results
@author D-CASCADE GUI Team
"""

from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QMessageBox,
    QFileDialog, QGroupBox, QFormLayout, QSpinBox,
    QCheckBox, QTabWidget, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
import pickle


class ResultsViewer(QDockWidget):
    """Advanced results viewer with multiple visualization options."""
    
    def __init__(self, parent=None):
        super().__init__("Results Analysis", parent)
        
        self.container = QWidget()
        self.main_layout = QVBoxLayout(self.container)
        
        self.results_data = None
        self.results_path = None
        self.reach_data = None
        
        self.init_ui()
        self.setWidget(self.container)
    
    def init_ui(self):
        """Initialize the user interface."""
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("Load Results (.p)")
        self.load_btn.clicked.connect(self.load_results)
        toolbar_layout.addWidget(self.load_btn)
        
        self.export_btn = QPushButton("Export Plot")
        self.export_btn.clicked.connect(self.export_plot)
        self.export_btn.setEnabled(False)
        toolbar_layout.addWidget(self.export_btn)
        
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
        
        # Tab 3: Dynamic Viewer
        self.dynamic_tab = self.create_dynamic_tab()
        self.tab_widget.addTab(self.dynamic_tab, "Dynamic Viewer")
        
        # Tab 4: Statistics
        self.stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "Statistics")
        
        self.main_layout.addWidget(self.tab_widget)
        
        # Main plot area
        self.plot_view = QWebEngineView()
        self.main_layout.addWidget(self.plot_view, 1)
        
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
    
    def create_dynamic_tab(self):
        """Create dynamic viewer tab with time slider."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Controls
        controls_layout = QFormLayout()
        
        self.dyn_variable_combo = QComboBox()
        self.dyn_variable_combo.addItems([
            'Volume out [m^3]',
            'Volume in [m^3]',
            'Transport capacity [m^3]',
            'Sediment budget [m^3]',
            'D50 active layer [m]',
            'D50 volume out [m]'
        ])
        controls_layout.addRow("Variable:", self.dyn_variable_combo)
        
        layout.addLayout(controls_layout)
        
        # Time slider
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Time Step:"))
        
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(100)
        self.time_slider.setValue(0)
        self.time_slider.setEnabled(False)
        self.time_slider.valueChanged.connect(self.update_dynamic_plot)
        slider_layout.addWidget(self.time_slider, 1)
        
        self.time_label = QLabel("0 / 0")
        slider_layout.addWidget(self.time_label)
        
        layout.addLayout(slider_layout)
        
        # Animation controls
        anim_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.animate_results)
        anim_layout.addWidget(self.play_btn)
        
        anim_layout.addStretch()
        layout.addLayout(anim_layout)
        
        layout.addStretch()
        
        return tab
    
    def create_stats_tab(self):
        """Create statistics summary tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info_label = QLabel("Summary statistics for loaded results:")
        layout.addWidget(info_label)
        
        self.stats_view = QWebEngineView()
        layout.addWidget(self.stats_view)
        
        refresh_btn = QPushButton("Refresh Statistics")
        refresh_btn.clicked.connect(self.update_statistics)
        layout.addWidget(refresh_btn)
        
        return tab
    
    def show_empty_plot(self):
        """Show empty plot message."""
        fig = go.Figure()
        fig.update_layout(
            title="D-CASCADE Results Viewer",
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[{
                "text": "Load simulation results to visualize",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16}
            }],
            height=600
        )
        html = fig.to_html(include_plotlyjs='cdn')
        self.plot_view.setHtml(html)
    
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
        
        self.export_btn.setEnabled(True)
        
        # Generate initial plot
        self.update_time_series_plot()
    
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
            
            fig = go.Figure()
            
            if self.ts_multi_check.isChecked():
                # Plot multiple reaches
                num_reaches = min(10, data.shape[1])  # Limit to 10 for performance
                for i in range(num_reaches):
                    fig.add_trace(go.Scatter(
                        y=data[:, i],
                        mode='lines',
                        name=f'Reach {i+1}',
                        line=dict(width=2)
                    ))
            else:
                # Single reach
                reach_idx = self.ts_reach_combo.currentIndex()
                if reach_idx < data.shape[1]:
                    fig.add_trace(go.Scatter(
                        y=data[:, reach_idx],
                        mode='lines',
                        name=f'Reach {reach_idx+1}',
                        line=dict(width=2, color='#1f77b4')
                    ))
            
            fig.update_layout(
                title=f"{variable} - Time Series",
                xaxis_title="Time Step",
                yaxis_title=variable,
                hovermode='x unified',
                height=600,
                showlegend=True
            )
            
            html = fig.to_html(include_plotlyjs='cdn')
            self.plot_view.setHtml(html)
            
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
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=[f"R{i+1}" for i in range(len(spatial_data))],
                y=spatial_data,
                marker=dict(
                    color=spatial_data,
                    colorscale='Viridis',
                    showscale=True
                )
            ))
            
            fig.update_layout(
                title=f"{variable} - {agg_method.title()} Along Reaches",
                xaxis_title="Reach Index",
                yaxis_title=f"{agg_method.title()} {variable}",
                height=600
            )
            
            html = fig.to_html(include_plotlyjs='cdn')
            self.plot_view.setHtml(html)
            
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
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=[f"R{i+1}" for i in range(data.shape[1])],
                y=data[time_step, :],
                marker=dict(
                    color=data[time_step, :],
                    colorscale='Plasma',
                    showscale=True
                )
            ))
            
            fig.update_layout(
                title=f"{variable} - Time Step {time_step}",
                xaxis_title="Reach Index",
                yaxis_title=variable,
                height=600
            )
            
            html = fig.to_html(include_plotlyjs='cdn')
            self.plot_view.setHtml(html)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to plot: {str(e)}")
    
    def animate_results(self):
        """Animate through time steps."""
        # Simple animation by incrementing slider
        from PyQt6.QtCore import QTimer
        
        if not hasattr(self, 'animation_timer'):
            self.animation_timer = QTimer()
            self.animation_timer.timeout.connect(self._advance_animation)
        
        if self.animation_timer.isActive():
            self.animation_timer.stop()
            self.play_btn.setText("▶ Play")
        else:
            self.animation_timer.start(200)  # 200ms per frame
            self.play_btn.setText("⏸ Pause")
    
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
            return
        
        try:
            # Create summary statistics table
            stats_html = "<html><body><h2>Results Summary</h2><table border='1' style='border-collapse: collapse; width: 100%;'>"
            stats_html += "<tr><th>Variable</th><th>Shape</th><th>Mean</th><th>Std</th><th>Min</th><th>Max</th></tr>"
            
            for var_name, var_data in self.results_data.items():
                if isinstance(var_data, np.ndarray) and var_data.ndim == 2:
                    stats_html += f"<tr>"
                    stats_html += f"<td>{var_name}</td>"
                    stats_html += f"<td>{var_data.shape}</td>"
                    stats_html += f"<td>{np.mean(var_data):.4f}</td>"
                    stats_html += f"<td>{np.std(var_data):.4f}</td>"
                    stats_html += f"<td>{np.min(var_data):.4f}</td>"
                    stats_html += f"<td>{np.max(var_data):.4f}</td>"
                    stats_html += f"</tr>"
            
            stats_html += "</table></body></html>"
            
            self.stats_view.setHtml(stats_html)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate statistics: {str(e)}")
    
    def export_plot(self):
        """Export current plot to file."""
        if self.results_data is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Plot",
            "",
            "HTML Files (*.html);;PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            try:
                # For now, just save the HTML
                # In a real implementation, we'd need to extract the current plot
                QMessageBox.information(self, "Info", "Plot export feature coming soon!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
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
