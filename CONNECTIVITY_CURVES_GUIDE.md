# Connectivity Curves - Quick Start Guide

## What Are Connectivity Curves?

Connectivity curves visualize sediment transport between river reaches in D-CASCADE simulations. They appear as animated, curved arrows on the map that show:
- **Where** sediment is moving (from which reach to which reach)
- **How much** sediment is moving (arrow color indicates volume)
- **When** sediment is moving (updates as you scrub through time)

## Visual Example

```
River Network View:

    [Reach 1] ═══╗
                  ║ Curved arc (sediment flow)
    [Reach 2]    ╚═══► [Reach 3]
      ║                    ║
      ║                    ║
      ╚════════════════════╝
           To Outlet →
```

## How to Use

### 1. Prerequisites
- D-CASCADE simulation results loaded (must include "Direct connectivity [m^3]" data)
- Network layer selected in Parameters dock
- Results loaded in Results Viewer dock

### 2. Enable Connectivity Curves

**Step-by-step:**
1. Open the **Results Viewer** dock (D-CASCADE menu → Show Results)
2. Click the **Animation** tab
3. Check the box: ☑ **"Show connectivity curves"**

**What happens:**
- Curved arrows appear on the map showing sediment transport
- Arrows are colored based on sediment volume (more sediment = different color)
- Arrow opacity is set to 78% so you can see the underlying network

### 3. View Animation

Use the time slider in the Animation tab to see how connectivity changes over time:
- Move slider → Curves update to show transport at that timestep
- Press **▶ Play** → Automatically animate through all timesteps
- Adjust **Frame Duration** → Control animation speed

### 4. Customize Appearance

**Color Ramp**: Select different color schemes
- Viridis (default) - perceptually uniform
- Spectral - rainbow-like
- Magma, Plasma, Inferno - heat-map styles

**Line Width**: Adjust thickness of curves (0.1 to 10.0)
- Thicker lines = easier to see
- Thinner lines = less visual clutter

**Note**: Color ramp and line width affect both the reach layer AND connectivity curves

## Understanding the Visualization

### Arrow Colors
Arrows are colored using a **logarithmic scale** because sediment volumes can vary by orders of magnitude:

```
Light color  → Lower volumes (e.g., 1-10 m³)
Medium color → Medium volumes (e.g., 10-100 m³)
Dark color   → Higher volumes (e.g., 100-1000 m³)
```

### Arrow Curvature
Two types of connections use different curvatures for clarity:

1. **Between reaches** (curved left): -0.6 curvature
   - Shows sediment moving from one reach to another
   
2. **To outlet** (curved right): +0.35 curvature
   - Shows sediment leaving the network at the outlet

This makes it easy to distinguish internal transport from export.

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Simulation Results                                           │
│ └─ "Direct connectivity [m³]"                               │
│    Shape: (timesteps, reaches, reaches+1)                   │
│    └─ [:, :, :-1] = sediment between reaches                │
│    └─ [:, :, -1]  = sediment to outlet                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Time Slider Changed                                          │
│ └─ User moves slider to timestep T                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Extract Connectivity Data                                    │
│ └─ transport_data = connectivity[T, :, :-1]                 │
│ └─ qout_data = connectivity[T, :, -1]                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Generate Arc Geometries                                      │
│ For each non-zero connection:                                │
│   1. Get reach centroids from network layer                  │
│   2. Create Bezier curve (20 points)                         │
│   3. Store as LineString feature                             │
│   4. Attach volume attribute                                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Apply Symbology                                              │
│ └─ Create 5 graduated classes (log scale)                   │
│ └─ Color from selected ramp                                 │
│ └─ Width from spinner                                       │
│ └─ Transparency: 78%                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Display on Map                                               │
│ └─ "D-CASCADE Connectivity" layer                           │
│ └─ Above animation layer                                    │
│ └─ Updates when time changes                                │
└─────────────────────────────────────────────────────────────┘
```

## Mathematical Details

### Bezier Curve Generation

Each curve is a quadratic Bezier curve defined by:
- **P₀**: Start point (source reach centroid)
- **P₁**: Control point (offset perpendicular to line)
- **P₂**: End point (destination reach centroid)

**Formula**: B(t) = (1-t)²P₀ + 2(1-t)t·P₁ + t²P₂, where t ∈ [0,1]

**Control point calculation**:
```python
midpoint = (start + end) / 2
perpendicular = rotate(end - start, 90°)
control = midpoint + perpendicular × curvature × distance × 0.3
```

The curve is sampled at 20 points for smooth rendering.

## Troubleshooting

### Curves Don't Appear
**Check:**
- ✓ Results are loaded (Results Viewer shows data)
- ✓ Network layer is selected (Parameters dock)
- ✓ Checkbox is checked (Animation tab)
- ✓ Results contain "Direct connectivity [m³]" field
- ✓ Current timestep has non-zero connectivity

**View QGIS Log:**
1. View → Panels → Log Messages
2. Select "D-CASCADE" tab
3. Look for error messages

### Performance Issues
If curves update slowly:
- Try with fewer reaches (< 50)
- Reduce frame duration for smoother animation
- Close other QGIS layers/panels

### Curves Look Wrong
- Check that network layer has correct topology (FromN, ToN)
- Verify reach centroids are reasonable
- Check for duplicate reach IDs

## Advanced Usage

### Filtering by Volume
To show only significant connections, modify the code:

```python
# In update_connectivity_curves(), add threshold
THRESHOLD = 10.0  # Only show if volume > 10 m³
if volume > THRESHOLD:
    # Create arc...
