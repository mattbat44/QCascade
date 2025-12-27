"""
@brief Dialog for editing reach attributes
@author D-CASCADE GUI Team
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QDoubleSpinBox, QPushButton, QLabel,
    QTabWidget, QWidget, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
import json


class ReachEditorDialog(QDialog):
    """Dialog to view and edit attributes of a selected reach."""
    
    def __init__(self, reach_data, parent=None):
        """
        @param reach_data: Dictionary containing reach attributes
        @param parent: Parent widget
        """
        super().__init__(parent)
        self.reach_data = reach_data.copy()
        self.original_data = reach_data.copy()
        self.setWindowTitle(f"Edit Reach: {reach_data.get('FromN', 'Unknown')}")
        self.setModal(True)
        self.resize(500, 600)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(f"<h2>Reach {self.reach_data.get('FromN', 'Unknown')}</h2>")
        layout.addWidget(title)
        
        # Tabs for organization
        tabs = QTabWidget()
        
        # Basic Info Tab
        basic_tab = QWidget()
        basic_layout = QFormLayout(basic_tab)
        
        # Reach Name (editable)
        self.name_edit = QLineEdit(str(self.reach_data.get('Name', '')))
        self.name_edit.setPlaceholderText("Enter reach name...")
        basic_layout.addRow("Reach Name:", self.name_edit)
        
        # FromN and ToN (read-only)
        from_n_label = QLabel(str(self.reach_data.get('FromN', 'N/A')))
        to_n_label = QLabel(str(self.reach_data.get('ToN', 'N/A')))
        basic_layout.addRow("From Node:", from_n_label)
        basic_layout.addRow("To Node:", to_n_label)
        
        tabs.addTab(basic_tab, "Basic Info")
        
        # Geometry Tab
        geom_tab = QWidget()
        geom_layout = QFormLayout(geom_tab)
        
        # Length (editable)
        self.length_edit = QDoubleSpinBox()
        self.length_edit.setRange(0, 1e9)
        self.length_edit.setDecimals(2)
        self.length_edit.setValue(float(self.reach_data.get('Length', 0)))
        self.length_edit.setSuffix(" m")
        geom_layout.addRow("Length:", self.length_edit)
        
        # Slope (editable)
        self.slope_edit = QDoubleSpinBox()
        self.slope_edit.setRange(0, 1)
        self.slope_edit.setDecimals(6)
        self.slope_edit.setValue(float(self.reach_data.get('Slope', 0)))
        geom_layout.addRow("Slope:", self.slope_edit)
        
        # Width (editable)
        self.width_edit = QDoubleSpinBox()
        self.width_edit.setRange(0, 10000)
        self.width_edit.setDecimals(2)
        self.width_edit.setValue(float(self.reach_data.get('W', 0)))
        self.width_edit.setSuffix(" m")
        geom_layout.addRow("Width:", self.width_edit)
        
        tabs.addTab(geom_tab, "Geometry")
        
        # Sediment Tab
        sed_tab = QWidget()
        sed_layout = QFormLayout(sed_tab)
        
        # D50 (editable)
        self.d50_edit = QDoubleSpinBox()
        self.d50_edit.setRange(0, 1)
        self.d50_edit.setDecimals(6)
        self.d50_edit.setValue(float(self.reach_data.get('D50', 0)))
        self.d50_edit.setSuffix(" m")
        sed_layout.addRow("D50:", self.d50_edit)
        
        # D90 (editable if present)
        if 'D90' in self.reach_data:
            self.d90_edit = QDoubleSpinBox()
            self.d90_edit.setRange(0, 1)
            self.d90_edit.setDecimals(6)
            self.d90_edit.setValue(float(self.reach_data.get('D90', 0)))
            self.d90_edit.setSuffix(" m")
            sed_layout.addRow("D90:", self.d90_edit)
        else:
            self.d90_edit = None
        
        tabs.addTab(sed_tab, "Sediment")
        
        # All Attributes Tab (JSON view)
        all_tab = QWidget()
        all_layout = QVBoxLayout(all_tab)
        self.json_view = QTextEdit()
        self.json_view.setReadOnly(True)
        self.json_view.setPlainText(json.dumps(self.reach_data, indent=2, default=str))
        all_layout.addWidget(QLabel("All Attributes (Read-only):"))
        all_layout.addWidget(self.json_view)
        
        tabs.addTab(all_tab, "All Attributes")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_values)
        
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def save_changes(self):
        """Save the edited values."""
        try:
            # Update reach_data with edited values
            self.reach_data['Name'] = self.name_edit.text()
            self.reach_data['Length'] = self.length_edit.value()
            self.reach_data['Slope'] = self.slope_edit.value()
            self.reach_data['W'] = self.width_edit.value()
            self.reach_data['D50'] = self.d50_edit.value()
            
            if self.d90_edit is not None:
                self.reach_data['D90'] = self.d90_edit.value()
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save changes: {str(e)}")
    
    def reset_values(self):
        """Reset all values to original."""
        self.name_edit.setText(str(self.original_data.get('Name', '')))
        self.length_edit.setValue(float(self.original_data.get('Length', 0)))
        self.slope_edit.setValue(float(self.original_data.get('Slope', 0)))
        self.width_edit.setValue(float(self.original_data.get('W', 0)))
        self.d50_edit.setValue(float(self.original_data.get('D50', 0)))
        
        if self.d90_edit is not None and 'D90' in self.original_data:
            self.d90_edit.setValue(float(self.original_data.get('D90', 0)))
    
    def get_updated_data(self):
        """Return the updated reach data."""
        return self.reach_data
