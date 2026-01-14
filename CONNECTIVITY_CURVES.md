# Connectivity Curves Implementation

## Overview

This implementation adds animated connectivity curves to the D-CASCADE QGIS plugin's main map viewer. The curves visualize sediment transport connections between reaches using the same logic as the `08-connectivity_maps.py` post-processing script.

## Features

### Core Functionality
- **Animated Arc Display**: Shows curved arrows between reaches representing sediment transport
- **Time-Step Synchronization**: Updates automatically when the animation time slider changes
- **Direct Connectivity Data**: Uses the "Direct connectivity [m^3]" field from simulation results
- **Width-Based Scale**: Line width represents sediment volume using logarithmic width classes
- **Consistent Width Classes**: Width classes calculated globally from all timesteps for animation consistency
- **Outlet Connections**: Handles sediment flowing to the outlet with different arc curvature

### Implementation Details

#### 1. Layer Management (`dcascade_plugin.py`)

**New Attributes:**
- `self.connectivity_layer`: QgsVectorLayer for storing connectivity arc geometries
- `self.connectivity_enabled`: Boolean flag to toggle visibility

**Key Methods:**

##### `update_connectivity_curves(time_step)`
Main method that updates the connectivity layer for a given time step:
1. Extracts "Direct connectivity [m^3]" data from results
2. Creates curved line geometries between reach centroids
3. Applies graduated width symbology based on sediment volume
4. Uses logarithmic width classes calculated globally across all timesteps for consistency
5. Uses a single consistent color for all arcs

**Data Structure:**
- `transport_data`: Shape (num_reaches, num_reaches) - sediment between reaches
- `qout_data`: Shape (num_reaches,) - sediment to outlet
- Creates arc features with attributes: `from_reach`, `to_reach`, `volume`, `to_outlet`

##### `_create_arc_geometry(start_pos, end_pos, curvature)`
Creates smooth curved arcs using quadratic Bezier curves:
- **Input**: Start/end coordinates, curvature factor
- **Output**: QgsGeometry with curved LineString
- **Algorithm**: 
  1. Calculate perpendicular offset from line midpoint
  2. Generate control point for Bezier curve
  3. Sample 20 points along quadratic Bezier curve
  4. Return as LineString geometry

**Bezier Formula:**
```
B(t) = (1-t)²P₀ + 2(1-t)t·P₁ + t²P₂
```
Where:
- P₀ = start point
- P₁ = control point (offset perpendicular to line)
- P₂ = end point
- t = parameter from 0 to 1

##### `_calculate_global_width_ranges()`
Calculates consistent width ranges from all timesteps:
1. Extracts all non-zero volumes from entire dataset
2. Computes logarithmic class boundaries (5 classes by default)
3. Assigns linearly increasing widths to each class (0.3mm to 3.0mm)
4. Returns list of (lower, upper, width) tuples
5. Called once when connectivity is enabled and cached for the animation

This ensures that width classes remain consistent throughout the animation,
making it easier to compare sediment transport between different timesteps.

##### `toggle_connectivity_curves(enabled)`
Enables or disables connectivity curve display:
- When enabled: Creates layer and populates with current time step data
- When disabled: Clears the layer but keeps it for performance

#### 2. UI Controls (`animation_tab.py`)

**New Widget:**
- `connectivity_check`: QCheckBox to toggle connectivity curves display
- Located in "Connectivity Curves" group box in Animation tab
- Connected to `on_connectivity_toggled` signal handler

#### 3. Integration

**Signal Flow:**
1. User toggles checkbox in Animation tab
2. `connectivity_check.stateChanged` signal emitted
3. `dcascade_plugin.on_connectivity_toggled()` called
4. `toggle_connectivity_curves()` updates layer visibility
5. If enabled, `update_connectivity_curves()` populates layer

**Time Step Updates:**
1. User moves time slider
2. `results_viewer_dock.time_step_changed` signal emitted
3. `dcascade_plugin.on_time_step_changed()` called
4. If connectivity enabled, `update_connectivity_curves()` called
5. Layer updated with new arc data for current time step

## Code Structure

### Modified Files

