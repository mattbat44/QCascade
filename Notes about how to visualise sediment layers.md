To answer your question about viewing sediment layers (like a sediment core) at a particular reach, I need to examine how D-CASCADE stores sediment deposition data and how it's structured in the output files. Based on my analysis of the D-CASCADE codebase, I can explain how to visualize sediment layers (like a sediment core) at a particular reach:

## Current Capability:  `Qbi_dep` Deposit Layer Matrix

The model **already tracks sediment layers** through the **`Qbi_dep`** matrix in `SedimentarySystem`. This matrix stores the deposit layers (stratigraphy) for each reach over time.

### How It Works: 

1. **Storage Structure**: `Qbi_dep` is a 3D list structure: 
   - **Dimension 1**: Time steps (controlled by `save_dep_layer` parameter)
   - **Dimension 2**: Reaches (n_reaches)
   - **Dimension 3**: Layers with metadata + sediment classes (each layer is a row)

2. **Layer Storage Options** (`save_dep_layer` parameter):
   - `'never'`: Only stores initial and final states
   - `'yearly'`: Stores deposit layers every 365 time steps
   - `'always'`: Stores deposit layers at every time step (memory intensive)

3. **Layer Structure**:  Each layer contains:
   - **Metadata column(s)**: Original provenance (which reach it came from)
   - **Sediment class columns**: Volume of each grain size class

4. **Stratigraphy**:  Layers are stacked vertically in a numpy array, with: 
   - **Top rows** = most recently deposited (youngest)
   - **Bottom rows** = oldest deposits

### Method to Extract a "Sediment Core": 

```python
def extract_sediment_core(sedimentary_system, reach_id, timestep_index):
    """
    Extract the sediment deposit layers (like a core) for a specific reach at a specific time. 
    
    Parameters:
    -----------
    sedimentary_system : SedimentarySystem
        The sedimentary system object after simulation
    reach_id : int
        The reach index (0-based)
    timestep_index : int
        The saved timestep index (depends on save_dep_layer setting)
        
    Returns: 
    --------
    core :  numpy.ndarray
        2D array where each row is a layer (top = youngest, bottom = oldest)
        Columns: [provenance, sediment_class_1, sediment_class_2, ...]
    """
    # Extract the deposit matrix for the specific reach at the specific time
    core = sedimentary_system. Qbi_dep[timestep_index][reach_id]
    
    return core

def visualize_sediment_core(core, psi, reach_id, timestep):
    """
    Visualize the sediment core as a stratigraphic column.
    
    Parameters:
    -----------
    core : numpy.ndarray
        The deposit layer matrix from extract_sediment_core()
    psi : array
        Sediment size class array (Krumbein phi scale)
    reach_id : int
        The reach identifier
    timestep : int
        The timestep identifier
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    n_layers = core.shape[0]
    n_classes = len(psi)
    
    # Extract sediment volumes (skip metadata column)
    sediment_volumes = core[:, 1:]  # Assumes 1 metadata column
    
    # Calculate layer thicknesses (assuming constant porosity and width)
    layer_thicknesses = np.sum(sediment_volumes, axis=1)
    cumulative_thickness = np.cumsum(layer_thicknesses[: :-1])[::-1]  # Bottom to top
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot each layer from bottom to top
    bottom = 0
    for i in range(n_layers-1, -1, -1):  # Start from bottom (oldest)
        height = layer_thicknesses[i]
        if height > 0:  # Only plot non-empty layers
            # Calculate grain size distribution for this layer
            gsd = sediment_volumes[i, : ] / np.sum(sediment_volumes[i, :])
            
            # Create stacked bar for grain size classes
            left = 0
            for j in range(n_classes):
                if gsd[j] > 0:
                    ax.barh(bottom + height/2, gsd[j], height=height, 
                           left=left, label=f'{2**(-psi[j]):.2f} mm' if i == n_layers-1 else '')
                    left += gsd[j]
            
            bottom += height
    
    ax.set_xlabel('Grain Size Fraction')
    ax.set_ylabel('Depth (m³ equivalent)')
    ax.set_title(f'Sediment Core at Reach {reach_id}, Timestep {timestep}')
    ax.legend(title='Grain Sizes', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()
```

### Example Usage in a Post-Processing Script:

```python name=post_process_examples/XX-sediment_core_visualization.py
# -*- coding: utf-8 -*-
"""
Visualize sediment deposit layers (cores) at specific reaches
"""

import sys
import os
sys.path. append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import pickle
import numpy as np
import matplotlib.pyplot as plt

# Load the extended output
path = "../cascade_results/"
name_simu_ext = "Vjosa_test_ext"

extended_output = pickle.load(open(path + name_simu_ext + '.p', "rb"))

# Extract Qbi_dep and parameters
Qbi_dep = extended_output['Qbi_dep']
psi = extended_output['psi']
n_reaches = extended_output['n_reaches']

# Choose reach and timestep to visualize
reach_id = 5  # Example reach
timestep_index = 0  # Depends on save_dep_layer setting

# Extract the core
core = Qbi_dep[timestep_index][reach_id]

print(f"Reach {reach_id} has {core.shape[0]} sediment layers")
print(f"Each layer contains {core.shape[1]} columns (metadata + {core.shape[1]-1} sediment classes)")

# Visualize (use function from above)
visualize_sediment_core(core, psi, reach_id, timestep_index)
```

### Key Points:

- ✅ **Already implemented**: The model tracks full stratigraphy in `Qbi_dep`
- ✅ **Includes provenance**:  Metadata shows where each layer originated
- ✅ **Handles erosion**: Erosion removes layers from the top
- ⚠️ **Memory consideration**: Set `save_dep_layer='always'` for full temporal resolution (but uses more memory)
- ⚠️ **No built-in visualizer**: You need to write custom post-processing (like the example above)

The deposit layer structure effectively represents a "sediment core" with each row being a distinct depositional layer that can be eroded from the top if transport capacity exceeds supply. 
