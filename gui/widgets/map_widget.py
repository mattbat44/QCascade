import io
import json
from pathlib import Path
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QDockWidget, QVBoxLayout, QWidget, QMessageBox, 
    QHBoxLayout, QPushButton, QToolBar, QMenu
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction
import folium
from folium.plugins import Draw
import geopandas as gpd
import pandas as pd

from gui.widgets.reach_editor_dialog import ReachEditorDialog


class MapWidget(QDockWidget):
    reach_edited = pyqtSignal(int, dict)  # Signal emitted when reach is edited (FromN, updated_data)
    
    def __init__(self, parent=None):
        super().__init__("GIS Viewer", parent)
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar for map actions
        self.create_toolbar()
        
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)
        
        self.setWidget(self.container)
        
        # Store geodataframe and shapefile path
        self.gdf = None
        self.shapefile_path = None
        self.selected_reach_id = None
        self.reach_names = {}  # Dictionary to store custom reach names
        
        # Initialize with a default map
        self.init_map()

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
    
    def init_map(self):
        """Initialize an empty map centered on a default location."""
        m = folium.Map(
            location=[45.0, 10.0], 
            zoom_start=5, 
            tiles="OpenStreetMap",
            prefer_canvas=True
        )
        self.set_map(m)

    def set_map(self, m):
        """Render a folium map in the web view."""
        data = io.BytesIO()
        m.save(data, close_file=False)
        html = data.getvalue().decode()
        self.web_view.setHtml(html)

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

            # Reproject to WGS84 (EPSG:4326) for Folium if needed
            if self.gdf.crs.to_string() != "EPSG:4326":
                self.gdf = self.gdf.to_crs("EPSG:4326")
            
            self.render_map()
            
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Shapefile", str(e))
    
    def render_map(self):
        """Render the current geodataframe on the map."""
        if self.gdf is None:
            return
        
        # Calculate center
        center_lat = self.gdf.geometry.centroid.y.mean()
        center_lon = self.gdf.geometry.centroid.x.mean()
        
        m = folium.Map(
            location=[center_lat, center_lon], 
            zoom_start=10, 
            tiles="OpenStreetMap",
            prefer_canvas=True
        )
        
        # Create tooltip fields including names
        tooltip_fields = ['FromN', 'ToN', 'Length', 'Slope', 'W', 'D50', 'Name']
        tooltip_fields = [f for f in tooltip_fields if f in self.gdf.columns]
        
        # Add the GeoJSON to the map with improved styling
        def style_function(feature):
            from_n = feature['properties'].get('FromN', None)
            if from_n == self.selected_reach_id:
                return {'color': 'red', 'weight': 5, 'opacity': 0.8}
            return {'color': '#1f77b4', 'weight': 3, 'opacity': 0.7}
        
        def highlight_function(feature):
            return {'color': 'yellow', 'weight': 5, 'opacity': 1}
        
        geojson = folium.GeoJson(
            self.gdf,
            name="River Network",
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=folium.GeoJsonTooltip(
                fields=tooltip_fields,
                aliases=[f.replace('_', ' ').title() + ':' for f in tooltip_fields],
                sticky=False
            )
        )
        geojson.add_to(m)
        
        # Add reach labels if names are provided
        for idx, row in self.gdf.iterrows():
            if row.get('Name', ''):
                centroid = row.geometry.centroid
                folium.Marker(
                    location=[centroid.y, centroid.x],
                    icon=folium.DivIcon(html=f'''
                        <div style="
                            font-size: 10px; 
                            color: white; 
                            background-color: rgba(0,0,0,0.7); 
                            padding: 2px 5px; 
                            border-radius: 3px;
                            white-space: nowrap;
                        ">
                            {row['Name']}
                        </div>
                    ''')
                ).add_to(m)
        
        folium.LayerControl().add_to(m)
        
        self.set_map(m)
    
    def refresh_map(self):
        """Refresh the map display."""
        if self.gdf is not None:
            self.render_map()
        else:
            self.init_map()
    
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