```

### Adjusting Curvature
To make curves more/less curved:

```python
# In update_connectivity_curves()
# For reach-to-reach connections (default: -0.6)
line_geom = self._create_arc_geometry(start_pos, dest_pos, -0.8)  # More curved

# For outlet connections (default: 0.35)
line_geom = self._create_arc_geometry(start_pos, dest_pos, 0.5)  # More curved
```

### Performance Optimization
For large networks (> 100 reaches):

1. **Spatial filtering**: Only show arcs in current viewport
2. **Volume filtering**: Skip small volumes
3. **Temporal filtering**: Show only current + adjacent timesteps
4. **LOD**: Reduce Bezier points from 20 to 10

## Technical Details

### Data Requirements
- **Network layer**: Must have FromN, ToN, and geometry
- **Results data**: Must include "Direct connectivity [m³]"
- **Data shape**: `(timesteps, reaches, reaches+1)`

### Layer Structure
- **Name**: "D-CASCADE Connectivity"
- **Type**: Memory layer (LineString)
- **CRS**: Inherited from network layer
- **Fields**:
  - `from_reach` (Int): Source reach ID
  - `to_reach` (Int): Destination reach ID (-1 for outlet)
  - `volume` (Double): Sediment volume [m³]
  - `to_outlet` (Int): 1 if outlet connection, 0 otherwise

### Renderer
- **Type**: QgsGraduatedSymbolRenderer
- **Field**: "volume"
- **Mode**: Custom (logarithmic classes)
- **Classes**: 5
- **Transparency**: 200/255 (78% opacity)

## FAQ

**Q: Why use logarithmic scale?**  
A: Sediment volumes can range from 0.1 to 10,000+ m³. Linear scale would make small flows invisible.

**Q: Why Bezier curves instead of straight lines?**  
A: Curves are visually clearer when multiple connections overlap or when reaches are close together.

**Q: Can I export connectivity maps?**  
A: Yes! Use QGIS tools: Project → Import/Export → Export Map to Image

**Q: Does this slow down QGIS?**  
A: For networks under 100 reaches, performance impact is minimal. The layer is efficiently regenerated each timestep.

**Q: Can I use this with other sediment transport data?**  
A: Currently, it only reads "Direct connectivity [m³]". To use other data, modify the `connectivity_key` variable in the code.

## References

- **Original post-processing script**: `qgis_plugin/post_process_examples/08-connectivity_maps.py`
- **Technical documentation**: `CONNECTIVITY_CURVES.md`
- **Implementation details**: `IMPLEMENTATION_SUMMARY.md`
- **Unit tests**: `qgis_plugin/unit_tests/test_connectivity_curves.py`

## Support

For issues or questions:
1. Check QGIS message log first
2. Review documentation files
3. Test with example data
4. Open GitHub issue with:
   - QGIS version
   - D-CASCADE version
   - Error messages
   - Steps to reproduce
