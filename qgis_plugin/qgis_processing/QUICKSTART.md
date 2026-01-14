# Quick Start Guide: River Network Extraction for D-CASCADE

This guide provides a step-by-step example of extracting a river network from a DEM and preparing it for use with D-CASCADE.

## Prerequisites

Before you begin, ensure you have:
- QGIS 3.x installed
- SAGA GIS installed and configured in QGIS
- A DEM raster file of your study area
- The `extract_river_network.py` script added to QGIS (see main README.md)

## Step-by-Step Workflow

### 1. Load Your DEM in QGIS

1. Open QGIS
2. Add your DEM raster layer: `Layer > Add Layer > Add Raster Layer`
3. Verify the DEM:
   - Check coordinate system (should be projected, not geographic)
   - Inspect for NoData values or artifacts
   - Note the resolution and extent

### 2. Run the River Network Extraction Script

1. Open Processing Toolbox: `Processing > Toolbox`
2. Navigate to: `D-CASCADE > Extract River Network for D-CASCADE`
3. Configure parameters:

   **Input DEM**: Select your DEM layer from the dropdown
   
   **Minimum Contributing Area**: Choose threshold based on your needs
   - Small catchment (<100 km²): Try 100,000 - 500,000 m²
   - Medium catchment (100-1000 km²): Try 500,000 - 2,000,000 m²
   - Large catchment (>1000 km²): Try 2,000,000 - 10,000,000 m²
   
   **Output River Network**: Specify output path (e.g., `my_river_network.shp`)

4. Click "Run"
5. Wait for processing to complete (may take several minutes for large DEMs)

### 3. Inspect the Output

1. The output shapefile will be added to QGIS automatically
2. Open the attribute table to verify fields
3. Check the network visually:
   - Does it follow the valley bottoms?
   - Are all major tributaries included?
   - Is the network too dense or too sparse?
4. If needed, adjust the minimum contributing area and re-run

### 4. Fill Required Attributes

The script creates all columns but some need to be populated with actual data:

#### Method A: Using Field Calculator (for uniform values)

1. Open attribute table
2. Enable editing (pencil icon)
3. Open Field Calculator (Ctrl+F)
4. Update field with expression:

**Example: Set deposit to 100,000 m**
```
Update existing field: deposit
Expression: 100000
```

**Example: Estimate channel width from contributing area**
```
Update existing field: Wac
Expression: 0.5 * power("Ad", 0.5) / 1000
```
(This uses a simple width-area relationship)

**Example: Set grain sizes**
```
D16: 0.016  (16 mm)
D50: 0.050  (50 mm)
D84: 0.084  (84 mm)
```

#### Method B: Join Data from External Sources

If you have field measurements or other data sources:

1. Prepare a CSV with `reach_id` and your data columns
2. Use QGIS join: `Layer Properties > Joins`
3. Join based on `reach_id`
4. Use Field Calculator to copy joined values to permanent fields

#### Method C: Manual Entry (for small networks)

For networks with few reaches, you can manually enter values in the attribute table.

### 5. Create Discharge Time Series

D-CASCADE requires a discharge file (CSV format):

**Format**: 
- Rows: Time steps (e.g., daily, hourly)
- Columns: Reaches (matching the order or names in your shapefile)
- First column: Date/time (optional but recommended)

**Example CSV structure**:
```
yyyy/mm/dd,reach_1,reach_2,reach_3
2020-01-01,10.5,15.2,25.8
2020-01-02,12.3,17.1,28.5
2020-01-03,11.8,16.5,27.2
```

You can generate this from:
- Hydrological models
- Gauging station data
- Rainfall-runoff calculations
- Synthetic time series

### 6. Verify Your Network

Before using with D-CASCADE, verify:

**Topology**:
- Each reach has unique `reach_id`
- `FromN` and `ToN` create a connected network
- Outlet reach has `FromN == ToN`
- No isolated reaches (unless intended)

**Attributes**:
- No zero or negative slopes
- Channel widths are reasonable
- Grain sizes follow D16 < D50 < D84
- All required fields are filled

