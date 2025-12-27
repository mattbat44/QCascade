import io
import json
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QMessageBox
import folium
import geopandas as gpd

class MapWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("GIS Viewer", parent)
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)
        
        self.setWidget(self.container)
        
        # Initialize with a default map
        self.init_map()

    def init_map(self):
        """Initialize an empty map centered on a default location."""
        m = folium.Map(location=[45.0, 10.0], zoom_start=5, tiles="OpenStreetMap")
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
            gdf = gpd.read_file(shp_path)
            
            # Set default CRS to WGS84 if missing
            if not gdf.crs:
                gdf.set_crs("EPSG:4326", inplace=True)

            # Reproject to WGS84 (EPSG:4326) for Folium if needed
            if gdf.crs.to_string() != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")
            
            # Calculate center
            center_lat = gdf.geometry.centroid.y.mean()
            center_lon = gdf.geometry.centroid.x.mean()
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles="OpenStreetMap")
            
            # Add the GeoJSON to the map
            folium.GeoJson(
                gdf,
                name="River Network",
                style_function=lambda x: {'color': 'blue', 'weight': 3},
                tooltip=folium.GeoJsonTooltip(fields=list(gdf.columns)[:5]) # Show first 5 columns as tooltip
            ).add_to(m)
            
            folium.LayerControl().add_to(m)
            
            self.set_map(m)
            
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Shapefile", str(e))
