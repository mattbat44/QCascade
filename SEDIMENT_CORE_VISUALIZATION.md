# Sediment Core Visualization in D-CASCADE

## Overview

D-CASCADE tracks the complete stratigraphy (sediment layers) of deposits in each reach through the `Qbi_dep` matrix. This allows visualization of sediment cores showing how deposits accumulate and erode over time.

## Key Features

- **Full stratigraphy tracking**: Every deposit layer is stored with its grain size distribution and provenance
- **Temporal resolution**: Controlled by the `save_dep_layer` parameter
- **Provenance tracking**: Each layer records which reach it originated from
- **Erosion handling**: Layers are removed from the top when erosion occurs

## Data Structure

### Qbi_dep Matrix

The `Qbi_dep` matrix is a 3D list structure:

```
Qbi_dep[timestep][reach_id] → numpy array (n_layers × n_columns)
```

**Dimensions:**
- **Dimension 1**: Time steps (number depends on `save_dep_layer` setting)
- **Dimension 2**: Reaches (n_reaches)
- **Dimension 3**: Layers (each row is a distinct depositional layer)

**Layer Structure:**
Each layer (row) contains:
- **Column 0**: Provenance (reach ID where sediment originated)
- **Columns 1 to n_classes**: Volume of each grain size class (m³)

**Stratigraphy Order:**
- **Top rows** = Most recently deposited (youngest)
- **Bottom rows** = Oldest deposits

### Storage Options (`save_dep_layer` parameter)

- `'never'`: Only stores initial and final states (minimal memory)
- `'yearly'`: Stores deposit layers every 365 time steps
- `'always'`: Stores deposit layers at every time step (memory intensive, full temporal resolution)

## Usage

### Post-Processing Script

The script `post_process_examples/09-sediment_core_visualization.py` provides complete functionality for extracting and visualizing sediment cores.

### Basic Usage

1. **Set parameters** in the script:
   ```python
   reach_id = 5              # Reach to visualize (0-based index)
   timestep_index = 0        # Timestep to visualize
   name_simu_ext = 'Vjosa_test_ext'  # Extended output filename
   ```

2. **Run the script**:
   ```bash
   python 09-sediment_core_visualization.py
   ```

3. **Output**: Creates two types of visualizations in `cascade_results/sediment_cores/`:
   - Single timestep core with grain size distribution and provenance
   - Summary showing core evolution over time

### Functions

#### `extract_sediment_core(Qbi_dep, reach_id, timestep_index)`

Extracts the sediment deposit layers for a specific reach at a specific time.

**Parameters:**
- `Qbi_dep`: The deposit layer matrix from extended output
- `reach_id`: Reach index (0-based)
- `timestep_index`: Saved timestep index (depends on `save_dep_layer` setting)

**Returns:**
- 2D numpy array where each row is a layer (top = youngest, bottom = oldest)
- Columns: [provenance, sediment_class_1, sediment_class_2, ...]

**Example:**
```python
core = extract_sediment_core(Qbi_dep, reach_id=5, timestep_index=0)
print(f"Reach has {core.shape[0]} sediment layers")
print(f"Total volume: {np.sum(core[:, 1:]):.2f} m³")
```

#### `visualize_sediment_core(core, psi, reach_id, timestep, output_path=None)`

Creates a two-panel visualization of the sediment core:
- **Left panel**: Grain size distribution by layer (stratigraphic column)
- **Right panel**: Provenance tracking showing sediment origin

**Parameters:**
- `core`: Deposit layer matrix from `extract_sediment_core()`
- `psi`: Sediment size class array (Krumbein phi scale)
- `reach_id`: Reach identifier
- `timestep`: Timestep identifier
- `output_path`: Optional path to save figure (displays interactively if None)

**Example:**
```python
visualize_sediment_core(
    core, 
    psi, 
    reach_id=5, 
    timestep=0, 
    output_path='sediment_core_reach5.png'
)
```

#### `visualize_core_summary(Qbi_dep, psi, reach_id, output_path=None)`