**Spatial**:
- Network flows downstream consistently
- Reaches connect at nodes
- No gaps or overlaps

### 7. Use with D-CASCADE

Now you can use your network with D-CASCADE:

```python
# In your D-CASCADE user script:

# Load the river network
filename_river_network = 'path/to/my_river_network.shp'
reach_data_df = read_network(filename_river_network)
reach_data = ReachData(reach_data_df)

# Load discharge data
filename_q = 'path/to/Q_timeseries.csv'
Q = extract_Q(filename_q)

# Continue with D-CASCADE setup...
```

## Tips and Best Practices

### DEM Preparation
- Use a DEM with appropriate resolution for your study area
  - High resolution (1-10m): Small catchments, detailed studies
  - Medium resolution (10-30m): Regional studies
  - Coarse resolution (30-90m): Large river basins
- Pre-process DEM if needed (remove artifacts, fill small depressions)
- Ensure DEM covers entire catchment

### Threshold Selection
- Start with a larger threshold for initial testing
- Refine based on validation data (maps, satellite imagery)
- Consider:
  - Available discharge data (need Q for each reach)
  - Computational resources
  - Level of detail required for your study

### Channel Width Estimation
If you don't have measured widths, use hydraulic geometry:
- `Wac = a * Ad^b` where typically b ≈ 0.5, a ≈ 0.01-0.1
- Adjust coefficients based on regional characteristics
- Validate against satellite imagery or field data

### Grain Size Estimation
- Use field measurements if available
- Literature values for similar catchments
- Regional sediment studies
- Grain size maps or models

### Quality Control
1. Visual inspection in QGIS
2. Compare with existing stream networks
3. Validate against satellite imagery
4. Check topology using QGIS topology checker
5. Test with a short D-CASCADE run before full simulation

## Troubleshooting Common Issues

### Network Too Dense
- Increase minimum contributing area
- Check DEM for artifacts
- Use pre-processed DEM with fewer spurious depressions

### Network Too Sparse
- Decrease minimum contributing area
- Verify DEM covers full catchment
- Check for DEM issues (NoData, poor quality)

### Disconnected Reaches
- Usually caused by DEM artifacts
- Try different breach/fill parameters
- Manual editing in QGIS may be needed

### Topology Errors
- Check that all reaches connect properly
- Use QGIS topology checker tool
- Verify outlet reach configuration

### Unrealistic Slopes
- Check DEM quality and artifacts
- Verify coordinate system and units
- Consider DEM resolution vs reach length

## Example Complete Workflow

Here's a complete example for a small catchment:

```bash
# 1. Prepare DEM (if needed)
# - Reproject to suitable coordinate system
# - Clip to study area

# 2. Run extraction in QGIS GUI
# Input DEM: my_catchment_dem.tif
# Min Area: 500000 m² (0.5 km²)
# Output: river_network_raw.shp

# 3. Post-process attributes in QGIS Field Calculator
# Wac = 5.0 * power("Ad" / 1000000, 0.5)  # Simple width estimation
# D16 = 0.016
# D50 = 0.050  
# D84 = 0.084
# deposit = 100000

# 4. Export final shapefile
# Save as: river_network_final.shp

# 5. Prepare Q file
# Create Q_timeseries.csv with daily discharge

# 6. Use in D-CASCADE
# Update paths in user script and run simulation
```

## Further Reading

- D-CASCADE documentation: See main README.md
- QGIS Processing documentation: https://docs.qgis.org/
- SAGA GIS hydrology tools: https://saga-gis.sourceforge.io/
- Hydraulic geometry relations: Leopold & Maddock (1953)

## Support

If you encounter issues:
1. Check the main README.md troubleshooting section
2. Verify SAGA GIS installation and configuration
3. Test with a small area first
4. Open an issue in the D-CASCADE repository with:
   - Description of the problem
   - DEM characteristics (resolution, extent, CRS)
   - Parameter values used
   - Error messages or unexpected results
