"""
@brief Inputs tab component for D-CASCADE parameters dock
@author Matt Adams
"""

from qgis.PyQt.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QPushButton, 
    QHBoxLayout, QLabel, QFileDialog, QSpacerItem,
    QMenu, QToolButton
)
from qgis.PyQt.QtCore import pyqtSignal
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMapLayerProxyModel
from ...compat import QToolButton_MenuButtonPopup, QSizePolicy_Minimum, QSizePolicy_Expanding
import csv


class InputsTab(QWidget):
    """Inputs tab with layer selector and discharge file."""
    
    layer_selected = pyqtSignal(object)  # Emits QgsVectorLayer
    discharge_path_changed = pyqtSignal(str)
    save_config_requested = pyqtSignal(str)
    load_config_requested = pyqtSignal(str)
    load_run_requested = pyqtSignal(str)
    run_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QFormLayout(self)
        
        # River Network Layer (QGIS layer selector)
        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.layer_combo.layerChanged.connect(self.on_layer_changed)
        layout.addRow("River Network Layer:", self.layer_combo)
        
        # Layer info label
        self.layer_info_label = QLabel("Select a vector layer with FromN, ToN attributes")
        self.layer_info_label.setWordWrap(True)
        layout.addRow("", self.layer_info_label)
        
        # Discharge CSV
        csv_layout = QHBoxLayout()
        self.csv_path = QLineEdit()
        self.csv_path.setToolTip("CSV file with water discharge per reach per time step.\nFormat: rows = time steps, columns = reaches.")
        self.csv_btn = QToolButton()
        self.csv_btn.setText("Browse...")
        self.csv_btn.clicked.connect(self.browse_csv)
        self.csv_btn.setPopupMode(QToolButton_MenuButtonPopup)
        csv_menu = QMenu(self.csv_btn)
        csv_menu.addAction("Browse...").triggered.connect(self.browse_csv)
        csv_menu.addAction("Create template").triggered.connect(self.create_discharge_template)
        self.csv_btn.setMenu(csv_menu)
        csv_layout.addWidget(self.csv_path)
        csv_layout.addWidget(self.csv_btn)
        layout.addRow("Discharge (.csv):", csv_layout)
        self.csv_path.textChanged.connect(lambda: self.discharge_path_changed.emit(self.csv_path.text()))

        # Optional overbank discharge thresholds
        overbank_layout = QHBoxLayout()
        self.overbank_csv_path = QLineEdit()
        self.overbank_csv_path.setToolTip(
            "CSV with one row per reach and columns: reach_id, Q_limit, W_overbank (width optional)."
        )
        self.overbank_csv_btn = QToolButton()
        self.overbank_csv_btn.setText("Browse...")
        self.overbank_csv_btn.clicked.connect(self.browse_overbank_csv)
        self.overbank_csv_btn.setPopupMode(QToolButton_MenuButtonPopup)
        overbank_menu = QMenu(self.overbank_csv_btn)
        overbank_menu.addAction("Browse...").triggered.connect(self.browse_overbank_csv)
        overbank_menu.addAction("Create template").triggered.connect(self.create_overbank_template)
        self.overbank_csv_btn.setMenu(overbank_menu)
        overbank_layout.addWidget(self.overbank_csv_path)
        overbank_layout.addWidget(self.overbank_csv_btn)
        layout.addRow("Overbank Q limit (.csv):", overbank_layout)
        
        # Output Name
        self.output_name = QLineEdit("simulation_output")
        self.output_name.setToolTip("Name of the output simulation files.")
        layout.addRow("Output Name:", self.output_name)
        
        # Output Directory
        out_layout = QHBoxLayout()
        self.output_dir = QLineEdit()
        self.output_dir.setToolTip("Directory to save simulation outputs (optional). If empty, a cascade_results folder next to the config will be used.")
        self.output_dir_btn = QPushButton("Browse...")
        self.output_dir_btn.clicked.connect(self.browse_output_dir)
        out_layout.addWidget(self.output_dir)
        out_layout.addWidget(self.output_dir_btn)
        layout.addRow("Output Directory:", out_layout)
        
        # Actions row
        actions_layout = QHBoxLayout()
        self.load_cfg_btn = QPushButton("Load Config...")
        self.load_cfg_btn.clicked.connect(self.on_load_config_clicked)
        self.load_run_btn = QPushButton("Load From Run...")
        self.load_run_btn.clicked.connect(self.on_load_run_clicked)
        self.save_btn = QPushButton("Save Config...")
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.run_btn = QPushButton("Run Simulation")
        self.run_btn.clicked.connect(lambda: self.run_requested.emit())
        for btn in (self.load_cfg_btn, self.load_run_btn, self.save_btn, self.run_btn):
            actions_layout.addWidget(btn)
        layout.addRow("Actions:", actions_layout)

        # Spacer to keep layout tidy if more widgets are added later
        layout.addItem(QSpacerItem(0, 0, QSizePolicy_Minimum, QSizePolicy_Expanding))
    
    def on_layer_changed(self, layer):
        """Handle layer selection change."""
        if layer is None:
            self.layer_info_label.setText("Select a vector layer with FromN, ToN attributes")
            return
        
        # Validate layer has required attributes
        required_fields = ['FromN', 'ToN']
        field_names = [field.name() for field in layer.fields()]
        missing_fields = [f for f in required_fields if f not in field_names]
        
        if missing_fields:
            self.layer_info_label.setText(
                f"<b>Warning:</b> Missing required fields: {', '.join(missing_fields)}"
            )
            self.layer_info_label.setStyleSheet("color: red;")
        else:
            self.layer_info_label.setText(f"Layer: {layer.name()}\nFields: {', '.join(field_names[:5])}...")
            self.layer_info_label.setStyleSheet("")
        
        self.layer_selected.emit(layer)
    
    def browse_csv(self):
        """Browse for discharge CSV file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Discharge CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self.csv_path.setText(path)

    def browse_overbank_csv(self):
        """Browse for overbank discharge threshold CSV file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Overbank Q CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self.overbank_csv_path.setText(path)

    def browse_output_dir(self):
        """Browse for output directory."""
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory", "")
        if path:
            self.output_dir.setText(path)
    
    def on_save_clicked(self):
        """Ask for path and emit save request."""
        path, _ = QFileDialog.getSaveFileName(self, "Save D-CASCADE config", "config.json", "JSON Files (*.json)")
        if path:
            self.save_config_requested.emit(path)

    def on_load_config_clicked(self):
        """Ask for config json and emit load request."""
        path, _ = QFileDialog.getOpenFileName(self, "Load D-CASCADE config", "", "JSON Files (*.json)")
        if path:
            self.load_config_requested.emit(path)

    def on_load_run_clicked(self):
        """Ask for model run file and emit load request."""
        path, _ = QFileDialog.getOpenFileName(self, "Load from run file", "", "Run Results (*.json);;All Files (*.*)")
        if path:
            self.load_run_requested.emit(path)
    
    def get_layer_path(self):
        """Get the file path of the selected layer."""
        layer = self.layer_combo.currentLayer()
        if layer is None:
            return None
        return layer.source()
    
    def _get_reach_ids(self):
        """Return sorted list of reach IDs from current layer (FromN field)."""
        layer = self.layer_combo.currentLayer()
        if layer is None:
            raise ValueError("Select a river network layer first.")
        from_idx = layer.fields().indexFromName("FromN")
        if from_idx < 0:
            raise ValueError("Layer is missing FromN field.")
        ids = [feat.attribute(from_idx) for feat in layer.getFeatures()]
        ids = [int(x) for x in ids if x is not None]
        if not ids:
            raise ValueError("No reaches found in layer.")
        return sorted(set(ids))
    
    def create_discharge_template(self):
        """Generate a zero-filled discharge CSV with rows=time, cols=reach order."""
        from qgis.PyQt.QtWidgets import QMessageBox
        from qgis.PyQt.QtCore import QUrl
        from qgis.PyQt.QtGui import QDesktopServices
        
        try:
            reach_ids = self._get_reach_ids()
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
        except Exception as e:
            QMessageBox.warning(self, "Cannot create template", str(e))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Discharge Template",
            "discharge_template.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not path:
            return

        try:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(reach_ids)
                row_zero = [0] * len(reach_ids)
                for _ in range(timescale):
                    writer.writerow(row_zero)
        except Exception as e:
            QMessageBox.critical(self, "Write Failed", f"Could not create template: {e}")
            return

        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception:
            pass

    def create_overbank_template(self):
        """Generate a CSV with one row per reach and columns reach_id,Q_limit,W_overbank."""
        from qgis.PyQt.QtWidgets import QMessageBox
        from qgis.PyQt.QtCore import QUrl
        from qgis.PyQt.QtGui import QDesktopServices
        
        try:
            reach_ids = self._get_reach_ids()
        except Exception as e:
            QMessageBox.warning(self, "Cannot create template", str(e))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Overbank Q Template",
            "overbank_q_template.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not path:
            return

        try:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["reach_id", "Q_limit", "W_overbank"])
                for rid in reach_ids:
                    writer.writerow([rid, 0, 0])
        except Exception as e:
            QMessageBox.critical(self, "Write Failed", f"Could not create template: {e}")
            return

        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception:
            pass
