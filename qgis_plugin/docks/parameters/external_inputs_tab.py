"""
@brief External inputs tab component for D-CASCADE parameters dock
@author D-CASCADE Team
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QListWidget, QFileDialog, QMessageBox
)
from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.core import QgsMessageLog, Qgis
import os
import csv


class ExternalInputsTab(QWidget):
    """External inputs management tab."""
    
    external_input_added = pyqtSignal(int, str)  # reach_idx, csv_path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.external_inputs_mapping = {}  # {reach_idx: [csv_paths]}
        self.selected_reach_idx = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel("Select a reach in the map canvas to add external input CSV files.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Selected reach info
        reach_layout = QHBoxLayout()
        reach_layout.addWidget(QLabel("Selected Reach:"))
        self.selected_reach_label = QLabel("None")
        reach_layout.addWidget(self.selected_reach_label)
        reach_layout.addStretch()
        layout.addLayout(reach_layout)
        
        # Add external input button
        self.add_ext_input_btn = QPushButton("Add External Input CSV...")
        self.add_ext_input_btn.setEnabled(False)
        self.add_ext_input_btn.clicked.connect(self.add_external_input)
        layout.addWidget(self.add_ext_input_btn)

        # Create template button
        self.create_ext_input_btn = QPushButton("Create External Input CSV")
        self.create_ext_input_btn.setEnabled(False)
        self.create_ext_input_btn.clicked.connect(self.create_external_input_template)
        layout.addWidget(self.create_ext_input_btn)
        
        # List of external inputs for selected reach
        self.ext_inputs_list = QListWidget()
        layout.addWidget(QLabel("External Inputs for Selected Reach:"))
        layout.addWidget(self.ext_inputs_list)
        
        # Remove button
        self.remove_ext_input_btn = QPushButton("Remove Selected")
        self.remove_ext_input_btn.setEnabled(False)
        self.remove_ext_input_btn.clicked.connect(self.remove_external_input)
        layout.addWidget(self.remove_ext_input_btn)
        
        layout.addStretch()
    
    def set_selected_reach(self, reach_idx):
        """Set the selected reach for external inputs management."""
        self.selected_reach_idx = reach_idx
        if reach_idx is not None:
            self.selected_reach_label.setText(f"Reach {reach_idx}")
            self.add_ext_input_btn.setEnabled(True)
            self.create_ext_input_btn.setEnabled(True)
            self.update_external_inputs_list()
        else:
            self.selected_reach_label.setText("None")
            self.add_ext_input_btn.setEnabled(False)
            self.create_ext_input_btn.setEnabled(False)
            self.ext_inputs_list.clear()
    
    def update_external_inputs_list(self):
        """Update the list of external inputs for the selected reach."""
        self.ext_inputs_list.clear()
        if self.selected_reach_idx is not None:
            inputs = self.external_inputs_mapping.get(self.selected_reach_idx, [])
            for csv_path in inputs:
                self.ext_inputs_list.addItem(os.path.basename(csv_path))
            self.remove_ext_input_btn.setEnabled(len(inputs) > 0)
    
    def add_external_input(self):
        """Add an external input CSV file to the selected reach."""
        if self.selected_reach_idx is None:
            return
        
        path, _ = QFileDialog.getOpenFileName(
            self, "Select External Input CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        
        if self.selected_reach_idx not in self.external_inputs_mapping:
            self.external_inputs_mapping[self.selected_reach_idx] = []
        
        self.external_inputs_mapping[self.selected_reach_idx].append(path)
        self.ext_inputs_list.addItem(os.path.basename(path))
        self.remove_ext_input_btn.setEnabled(True)
        
        self.external_input_added.emit(self.selected_reach_idx, path)

    def create_external_input_template(self):
        """Create a CSV template for the selected reach and open it for editing."""
        if self.selected_reach_idx is None:
            QgsMessageLog.logMessage("Please select a reach in the map first.", "D-CASCADE", Qgis.Info)
            return

        default_name = f"reach_{self.selected_reach_idx}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Create External Input CSV",
            default_name,
            "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return

        try:
            # Get timescale from parent if available
            timescale = 1
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, 'timescale'):
                    try:
                        timescale = max(1, int(parent.timescale.value()))
                    except Exception:
                        pass
                    break
                parent = parent.parent()
        except Exception:
            timescale = 1

        header = ["time_idx", "D50", "volume_m3"]
        rows = [[t, 2.0, 0] for t in range(timescale)]

        try:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(rows)
        except Exception as e:
            QMessageBox.critical(self, "Write Failed", f"Could not create template: {e}")
            return

        # Track in UI/mapping
        if self.selected_reach_idx not in self.external_inputs_mapping:
            self.external_inputs_mapping[self.selected_reach_idx] = []
        self.external_inputs_mapping[self.selected_reach_idx].append(path)
        self.ext_inputs_list.addItem(os.path.basename(path))
        self.remove_ext_input_btn.setEnabled(True)

        # Open the file for user editing
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception:
            pass
    
    def remove_external_input(self):
        """Remove the selected external input from the list."""
        if self.selected_reach_idx is None:
            return
        
        current_item = self.ext_inputs_list.currentItem()
        if current_item is None:
            return
        
        row = self.ext_inputs_list.row(current_item)
        if self.selected_reach_idx in self.external_inputs_mapping:
            inputs = self.external_inputs_mapping[self.selected_reach_idx]
            if row < len(inputs):
                del inputs[row]
                self.ext_inputs_list.takeItem(row)
                self.remove_ext_input_btn.setEnabled(len(inputs) > 0)
