#!/usr/bin/env python3
"""
QGIS Processing Script for D-CASCADE River Network Extraction from DEM

This script provides a QGIS Processing algorithm to extract river networks from
Digital Elevation Models (DEMs) and prepare them for use with D-CASCADE.

The script performs the following steps:
1. Breach depressions in the DEM
2. Fill sinks
3. Calculate flow direction
4. Calculate flow accumulation
5. Extract river network based on minimum contributing area threshold
6. Build river network topology (reach_id, FromN, ToN)
7. Calculate reach attributes (slope, elevation, length)
8. Generate all required attribute columns for D-CASCADE

@author: D-CASCADE Development Team
@date: 2025
"""

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorDestination,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsWkbTypes,
    QgsVectorLayer,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsRasterLayer,
    QgsRaster
)
from qgis import processing
from PyQt5.QtCore import QVariant
import numpy as np


class RiverNetworkExtractionAlgorithm(QgsProcessingAlgorithm):
    """
    QGIS Processing Algorithm for extracting river networks from DEM
    for use with D-CASCADE sediment transport model.
    
    Requirements:
    - QGIS 3.x or higher
    - SAGA GIS 7.x or higher (for hydrological processing)
    - PyQt5
    
    Limitations:
    - Assumes square or near-square DEM pixels
    - Best suited for projected coordinate systems
    - May require parameter tuning for different catchment sizes
    """
    
    # Algorithm parameters
    INPUT_DEM = 'INPUT_DEM'
    MIN_CONTRIBUTING_AREA = 'MIN_CONTRIBUTING_AREA'
    OUTPUT = 'OUTPUT'
    
    # Constants
    MIN_SLOPE = 0.0001  # Minimum slope threshold (m/m) to avoid zero slopes
    NODE_PRECISION = 3  # Decimal places for rounding node coordinates
    
    def tr(self, string):
        """Returns a translatable string"""
        return string
    
    def createInstance(self):
        """Create a new instance of the algorithm"""
        return RiverNetworkExtractionAlgorithm()
    
    def name(self):
        """Algorithm identifier"""
        return 'extract_river_network_dcascade'
    
    def displayName(self):
        """User-friendly algorithm name"""
        return self.tr('Extract River Network for D-CASCADE')
    
    def group(self):
        """Group identifier"""
        return self.tr('D-CASCADE')
    
    def groupId(self):
        """Group identifier"""
        return 'dcascade'
    
    def shortHelpString(self):
        """Help documentation for the algorithm"""
        return self.tr("""
        Extract river network from a Digital Elevation Model (DEM) and prepare
        it for use with the D-CASCADE sediment transport model.
        
        This algorithm performs the following steps:
        1. Breach depressions in the DEM using SAGA GIS
        2. Fill sinks to ensure proper flow routing
        3. Calculate flow direction using D8 algorithm
        4. Calculate flow accumulation
        5. Extract river network based on minimum contributing area
        6. Build river network topology with unique reach IDs
        7. Calculate reach attributes (slope, length, elevations)
        8. Generate all required D-CASCADE attribute columns
        
        Parameters:
        - Input DEM: Digital Elevation Model raster layer
        - Minimum Contributing Area: Threshold in square meters to define stream channels
        - Output: Vector layer (shapefile) with river network and all D-CASCADE attributes
        
        Output attributes include:
        - reach_id: Unique identifier for each reach
        - FromN: Upstream node ID
        - ToN: Downstream node ID
        - Slope: Reach slope (m/m)
        - Length: Reach length (m)
        - el_FN: Elevation at upstream node (m)
        - el_TN: Elevation at downstream node (m)
        - x_FN, y_FN: Coordinates of upstream node
        - x_TN, y_TN: Coordinates of downstream node
        - Wac: Active channel width (m) - initialized to 0
        - Q: Discharge (m³/s) - initialized to 0
        - n: Manning coefficient - initialized to 0.035
        - D16, D50, D84: Grain size percentiles (m) - initialized to 0
        - tr_limit: Transport limit - initialized to 0
        - Ad: Contributing area (m²)
        - directAd: Direct contributing area (m²) - initialized to 0
        - StrO: Stream order - initialized to 1
        - deposit: Initial deposit (m) - initialized to 0
        """)
    
    def initAlgorithm(self, config=None):
        """Define algorithm inputs and outputs"""
        
        # Input DEM raster layer
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DEM,
                self.tr('Input DEM'),
                None
            )
        )
        
        # Minimum contributing area parameter (in square meters)
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_CONTRIBUTING_AREA,
                self.tr('Minimum Contributing Area (m²)'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1000000.0,  # 1 km²
                minValue=1000.0  # Minimum 1000 m²
            )
        )
        
        # Output vector layer (shapefile)
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                self.tr('Output River Network'),
                type=QgsProcessing.TypeVectorLine
            )
        )
    
    def processAlgorithm(self, parameters, context, feedback):
        """
        Main algorithm processing method
        """
        
        # Get input parameters
        dem = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        min_contrib_area = self.parameterAsDouble(parameters, self.MIN_CONTRIBUTING_AREA, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        
        if dem is None:
            raise QgsProcessingException(self.tr('Invalid DEM layer'))
        
        feedback.pushInfo(f'Input DEM: {dem.name()}')
        feedback.pushInfo(f'Minimum Contributing Area: {min_contrib_area} m²')
        
        # Step 1: Breach depressions using SAGA
        feedback.pushInfo('Step 1/8: Breaching depressions...')
        feedback.setProgress(10)
        
        try:
            breached_result = processing.run(
                'saga:breachdepressions',
                {
                    'DEM': dem,
                    'BREACH': 'TEMPORARY_OUTPUT'
                },
                context=context,
                feedback=feedback
            )
            breached_dem = breached_result['BREACH']
        except Exception as e:
            feedback.reportError(f'Breach depressions failed: {str(e)}')
            feedback.pushInfo('Continuing with original DEM...')
            breached_dem = dem
        
        # Step 2: Fill sinks
        feedback.pushInfo('Step 2/8: Filling sinks...')
        feedback.setProgress(20)
        
        try:
            filled_result = processing.run(
                'saga:fillsinks',
                {
                    'DEM': breached_dem,
                    'RESULT': 'TEMPORARY_OUTPUT'
                },
                context=context,
                feedback=feedback
            )
            filled_dem = filled_result['RESULT']
        except Exception as e:
            feedback.reportError(f'Fill sinks failed: {str(e)}')
            feedback.pushInfo('Continuing with breached DEM...')
            filled_dem = breached_dem
        
        # Step 3: Calculate flow direction (D8)
        feedback.pushInfo('Step 3/8: Calculating flow direction...')
        feedback.setProgress(30)
        
        flow_dir_result = processing.run(
            'saga:flowaccumulationtopdown',
            {
                'ELEVATION': filled_dem,
                'FLOW': 'TEMPORARY_OUTPUT',
                'FLOW_UNIT': 0,  # Number of cells
                'METHOD': 0,  # Deterministic 8
            },
            context=context,
            feedback=feedback
        )
        
        flow_accumulation = flow_dir_result['FLOW']
        
        # Step 4: Calculate contributing area from flow accumulation
        feedback.pushInfo('Step 4/8: Calculating contributing area...')
        feedback.setProgress(40)
        
        # Get cell size to convert cell count to area
        # Note: This assumes square or near-square pixels. For significantly
        # non-square pixels, consider using a more sophisticated area calculation.
        cell_size_x = dem.rasterUnitsPerPixelX()
        cell_size_y = dem.rasterUnitsPerPixelY()
        cell_area = cell_size_x * cell_size_y
        
        # Step 5: Extract channel network
        feedback.pushInfo('Step 5/8: Extracting channel network...')
        feedback.setProgress(50)
        
        # Calculate threshold in number of cells
        threshold_cells = min_contrib_area / cell_area
        
        channel_result = processing.run(
            'saga:channelnetwork',
            {
                'ELEVATION': filled_dem,
                'INIT_GRID': flow_accumulation,
                'INIT_METHOD': 2,  # Greater than threshold
                'INIT_VALUE': threshold_cells,
                'SHAPES': 'TEMPORARY_OUTPUT',
            },
            context=context,
            feedback=feedback
        )
        
        channel_network = channel_result['SHAPES']
        
        # Step 6: Build network topology
        feedback.pushInfo('Step 6/8: Building network topology...')
        feedback.setProgress(60)
        
        # Load channel network as vector layer
        if isinstance(channel_network, str):
            channel_layer = QgsVectorLayer(channel_network, "channels", "ogr")
        else:
            channel_layer = channel_network
        
        # Step 7: Create output fields with D-CASCADE required attributes
        feedback.pushInfo('Step 7/8: Creating attribute table...')
        feedback.setProgress(70)
        
        fields = QgsFields()
        fields.append(QgsField('reach_id', QVariant.Int))
        fields.append(QgsField('FromN', QVariant.Int))
        fields.append(QgsField('ToN', QVariant.Int))
        fields.append(QgsField('Slope', QVariant.Double))
        fields.append(QgsField('Wac', QVariant.Double))
        fields.append(QgsField('Q', QVariant.Double))
        fields.append(QgsField('n', QVariant.Double))
        fields.append(QgsField('D16', QVariant.Double))
        fields.append(QgsField('D50', QVariant.Double))
        fields.append(QgsField('D84', QVariant.Double))
        fields.append(QgsField('tr_limit', QVariant.Double))
        fields.append(QgsField('Length', QVariant.Double))
        fields.append(QgsField('x_FN', QVariant.Double))
        fields.append(QgsField('y_FN', QVariant.Double))
        fields.append(QgsField('x_TN', QVariant.Double))
        fields.append(QgsField('y_TN', QVariant.Double))
        fields.append(QgsField('el_FN', QVariant.Double))
        fields.append(QgsField('el_TN', QVariant.Double))
        fields.append(QgsField('Ad', QVariant.Double))
        fields.append(QgsField('directAd', QVariant.Double))
        fields.append(QgsField('StrO', QVariant.Int))
        fields.append(QgsField('deposit', QVariant.Double))
        
        # Step 8: Process features and populate attributes
        feedback.pushInfo('Step 8/8: Processing features and calculating attributes...')
        feedback.setProgress(80)
        
        # Create output sink
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            dem.crs()
        )
        
        if sink is None:
            raise QgsProcessingException(self.tr('Failed to create output'))
        
        # Process each feature
        features = channel_layer.getFeatures()
        total = channel_layer.featureCount()
        
        # Build network topology
        node_map = {}  # Map coordinates to node IDs
        next_node_id = 1
        reach_id = 1
        
        output_features = []
        
        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break
            
            geom = feature.geometry()
            if geom.isMultipart():
                lines = geom.asMultiPolyline()
            else:
                lines = [geom.asPolyline()]
            
            for line in lines:
                if len(line) < 2:
                    continue
                
                # Get start and end points
                start_point = line[0]
                end_point = line[-1]
                
                # Create coordinate keys for node mapping
                # Coordinates are rounded to avoid floating-point comparison issues
                start_key = (round(start_point.x(), self.NODE_PRECISION), 
                           round(start_point.y(), self.NODE_PRECISION))
                end_key = (round(end_point.x(), self.NODE_PRECISION), 
                         round(end_point.y(), self.NODE_PRECISION))
                
                # Assign node IDs
                if start_key not in node_map:
                    node_map[start_key] = next_node_id
                    next_node_id += 1
                from_node = node_map[start_key]
                
                if end_key not in node_map:
                    node_map[end_key] = next_node_id
                    next_node_id += 1
                to_node = node_map[end_key]
                
                # Sample elevations from DEM
                start_elev = self.sample_raster_at_point(filled_dem, start_point)
                end_elev = self.sample_raster_at_point(filled_dem, end_point)
                
                # Calculate length
                length = geom.length()
                
                # Calculate slope
                if length > 0 and start_elev is not None and end_elev is not None:
                    slope = abs(start_elev - end_elev) / length
                    # Ensure slope is positive and above minimum threshold
                    if slope < self.MIN_SLOPE:
                        slope = self.MIN_SLOPE
                else:
                    slope = 0.001  # Default slope for missing data
                
                # Sample flow accumulation for contributing area
                contrib_area = self.sample_raster_at_point(flow_accumulation, end_point)
                if contrib_area is not None:
                    # Convert from cell count to area
                    contrib_area = contrib_area * cell_area
                else:
                    contrib_area = 0.0
                
                # Create output feature
                out_feature = QgsFeature(fields)
                out_feature.setGeometry(QgsGeometry.fromPolylineXY(line))
                
                # Set attributes
                out_feature.setAttribute('reach_id', reach_id)
                out_feature.setAttribute('FromN', from_node)
                out_feature.setAttribute('ToN', to_node)
                out_feature.setAttribute('Slope', slope)
                out_feature.setAttribute('Wac', 0.0)  # To be filled by user
                out_feature.setAttribute('Q', 0.0)  # To be filled by user
                out_feature.setAttribute('n', 0.035)  # Default Manning coefficient
                out_feature.setAttribute('D16', 0.0)  # To be filled by user
                out_feature.setAttribute('D50', 0.0)  # To be filled by user
                out_feature.setAttribute('D84', 0.0)  # To be filled by user
                out_feature.setAttribute('tr_limit', 0.0)  # To be filled by user
                out_feature.setAttribute('Length', length)
                out_feature.setAttribute('x_FN', start_point.x())
                out_feature.setAttribute('y_FN', start_point.y())
                out_feature.setAttribute('x_TN', end_point.x())
                out_feature.setAttribute('y_TN', end_point.y())
                out_feature.setAttribute('el_FN', start_elev if start_elev is not None else 0.0)
                out_feature.setAttribute('el_TN', end_elev if end_elev is not None else 0.0)
                out_feature.setAttribute('Ad', contrib_area)
                out_feature.setAttribute('directAd', 0.0)  # To be filled by user
                out_feature.setAttribute('StrO', 1)  # Default stream order
                out_feature.setAttribute('deposit', 0.0)  # To be filled by user
                
                sink.addFeature(out_feature)
                reach_id += 1
            
            feedback.setProgress(80 + int(20 * current / total))
        
        feedback.pushInfo(f'Successfully extracted {reach_id - 1} reaches')
        feedback.pushInfo('Note: Please fill in the following attributes before using with D-CASCADE:')
        feedback.pushInfo('  - Wac (active channel width)')
        feedback.pushInfo('  - Q (discharge) - or provide separate Q file')
        feedback.pushInfo('  - D16, D50, D84 (grain size distributions)')
        feedback.pushInfo('  - deposit (initial deposit layer)')
        
        return {self.OUTPUT: dest_id}
    
    def sample_raster_at_point(self, raster_layer, point):
        """
        Sample raster value at a specific point
        """
        try:
            if isinstance(raster_layer, str):
                raster = QgsRasterLayer(raster_layer, "temp")
            else:
                raster = raster_layer
            
            provider = raster.dataProvider()
            ident = provider.identify(point, QgsRaster.IdentifyFormatValue)
            
            if ident.isValid():
                values = ident.results()
                if values and 1 in values:
                    return float(values[1])
            return None
        except Exception:
            return None
