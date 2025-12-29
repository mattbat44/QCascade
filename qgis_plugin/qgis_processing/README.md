# QGIS Processing Script for D-CASCADE River Network Extraction

## Overview

This directory contains a QGIS Processing script that extracts river networks from Digital Elevation Models (DEMs) and prepares them for use with the D-CASCADE sediment transport model.

## Features

The script (`extract_river_network.py`) performs the following operations:

1. **DEM Preprocessing**: Breaches depressions and fills sinks to ensure proper flow routing
2. **Flow Analysis**: Calculates flow direction and flow accumulation using D8 algorithm
3. **Network Extraction**: Extracts river channels based on a user-defined minimum contributing area threshold
4. **Topology Building**: Creates network topology with unique reach IDs and node connections
5. **Attribute Calculation**: Computes reach attributes including:
   - Slope (from DEM)
   - Length (from geometry)
   - Elevation at nodes (from DEM)
   - Coordinates of nodes
   - Contributing area
6. **D-CASCADE Compatibility**: Generates all required attribute columns for D-CASCADE input

## Installation

### Method 1: Using the QGIS Python Console

1. Open QGIS
2. Go to `Plugins > Python Console`
3. Click the "Show Editor" button
4. Click "Open Script" and navigate to `extract_river_network.py`
5. Click "Run Script"

The algorithm will be available in the Processing Toolbox under **D-CASCADE > Extract River Network for D-CASCADE**.

### Method 2: Adding to Processing Scripts

1. Open QGIS
2. Go to `Processing > Toolbox`
3. Click the Python icon at the top of the Processing Toolbox
4. Select "Add Script to Toolbox..."
5. Navigate to and select `extract_river_network.py`
6. The algorithm will appear under **Scripts > D-CASCADE > Extract River Network for D-CASCADE**

### Method 3: Using the Scripts Folder

1. Copy `extract_river_network.py` to your QGIS user scripts folder:
   - Windows: `C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\processing\scripts`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/processing/scripts`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/processing/scripts`
2. Restart QGIS or refresh the Processing Toolbox
3. The script will appear under **Scripts > D-CASCADE**

## Usage

### Prerequisites

- QGIS 3.x with Processing Framework
- SAGA GIS tools installed and configured in QGIS
  - Go to `Processing > Options > Providers > SAGA` to configure SAGA
  - If SAGA is not installed, install it from: https://saga-gis.sourceforge.io/

### Input Requirements

1. **Digital Elevation Model (DEM)**:
   - Raster format (GeoTIFF, ASCII grid, etc.)
   - Projected coordinate system (not geographic)
   - Sufficient resolution for your study area
   - Should cover the entire catchment of interest

### Running the Algorithm

1. Open QGIS and load your DEM
2. Open the Processing Toolbox (`Processing > Toolbox`)
3. Navigate to **D-CASCADE > Extract River Network for D-CASCADE**
4. Double-click to open the algorithm dialog
5. Set the parameters:
   - **Input DEM**: Select your DEM raster layer
   - **Minimum Contributing Area (m²)**: Set the threshold for stream initiation
     - Typical values: 100,000 - 10,000,000 m² (0.1 - 10 km²)
     - Smaller values = denser network
     - Larger values = main channels only
   - **Output River Network**: Specify output shapefile path
6. Click "Run"

### Output

The script generates a polyline shapefile with the following attributes:

#### Mandatory Attributes (populated by script):
- `reach_id`: Unique identifier for each reach
- `FromN`: Upstream node ID
- `ToN`: Downstream node ID
- `Slope`: Reach slope (m/m)
- `Length`: Reach length (m)
- `el_FN`: Elevation at upstream node (m)
- `el_TN`: Elevation at downstream node (m)
- `x_FN`, `y_FN`: Coordinates of upstream node
- `x_TN`, `y_TN`: Coordinates of downstream node
- `Ad`: Contributing area (m²)
- `n`: Manning coefficient (initialized to 0.035)

