import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QDockWidget, QVBoxLayout, QWidget, QMessageBox,
    QHBoxLayout, QPushButton, QMenu, QFileDialog, QGraphicsView, QGraphicsScene
)
from PyQt6.QtCore import pyqtSignal, Qt, QPointF
from PyQt6.QtGui import QPen, QColor, QPainterPath
import geopandas as gpd
import pandas as pd

from gui.widgets.reach_editor_dialog import ReachEditorDialog


class MapWidget(QDockWidget):
    reach_edited = pyqtSignal(int, dict)  # Signal emitted when reach is edited (FromN, updated_data)
    
    def __init__(self, parent=None):
        super().__init__("Map", parent)
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar for map actions
        self.create_toolbar()
        
        # Graphics view for Qt-based GIS rendering
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(self.view.renderHints())
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setMouseTracking(True)
        self.view.viewport().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.viewport().customContextMenuRequested.connect(self.on_context_menu)
        self.view.mousePressEvent = self.on_mouse_press
        self.layout.addWidget(self.view)
        
        self.setWidget(self.container)
        
        # Store geodataframe and shapefile path
        self.gdf = None
        self.shapefile_path = None
        self.selected_reach_id = None
        self.reach_names = {}  # Dictionary to store custom reach names
        # External inputs mapping: {reach_idx: [csv_paths]}
        self.external_inputs_mapping = {}
        
        # Initialize empty scene
        self.refresh_map()

    def create_toolbar(self):
        """Create toolbar with map actions."""
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(2, 2, 2, 2)
        
        self.edit_btn = QPushButton("Edit Selected Reach")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_selected_reach)
        toolbar_layout.addWidget(self.edit_btn)
        
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_shapefile)
        toolbar_layout.addWidget(self.save_btn)
        
        self.refresh_btn = QPushButton("Refresh Map")
        self.refresh_btn.clicked.connect(self.refresh_map)
        toolbar_layout.addWidget(self.refresh_btn)
        
        toolbar_layout.addStretch()
        
        self.layout.addWidget(toolbar_widget)
    
    def clear_scene(self):
        self.scene.clear()

    def load_shapefile(self, shp_path):
        """Load a shapefile and display it on the map."""
        try:
            self.shapefile_path = shp_path
            self.gdf = gpd.read_file(shp_path)
            
            # Add Name column if not present
            if 'Name' not in self.gdf.columns:
                self.gdf['Name'] = ''
            
            # Load custom names if they exist
            self.load_reach_names()
            
            # Set default CRS to WGS84 if missing
            if not self.gdf.crs:
                self.gdf.set_crs("EPSG:4326", inplace=True)

            # Reproject to WGS84 (EPSG:4326) for display if needed
            if self.gdf.crs.to_string() != "EPSG:4326":
                self.gdf = self.gdf.to_crs("EPSG:4326")
            
            # Load external inputs mapping if available
            self.load_external_inputs_mapping()
            self.render_map()
            
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Shapefile", str(e))
    
    def render_map(self):
        """Render the current geodataframe onto the QGraphicsScene."""
        self.clear_scene()
        if self.gdf is None or self.gdf.empty:
            return
        # Determine bounds
        xs = []
        ys = []
        for geom in self.gdf.geometry:
            for x, y in geom.coords:
                xs.append(x)
                ys.append(y)
        if not xs or not ys:
            return
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        dx = max(maxx - minx, 1e-9)
        dy = max(maxy - miny, 1e-9)
        # Simple scaling to view coordinates
        width = 1000.0
        height = 600.0
        sx = width / dx
        sy = -height / dy  # invert Y for screen
        tx = -minx * sx
        ty = maxy * (-sy)

        # Draw reaches
        self.items_by_reach = {}
        for _, row in self.gdf.iterrows():
            geom = row.geometry
            from_n = int(row['FromN']) if 'FromN' in row else None
            if geom is None or from_n is None:
                continue
            pts = [QPointF(x * sx + tx, y * sy + ty) for x, y in geom.coords]
            # Create polyline
            pen = QPen(QColor('#1f77b4'), 3)
            if self.selected_reach_id == from_n:
                pen = QPen(QColor('red'), 5)
            if not pts:
                continue
            path = QPainterPath(pts[0])
            for p in pts[1:]:
                path.lineTo(p)
            item = self.scene.addPath(path, pen)
            item.setData(0, from_n)
            self.items_by_reach[from_n] = item
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def refresh_map(self):
        """Refresh the map display."""
        self.render_map()
    
    def edit_selected_reach(self):
        """Open dialog to edit the selected reach."""
        if self.selected_reach_id is None:
            QMessageBox.warning(self, "No Selection", "Please select a reach first by clicking on it.")
            return
        
        # Find reach in geodataframe
        reach_row = self.gdf[self.gdf['FromN'] == self.selected_reach_id]
        if reach_row.empty:
            QMessageBox.warning(self, "Error", "Selected reach not found in data.")
            return
        
        reach_data = reach_row.iloc[0].to_dict()
        
        # Open editor dialog
        dialog = ReachEditorDialog(reach_data, self)
        if dialog.exec():
            updated_data = dialog.get_updated_data()
            self.update_reach_data(self.selected_reach_id, updated_data)
    
    def update_reach_data(self, from_n, updated_data):
        """Update reach data in the geodataframe."""
        try:
            idx = self.gdf[self.gdf['FromN'] == from_n].index[0]
            
            # Update editable fields
            for key in ['Name', 'Length', 'Slope', 'W', 'D50', 'D90']:
                if key in updated_data and key in self.gdf.columns:
                    self.gdf.at[idx, key] = updated_data[key]
            
            # Store custom name
            if updated_data.get('Name'):
                self.reach_names[from_n] = updated_data['Name']
                self.save_reach_names()
            
            self.save_btn.setEnabled(True)
            self.render_map()
            
            # Emit signal
            self.reach_edited.emit(from_n, updated_data)
            
            QMessageBox.information(self, "Success", "Reach data updated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update reach: {str(e)}")

    def on_mouse_press(self, event):
        pos = self.view.mapToScene(event.pos())
        # Find nearest item by boundingRect contains
        found = None
        for from_n, item in self.items_by_reach.items():
            if item.boundingRect().translated(item.pos()).contains(pos):
                found = from_n
                break
        if found is not None:
            self.selected_reach_id = found
            self.render_map()
        # call base behavior for panning
        return QGraphicsView.mousePressEvent(self.view, event)

    def on_context_menu(self, pos):
        # Context menu relative to viewport
        menu = QMenu(self)
        edit_action = menu.addAction("Edit Selected Reach")
        attach_action = menu.addAction("Attach External Input CSV...")
        action = menu.exec(self.view.viewport().mapToGlobal(pos))
        if action == edit_action:
            self.edit_selected_reach()
        elif action == attach_action:
            self.attach_external_csv()

    def attach_external_csv(self):
        if self.selected_reach_id is None:
            QMessageBox.warning(self, "No Selection", "Select a reach first.")
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Select External Input CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return
        self.external_inputs_mapping.setdefault(int(self.selected_reach_id), []).append(file_path)
        self.save_external_inputs_mapping()
        QMessageBox.information(self, "Attached", f"Attached CSV to reach {self.selected_reach_id}.")
    
    def save_shapefile(self):
        """Save the modified geodataframe back to shapefile."""
        if self.gdf is None or self.shapefile_path is None:
            QMessageBox.warning(self, "No Data", "No shapefile loaded to save.")
            return
        
        try:
            # Reproject back to original CRS if needed
            original_gdf = gpd.read_file(self.shapefile_path)
            if original_gdf.crs:
                gdf_to_save = self.gdf.to_crs(original_gdf.crs)
            else:
                gdf_to_save = self.gdf
            
            # Save to file
            gdf_to_save.to_file(self.shapefile_path)
            self.save_btn.setEnabled(False)
            
            QMessageBox.information(self, "Success", "Shapefile saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save shapefile: {str(e)}")
    
    def load_reach_names(self):
        """Load custom reach names from JSON file."""
        if self.shapefile_path is None:
            return
        
        names_file = Path(self.shapefile_path).parent / 'reach_names.json'
        if names_file.exists():
            try:
                with open(names_file, 'r') as f:
                    self.reach_names = json.load(f)
                
                # Apply names to geodataframe
                for from_n, name in self.reach_names.items():
                    idx = self.gdf[self.gdf['FromN'] == int(from_n)].index
                    if not idx.empty:
                        self.gdf.at[idx[0], 'Name'] = name
            except Exception as e:
                print(f"Warning: Could not load reach names: {e}")
    
    def save_reach_names(self):
        """Save custom reach names to JSON file."""
        if self.shapefile_path is None:
            return
        
        names_file = Path(self.shapefile_path).parent / 'reach_names.json'
        try:
            with open(names_file, 'w') as f:
                json.dump(self.reach_names, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save reach names: {e}")

    def load_external_inputs_mapping(self):
        if self.shapefile_path is None:
            return
        mapping_file = Path(self.shapefile_path).parent / 'external_inputs_mapping.json'
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r') as f:
                    self.external_inputs_mapping = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load external inputs mapping: {e}")

    def save_external_inputs_mapping(self):
        if self.shapefile_path is None:
            return
        mapping_file = Path(self.shapefile_path).parent / 'external_inputs_mapping.json'
        try:
            with open(mapping_file, 'w') as f:
                json.dump(self.external_inputs_mapping, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save external inputs mapping: {e}")

    def get_external_inputs_config(self):
        """Return external inputs configuration compatible with JSON runner."""
        if not self.external_inputs_mapping:
            return None
        per_reach = []
        for reach_str, paths in self.external_inputs_mapping.items():
            reach_idx = int(reach_str)
            for p in paths:
                per_reach.append({"reach_idx": reach_idx, "path": p})
        return {
            "per_reach_csvs": per_reach,
            "grain_unit": "mm",
            "default_sigma_g": 1.6
        }