Creates a summary visualization showing the evolution of the sediment core over multiple timesteps.

**Parameters:**
- `Qbi_dep`: Full deposit layer matrix
- `psi`: Sediment size class array (Krumbein phi scale)
- `reach_id`: Reach identifier
- `output_path`: Optional path to save figure

**Example:**
```python
visualize_core_summary(Qbi_dep, psi, reach_id=5, output_path='core_summary.png')
```

## Interpretation

### Reading the Visualization

**Grain Size Distribution Panel:**
- Vertical axis: Depth (in m³ equivalent volume)
- Horizontal axis: Grain size fraction (0 to 1)
- Colors: Different grain size classes
- Each horizontal bar: One depositional layer
- Width of each color: Proportion of that grain size in the layer

**Provenance Panel:**
- Vertical axis: Depth (in m³ equivalent volume)
- Colors: Different source reaches
- Shows sediment connectivity: which reaches contributed to deposits

### Example Interpretations

**Uniform layers**: Consistent grain size → steady sediment supply and transport conditions

**Fining upward sequence**: Coarse at bottom, fine at top → decreasing transport energy over time

**Multiple provenances**: Different colored bands → sediment from various upstream sources

**Thin recent layers**: Small top layers → recent deposition phase or erosion

## Memory Considerations

The `Qbi_dep` matrix can be large depending on:
- Number of reaches
- Number of timesteps
- `save_dep_layer` setting

**Recommendations:**
- Use `'never'` for large simulations (thousands of reaches/timesteps)
- Use `'yearly'` for moderate temporal resolution with manageable memory
- Use `'always'` only for detailed analysis of small networks or short simulations

**Typical sizes:**
- 100 reaches × 1000 timesteps × 10 layers × 6 classes ≈ 50 MB
- 1000 reaches × 10000 timesteps × 10 layers × 6 classes ≈ 5 GB (with `'always'`)

## Integration with Existing Post-Processing

The sediment core visualization complements other post-processing scripts:

- **01-03**: Time series of sediment transport → Use with core viewer to understand layer formation
- **04-06**: Spatial patterns along network → Identify key reaches for core visualization
- **08**: Connectivity analysis → Understand provenance patterns in cores

## Technical Details

### Data Access Pattern

```python
# Load extended output
data_output_ext = load_from_json('cascade_results/simulation_ext.json')
Qbi_dep = data_output_ext['Qbi_dep [m^3]']

# Access specific reach at specific time
core = Qbi_dep[timestep_index][reach_id]

# Extract components
provenance = core[:, 0]           # First column
sediment_volumes = core[:, 1:]    # Remaining columns
```

### Layer Thickness Calculation

Layer thickness is proportional to total sediment volume:
```python
layer_thickness = np.sum(sediment_volumes, axis=1)
```

This represents volumetric depth. For actual physical depth, divide by reach width and account for porosity:
```python
physical_depth = layer_thickness / (reach_width * reach_length * (1 - porosity))
```

## Troubleshooting

**Issue**: Empty or missing layers
- **Cause**: Reach had no deposits at that timestep
- **Solution**: Check earlier/later timesteps or different reaches

**Issue**: All layers from same provenance
- **Cause**: Reach is at tributary junction or network head
- **Solution**: Expected behavior; upstream reaches will show more diversity

**Issue**: Memory error loading Qbi_dep
- **Cause**: Too many timesteps saved with `'always'` setting
- **Solution**: Use `'yearly'` or `'never'`, or analyze fewer timesteps

**Issue**: Visualization shows warnings about empty legend
- **Cause**: Layers have zero volume
- **Solution**: Normal for reaches with little deposition; warnings can be ignored

## References

- Tangi et al. (2022): Original CASCADE framework
- Doolaeghe et al. (in prep): D-CASCADE v2.0.0
- Schmitt et al. (2016): CASCADE model description

## See Also

- User script example: `user_scripts/00-DCASCADE_user_script_example_Vjosa.py`
- Other post-processing examples: `post_process_examples/01-08-*.py`
- Test examples: `unit_tests/test_sediment_core_visualization.py`
