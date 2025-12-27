"""
@brief Widget for viewing and editing discharge data
@author D-CASCADE GUI Team
"""

from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QFileDialog, QHeaderView, QComboBox, QLabel, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
from PyQt6.QtWebEngineWidgets import QWebEngineView


class DischargeEditor(QDockWidget):
    """Widget for viewing, editing, and creating discharge data."""
    
    discharge_updated = pyqtSignal(str)  # Emits path to updated discharge file
    
    def __init__(self, parent=None):
        super().__init__("Discharge", parent)
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        
        self.discharge_data = None
        self.discharge_path = None
        
        self.init_ui()
        self.setWidget(self.container)
    
    def init_ui(self):
        """Initialize the user interface."""
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("Load CSV")
        self.load_btn.clicked.connect(self.load_discharge_csv)
        toolbar_layout.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("Save CSV")
        self.save_btn.clicked.connect(self.save_discharge_csv)
        self.save_btn.setEnabled(False)
        toolbar_layout.addWidget(self.save_btn)
        
        self.new_btn = QPushButton("New Dataset")
        self.new_btn.clicked.connect(self.create_new_dataset)
        toolbar_layout.addWidget(self.new_btn)
        
        self.plot_btn = QPushButton("Plot Time Series")
        self.plot_btn.clicked.connect(self.plot_discharge)
        self.plot_btn.setEnabled(False)
        toolbar_layout.addWidget(self.plot_btn)
        
        toolbar_layout.addStretch()
        
        self.layout.addLayout(toolbar_layout)
        
        # Selection controls
        select_layout = QHBoxLayout()
        
        select_layout.addWidget(QLabel("View Reach:"))
        self.reach_combo = QComboBox()
        self.reach_combo.setEnabled(False)
        self.reach_combo.currentIndexChanged.connect(self.on_reach_selected)
        select_layout.addWidget(self.reach_combo)
        
        select_layout.addWidget(QLabel("Show Rows:"))
        self.row_limit_spin = QSpinBox()
        self.row_limit_spin.setRange(10, 10000)
        self.row_limit_spin.setValue(100)
        self.row_limit_spin.setSuffix(" rows")
        self.row_limit_spin.valueChanged.connect(self.update_table_display)
        select_layout.addWidget(self.row_limit_spin)
        
        select_layout.addStretch()
        
        self.layout.addLayout(select_layout)
        
        # Data info label
        self.info_label = QLabel("No discharge data loaded")
        self.layout.addWidget(self.info_label)
        
        # Table widget
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.itemChanged.connect(self.on_cell_changed)
        self.layout.addWidget(self.table)
        
        # Plot view
        self.plot_view = QWebEngineView()
        self.plot_view.setMaximumHeight(300)
        self.layout.addWidget(self.plot_view)
        self.show_empty_plot()
    
    def show_empty_plot(self):
        """Show empty plot message."""
        fig = go.Figure()
        fig.update_layout(
            title="Discharge Time Series",
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[{
                "text": "Load data and click 'Plot Time Series' to visualize",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 14}
            }]
        )
        html = fig.to_html(include_plotlyjs='cdn')
        self.plot_view.setHtml(html)
    
    def load_discharge_csv(self):
        """Load discharge data from CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Discharge CSV",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            self.discharge_data = pd.read_csv(file_path, header=None)
            self.discharge_path = file_path
            
            self.update_ui_with_data()
            self.save_btn.setEnabled(True)
            self.plot_btn.setEnabled(True)
            
            QMessageBox.information(
                self,
                "Success",
                f"Loaded discharge data with {self.discharge_data.shape[0]} time steps "
                f"and {self.discharge_data.shape[1]} reaches."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")
    
    def save_discharge_csv(self):
        """Save discharge data to CSV file."""
        if self.discharge_data is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Discharge CSV",
            self.discharge_path or "discharge.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            self.discharge_data.to_csv(file_path, index=False, header=False)
            self.discharge_path = file_path
            
            QMessageBox.information(self, "Success", "Discharge data saved successfully!")
            self.discharge_updated.emit(file_path)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CSV: {str(e)}")
    
    def create_new_dataset(self):
        """Create a new discharge dataset."""
        from PyQt6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Discharge Dataset")
        layout = QFormLayout(dialog)
        
        time_steps = QSpinBox()
        time_steps.setRange(1, 100000)
        time_steps.setValue(365)
        layout.addRow("Number of Time Steps:", time_steps)
        
        num_reaches = QSpinBox()
        num_reaches.setRange(1, 1000)
        num_reaches.setValue(10)
        layout.addRow("Number of Reaches:", num_reaches)
        
        default_value = QSpinBox()
        default_value.setRange(0, 10000)
        default_value.setValue(10)
        default_value.setSuffix(" m³/s")
        layout.addRow("Default Discharge:", default_value)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec():
            self.discharge_data = pd.DataFrame(
                np.full((time_steps.value(), num_reaches.value()), default_value.value())
            )
            self.discharge_path = None
            
            self.update_ui_with_data()
            self.save_btn.setEnabled(True)
            self.plot_btn.setEnabled(True)
    
    def update_ui_with_data(self):
        """Update UI components with loaded data."""
        if self.discharge_data is None:
            return
        
        # Update info label
        self.info_label.setText(
            f"Data Shape: {self.discharge_data.shape[0]} time steps × "
            f"{self.discharge_data.shape[1]} reaches | "
            f"File: {Path(self.discharge_path).name if self.discharge_path else 'Unsaved'}"
        )
        
        # Update reach selector
        self.reach_combo.clear()
        self.reach_combo.addItem("All Reaches (Preview)")
        for i in range(self.discharge_data.shape[1]):
            self.reach_combo.addItem(f"Reach {i + 1}")
        self.reach_combo.setEnabled(True)
        
        # Update table display
        self.update_table_display()
    
    def update_table_display(self):
        """Update the table widget with current data."""
        if self.discharge_data is None:
            return
        
        self.table.blockSignals(True)  # Prevent itemChanged during updates
        
        row_limit = self.row_limit_spin.value()
        display_rows = min(row_limit, self.discharge_data.shape[0])
        
        self.table.setRowCount(display_rows)
        self.table.setColumnCount(self.discharge_data.shape[1])
        
        # Set headers
        self.table.setHorizontalHeaderLabels(
            [f"Reach {i+1}" for i in range(self.discharge_data.shape[1])]
        )
        self.table.setVerticalHeaderLabels(
            [f"T{i+1}" for i in range(display_rows)]
        )
        
        # Populate table
        for i in range(display_rows):
            for j in range(self.discharge_data.shape[1]):
                item = QTableWidgetItem(str(self.discharge_data.iloc[i, j]))
                self.table.setItem(i, j, item)
        
        # Auto-resize columns
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.blockSignals(False)
    
    def on_cell_changed(self, item):
        """Handle cell value changes."""
        if self.discharge_data is None:
            return
        
        try:
            row = item.row()
            col = item.column()
            new_value = float(item.text())
            self.discharge_data.iloc[row, col] = new_value
        except ValueError:
            QMessageBox.warning(self, "Invalid Value", "Please enter a numeric value.")
            # Restore old value
            self.table.blockSignals(True)
            item.setText(str(self.discharge_data.iloc[item.row(), item.column()]))
            self.table.blockSignals(False)
    
    def on_reach_selected(self, index):
        """Handle reach selection change."""
        # This could be used to highlight specific reach or filter view
        pass
    
    def plot_discharge(self):
        """Plot discharge time series."""
        if self.discharge_data is None:
            return
        
        selected_idx = self.reach_combo.currentIndex()
        
        fig = go.Figure()
        
        if selected_idx == 0:  # All reaches preview
            # Plot first 5 reaches or all if less than 5
            num_to_plot = min(5, self.discharge_data.shape[1])
            for i in range(num_to_plot):
                fig.add_trace(go.Scatter(
                    y=self.discharge_data.iloc[:, i],
                    mode='lines',
                    name=f'Reach {i+1}'
                ))
        else:  # Single reach
            reach_idx = selected_idx - 1
            fig.add_trace(go.Scatter(
                y=self.discharge_data.iloc[:, reach_idx],
                mode='lines',
                name=f'Reach {reach_idx+1}'
            ))
        
        fig.update_layout(
            title="Discharge Time Series",
            xaxis_title="Time Step",
            yaxis_title="Discharge (m³/s)",
            hovermode='x unified',
            showlegend=True
        )
        
        html = fig.to_html(include_plotlyjs='cdn')
        self.plot_view.setHtml(html)
    
    def set_discharge_path(self, path):
        """Set discharge path from external source (e.g., config)."""
        if Path(path).exists():
            self.discharge_path = path
            try:
                self.discharge_data = pd.read_csv(path, header=None)
                self.update_ui_with_data()
                self.save_btn.setEnabled(True)
                self.plot_btn.setEnabled(True)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not load discharge file: {str(e)}")
