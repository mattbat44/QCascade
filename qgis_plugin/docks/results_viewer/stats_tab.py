"""
@brief Statistics summary tab component for D-CASCADE results viewer
@author D-CASCADE Team
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel
)


from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QCheckBox, QScrollArea, QFrame
)
from qgis.PyQt.QtCore import Qt
import numpy as np


class StatsTab(QWidget):
    """Functional summary tab for exploring results matrices and statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_dock = parent  # Reference to ResultsViewerDock
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        
        # 1. Variable Selection
        selection_group = QGroupBox("Matrix Selection")
        selection_layout = QVBoxLayout(selection_group)
        
        var_hbox = QHBoxLayout()
        var_hbox.addWidget(QLabel("Variable:"))
        self.var_combo = QComboBox()
        self.var_combo.currentTextChanged.connect(self._on_var_changed)
        var_hbox.addWidget(self.var_combo, 1)
        selection_layout.addLayout(var_hbox)
        
        self.shape_label = QLabel("Shape: N/A")
        selection_layout.addWidget(self.shape_label)
        
        main_layout.addWidget(selection_group)
        
        # 2. Dimensions & Aggregation
        agg_group = QGroupBox("Aggregation Options")
        self.agg_layout = QVBoxLayout(agg_group)
        
        self.agg_info = QLabel("Select dimensions to sum/mean over:")
        self.agg_layout.addWidget(self.agg_info)
        
        self.dim_checkboxes = []
        self.dim_container = QWidget()
        self.dim_hbox = QHBoxLayout(self.dim_container)
        self.agg_layout.addWidget(self.dim_container)
        
        mode_hbox = QHBoxLayout()
        mode_hbox.addWidget(QLabel("Mode:"))
        self.agg_mode_combo = QComboBox()
        self.agg_mode_combo.addItems(["Sum", "Mean", "Max", "Min"])
        mode_hbox.addWidget(self.agg_mode_combo, 1)
        self.agg_layout.addLayout(mode_hbox)
        
        main_layout.addWidget(agg_group)
        
        # 3. Actions
        btn_hbox = QHBoxLayout()
        self.refresh_btn = QPushButton("Calculate Statistics")
        self.refresh_btn.clicked.connect(self.update_statistics)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E86AB;
                color: white;
                font-weight: bold;
                height: 30px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3AABDB;
            }
        """)
        btn_hbox.addWidget(self.refresh_btn)
        
        self.plot_btn = QPushButton("Plot Current State")
        self.plot_btn.clicked.connect(self._plot_aggregated)
        btn_hbox.addWidget(self.plot_btn)
        
        main_layout.addLayout(btn_hbox)
        
        # 4. Statistics Results
        results_group = QGroupBox("Exploration & Statistics")
        results_layout = QVBoxLayout(results_group)
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stats_table.setStyleSheet("QTableWidget { gridline-color: #ddd; }")
        results_layout.addWidget(self.stats_table)
        
        # Add a placeholder for general info
        self.info_text = QLabel("<i>Aggregation reduces the dimensions of the matrix before calculating statistics.</i>")
        self.info_text.setWordWrap(True)
        self.info_text.setStyleSheet("color: #666; font-size: 10px;")
        results_layout.addWidget(self.info_text)
        
        self.stats_label = QLabel("") # For backward compatibility with dock's reference
        self.stats_label.hide()
        
        main_layout.addWidget(results_group)
        
        main_layout.addStretch()

    def _on_var_changed(self, var_name):
        """Handle variable change to update dimension checkboxes."""
        if not var_name or self.results_dock.results_data is None:
            return
            
        # Clear old checkboxes
        for cb in self.dim_checkboxes:
            self.dim_hbox.removeWidget(cb)
            cb.deleteLater()
        self.dim_checkboxes = []
        
        # Get data
        data = self._get_var_data(var_name)
        if data is None:
            self.shape_label.setText("Shape: N/A")
            return
            
        self.shape_label.setText(f"<b>Shape:</b> {data.shape}")
        
        # Define dimension names based on typical D-CASCADE shapes
        # (Time, Reach) or (Time, Reach, Class)
        dim_names = []
        if data.ndim == 2:
            dim_names = ["Time", "Reach"]
        elif data.ndim == 3:
            dim_names = ["Time", "Reach", "Sediment Class"]
        elif data.ndim == 1:
            dim_names = ["Index"]
        else:
            dim_names = [f"Dim {i}" for i in range(data.ndim)]
            
        for i, name in enumerate(dim_names):
            cb = QCheckBox(name)
            cb.setProperty("dim_index", i)
            cb.stateChanged.connect(self.update_statistics) # Auto-update when toggled
            self.dim_hbox.addWidget(cb)
            self.dim_checkboxes.append(cb)
            
        # Initial statistics calculation
        self.update_statistics()

    def _get_var_data(self, var_name):
        """Helper to get data from results or extended results."""
        if self.results_dock.results_data and var_name in self.results_dock.results_data:
            return self.results_dock.results_data[var_name]
        if self.results_dock.results_data_ext and var_name in self.results_dock.results_data_ext:
            return self.results_dock.results_data_ext[var_name]
        return None

    def update_statistics(self):
        """Calculate and display statistics for selected/aggregated data."""
        var_name = self.var_combo.currentText()
        if not var_name: return
        
        data = self._get_var_data(var_name)
        if data is None: return
            
        # Perform aggregation if requested
        agg_dims = [cb.property("dim_index") for cb in self.dim_checkboxes if cb.isChecked()]
        mode = self.agg_mode_combo.currentText()
        
        processed_data = data
        if agg_dims:
            try:
                # We need to handle nan values
                if mode == "Sum":
                    processed_data = np.nansum(data, axis=tuple(agg_dims))
                elif mode == "Mean":
                    processed_data = np.nanmean(data, axis=tuple(agg_dims))
                elif mode == "Max":
                    processed_data = np.nanmax(data, axis=tuple(agg_dims))
                elif mode == "Min":
                    processed_data = np.nanmin(data, axis=tuple(agg_dims))
            except Exception as e:
                self.info_text.setText(f"<font color='red'>Aggregation error: {e}</font>")
                return

        # Calculate metrics
        try:
            metrics = {
                "Full Mean": np.nanmean(data),
                "Full Sum": np.nansum(data),
                "Aggregated Mean": np.nanmean(processed_data),
                "Aggregated Sum": np.nansum(processed_data),
                "Aggregated Max": np.nanmax(processed_data),
                "Aggregated Min": np.nanmin(processed_data),
                "Non-NaN Count": np.count_nonzero(~np.isnan(processed_data)),
                "Aggregated Shape": processed_data.shape
            }
            
            # Update table
            self.stats_table.setRowCount(len(metrics))
            for i, (name, val) in enumerate(metrics.items()):
                self.stats_table.setItem(i, 0, QTableWidgetItem(name))
                if isinstance(val, (tuple, list, np.ndarray)):
                    self.stats_table.setItem(i, 1, QTableWidgetItem(str(val)))
                elif isinstance(val, (int, np.integer)):
                    self.stats_table.setItem(i, 1, QTableWidgetItem(str(val)))
                else:
                    self.stats_table.setItem(i, 1, QTableWidgetItem(f"{val:.4e}"))
            
            self.info_text.setText(f"Showing results for <b>{var_name}</b>" + (f" aggregated by {mode}" if agg_dims else ""))
            
        except Exception as e:
            self.info_text.setText(f"<font color='red'>Stat calculation error: {e}</font>")
                
    def _plot_aggregated(self):
        """Plot the currently aggregated data in the main dock's canvas."""
        var_name = self.var_combo.currentText()
        data = self._get_var_data(var_name)
        if data is None: return
        
        agg_dims = [cb.property("dim_index") for cb in self.dim_checkboxes if cb.isChecked()]
        mode = self.agg_mode_combo.currentText()
        
        processed_data = data
        remaining_dims = [i for i in range(data.ndim) if i not in agg_dims]
        
        if agg_dims:
            try:
                if mode == "Sum": processed_data = np.nansum(data, axis=tuple(agg_dims))
                elif mode == "Mean": processed_data = np.nanmean(data, axis=tuple(agg_dims))
                elif mode == "Max": processed_data = np.nanmax(data, axis=tuple(agg_dims))
                elif mode == "Min": processed_data = np.nanmin(data, axis=tuple(agg_dims))
            except Exception as e:
                from qgis.PyQt.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Plot Error", f"Could not aggregate for plotting: {e}")
                return

        # We can only plot if 1D or 2D (heatmap)
        try:
            if processed_data.ndim == 1:
                self.results_dock.figure.clear()
                ax = self.results_dock.figure.add_subplot(111)
                ax.plot(processed_data, marker='o', linestyle='-', markersize=4)
                ax.set_title(f"{mode} of {var_name}")
                ax.set_ylabel(var_name)
                ax.grid(True, alpha=0.3)
                
                # Label X axis based on what's left
                if len(remaining_dims) == 1:
                    labels = ["Time", "Reach", "Sediment Class"]
                    ax.set_xlabel(labels[remaining_dims[0]] if remaining_dims[0] < 3 else "Index")
                
                self.results_dock._apply_plot_margins()
                self.results_dock.canvas.draw()
                if self.results_dock.canvas_dock:
                    self.results_dock.canvas_dock.show()
            elif processed_data.ndim == 2:
                self.results_dock.figure.clear()
                ax = self.results_dock.figure.add_subplot(111)
                im = ax.imshow(processed_data, aspect='auto', interpolation='nearest', cmap='viridis')
                self.results_dock.figure.colorbar(im, ax=ax, label=var_name)
                ax.set_title(f"{mode} of {var_name}")
                
                if len(remaining_dims) == 2:
                    labels = ["Time", "Reach", "Sediment Class"]
                    ax.set_ylabel(labels[remaining_dims[0]] if remaining_dims[0] < 3 else "Dim 0")
                    ax.set_xlabel(labels[remaining_dims[1]] if remaining_dims[1] < 3 else "Dim 1")

                self.results_dock._apply_plot_margins()
                self.results_dock.canvas.draw()
                if self.results_dock.canvas_dock:
                    self.results_dock.canvas_dock.show()
            else:
                 from qgis.PyQt.QtWidgets import QMessageBox
                 QMessageBox.information(self, "Plotting Info", 
                    f"Processed data has {processed_data.ndim} dimensions. Please aggregate more dimensions (checkboxes) until you have 1 or 2 left to visualize.")
        except Exception as e:
            from qgis.PyQt.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Critical Plot Error", str(e))