1. **`qgis_plugin/dcascade_plugin.py`**
   - Added `connectivity_layer` and `connectivity_enabled` attributes
   - Implemented `update_connectivity_curves()` method
   - Implemented `_create_arc_geometry()` method
   - Implemented `toggle_connectivity_curves()` method
   - Added `on_connectivity_toggled()` signal handler
   - Updated `on_time_step_changed()` to update curves

2. **`qgis_plugin/docks/results_viewer/animation_tab.py`**
   - Added `connectivity_check` checkbox
   - Added "Connectivity Curves" group box

3. **`qgis_plugin/docks/results_viewer_dock.py`**
   - Exposed `connectivity_check` widget for plugin access

### Data Requirements

The implementation requires the following data in simulation results:

- **"Direct connectivity [m^3]"**: 3D numpy array
  - Shape: `(timesteps, reaches, reaches+1)`
  - `[:, :, :-1]`: Sediment transport between reaches
  - `[:, :, -1]`: Sediment transport to outlet

- **Network layer attributes**:
  - `FromN`: Reach identifier
  - `ToN`: Downstream reach identifier
  - Geometry: LineString or MultiLineString with centroid

## Usage

### For Users

1. Load simulation results in the Results Viewer dock
2. Go to the Animation tab
3. Check "Show connectivity curves"
4. Use the time slider to see connectivity change over time
5. Width classes are automatically calculated from all timesteps for consistency
6. Thicker lines represent larger sediment volumes

### For Developers

#### Adding New Features

To extend the connectivity visualization:

1. **Modify Arc Appearance**: Edit `update_connectivity_curves()` renderer setup
2. **Change Curvature**: Adjust curvature parameters in arc creation calls
3. **Add Filtering**: Add logic to filter which connections are shown
4. **Performance**: Implement spatial indexing for large networks

#### Key Design Decisions

1. **Width-Based Visualization**: Line width represents volume instead of color for clearer comparison
2. **Consistent Width Classes**: Classes calculated globally from all timesteps for animation consistency
3. **Logarithmic Scale**: Used because sediment volumes span several orders of magnitude
4. **Single Color Scheme**: Uses consistent blue color to avoid color-based confusion
5. **Bezier Curves**: Provide smooth, visually appealing arcs
6. **Memory Layer**: Recreated each timestep for simplicity and correctness
7. **Graduated Renderer**: Provides clear visual differentiation of volumes

## Performance Considerations

- Layer is cleared and repopulated each time step (not incremental updates)
- For networks with N reaches, max connections = N²
- Bezier curves use 20 points per arc
- Performance tested on networks up to ~100 reaches

## Testing

### Manual Testing Checklist

- [ ] Connectivity curves appear when checkbox is enabled
- [ ] Curves disappear when checkbox is disabled
- [ ] Curves update when time slider moves
- [ ] Width classes remain consistent throughout animation
- [ ] Thicker lines represent larger volumes
- [ ] All curves use consistent blue color
- [ ] Arcs point from upstream to downstream
- [ ] Outlet connections use different curvature
- [ ] Layer appears above animation layer in layer tree
- [ ] No errors in QGIS message log

### Unit Tests

See `qgis_plugin/unit_tests/test_connectivity_curves.py` for logic validation tests:
- Bezier curve generation
- Direct connectivity data extraction
- Logarithmic width scale binning
- Global width range calculation

## References

- **Original Implementation**: `qgis_plugin/post_process_examples/08-connectivity_maps.py`
- **Matplotlib FancyArrowPatch**: Inspiration for arc styling
- **QGIS API**: QgsVectorLayer, QgsGraduatedSymbolRenderer
- **Bezier Curves**: https://en.wikipedia.org/wiki/B%C3%A9zier_curve

## Future Enhancements

Potential improvements:
1. **Arc Filtering**: Show only significant connections (volume threshold)
2. **Animation Trails**: Show previous timesteps as fading arcs
3. **Interactive Selection**: Click arc to see details
4. **Performance Optimization**: Spatial indexing, viewport culling
5. **3D Visualization**: Extend to 3D view if QGIS supports it
6. **Export**: Save connectivity maps as images or videos