#### Attributes to be Filled by User:
- `Wac`: Active channel width (m) - **REQUIRED**
- `Q`: Discharge (m³/s) - **REQUIRED** (or provide separate Q file)
- `D16`: 16th percentile grain size (m) - **REQUIRED**
- `D50`: 50th percentile grain size (m) - **REQUIRED**
- `D84`: 84th percentile grain size (m) - **REQUIRED**
- `deposit`: Initial deposit layer (m) - **REQUIRED**
- `tr_limit`: Transport limit - optional
- `directAd`: Direct contributing area (m²) - optional
- `StrO`: Stream order - optional (initialized to 1)

## Post-Processing

After running the script, you need to:

1. **Fill Required Attributes**: Open the output shapefile in QGIS and populate the required fields:
   - Use field calculator or manual entry
   - `Wac` can be estimated from hydraulic geometry relations
   - `D16`, `D50`, `D84` can be obtained from field measurements or literature
   - `deposit` can be set to a uniform value (e.g., 100,000 m)

2. **Prepare Discharge Data**: Create a CSV file with discharge time series for each reach
   - Format: rows = time steps, columns = reaches
   - See D-CASCADE documentation for details

3. **Verify Topology**: Check that the network topology is correct:
   - Each reach should have unique `FromN` and `ToN` values
   - Downstream reaches should connect properly
   - The outlet reach should have `FromN == ToN`

## Troubleshooting

### SAGA Tools Not Found
- Install SAGA GIS: https://saga-gis.sourceforge.io/
- Configure SAGA path in QGIS: `Processing > Options > Providers > SAGA`

### No Output Generated
- Check that DEM has no NoData values in the area of interest
- Try a larger minimum contributing area threshold
- Verify DEM is in a projected coordinate system

### Network Topology Issues
- Ensure DEM covers the entire catchment
- Check for DEM artifacts or errors
- Try adjusting the minimum contributing area threshold

### Script Errors
- Verify QGIS version is 3.x or higher
- Check that all required Python packages are available
- Review the QGIS log for detailed error messages

## Example Workflow

```python
# Example: Complete workflow from DEM to D-CASCADE input

# 1. Run the extraction script in QGIS GUI with:
#    - Input DEM: my_catchment_dem.tif
#    - Min Contributing Area: 1000000 m² (1 km²)
#    - Output: river_network_raw.shp

# 2. Load the output in QGIS and use Field Calculator to populate attributes:
#    - Wac: estimate from area (e.g., 0.5 * Ad^0.5)
#    - D16: 0.016 (16 mm, example value)
#    - D50: 0.050 (50 mm, example value)
#    - D84: 0.084 (84 mm, example value)
#    - deposit: 100000 (100 km initial deposit)

# 3. Save the edited shapefile as: river_network.shp

# 4. Prepare discharge CSV file: Q_timeseries.csv

# 5. Use in D-CASCADE user script:
#    filename_river_network = 'river_network.shp'
#    filename_q = 'Q_timeseries.csv'
```

## Technical Notes

- The script uses SAGA GIS algorithms for hydrological processing
- Flow direction is calculated using the D8 algorithm
- Network topology is built by matching endpoint coordinates
- Elevations are sampled directly from the filled DEM
- Contributing areas are derived from flow accumulation

## Contributing

To improve this script:
1. Test with various DEM resolutions and catchment sizes
2. Add support for alternative flow routing algorithms (D-infinity, MFD)
3. Implement automatic channel width estimation
4. Add stream order calculation using Strahler or Shreve methods

## Support

For issues or questions:
- Check the D-CASCADE documentation
- Review QGIS Processing documentation
- Open an issue in the D-CASCADE repository

## References

- D-CASCADE model: Schmitt et al. (2016), Tangi et al. (2022)
- SAGA GIS: https://saga-gis.sourceforge.io/
- QGIS Processing: https://docs.qgis.org/
