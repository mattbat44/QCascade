# -*- coding: utf-8 -*-
"""
Visualize sediment deposit layers (cores) at specific reaches

This script extracts and visualizes the sediment stratigraphy (like a sediment core)
at specific reaches from D-CASCADE extended output. The Qbi_dep matrix stores the 
deposit layers for each reach over time, with each layer representing a distinct 
depositional event.

Layer Structure:
- Top rows = most recently deposited (youngest)
- Bottom rows = oldest deposits
- Each layer contains: metadata (provenance) + sediment class volumes

@author: D-CASCADE Development Team
"""

# Libraries 
import os
import sys
import numpy as np 
from matplotlib import pyplot as plt 
import matplotlib.cm as cm 

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add source (src) folder in the python path
sys.path.append(os.path.abspath(os.path.join(SCRIPT_DIR, '../src')))
from json_serializer import load_from_json

#---------------------Path to the extended JSON output
path = os.path.join(SCRIPT_DIR, "..", "cascade_results", "") 
name_simu_ext = 'Vjosa_test_ext'

#---------------------Folder to store the plots
figure_folder = os.path.join(path, 'sediment_cores', '')
if not os.path.exists(figure_folder):       
    os.makedirs(figure_folder)

#---------------------Parameters for visualization
reach_id = 5              # Reach index to visualize (0-based)
timestep_index = 0        # Timestep index (depends on save_dep_layer setting)
                          # 0 = initial condition
                          # For save_dep_layer='yearly', index corresponds to year
                          # For save_dep_layer='always', index corresponds to timestep


##############################################################################

def extract_sediment_core(Qbi_dep, reach_id, timestep_index):
    """
    Extract the sediment deposit layers (like a core) for a specific reach at a specific time.
    
    Parameters:
    -----------
    Qbi_dep : list
        The deposit layer matrix from extended output
        Structure: [timestep][reach_id] -> numpy array with layers as rows
    reach_id : int
        The reach index (0-based)
    timestep_index : int
        The saved timestep index (depends on save_dep_layer setting)
        
    Returns:
    --------
    core : numpy.ndarray
        2D array where each row is a layer (top = youngest, bottom = oldest)
        Columns: [provenance, sediment_class_1, sediment_class_2, ...]
    """
    # Extract the deposit matrix for the specific reach at the specific time
    core = Qbi_dep[timestep_index][reach_id]
    
    return core


def visualize_sediment_core(core, psi, reach_id, timestep, output_path=None):
    """
    Visualize the sediment core as a stratigraphic column.
    
    Parameters:
    -----------
    core : numpy.ndarray
        The deposit layer matrix from extract_sediment_core()
        Each row is a layer, columns are [provenance, sediment_classes...]
    psi : array
        Sediment size class array (Krumbein phi scale)
    reach_id : int
        The reach identifier (0-based)
    timestep : int
        The timestep identifier
    output_path : str, optional
        Path to save the figure. If None, displays interactively.
    """
    n_layers = core.shape[0]
    n_classes = len(psi)
    
    # Extract sediment volumes (skip metadata column - provenance is first column)
    sediment_volumes = core[:, 1:]  # Assumes 1 metadata column
    
    # Calculate layer thicknesses (sum of all sediment classes)
    # Suppress only division warnings that may occur with empty layers
    with np.errstate(divide='ignore', invalid='ignore'):
        layer_thicknesses = np.sum(sediment_volumes, axis=1)
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 10))
    
    # Convert psi to grain size in mm
    grain_sizes_mm = 2**(-psi)
    
    # Color map for grain size classes
    cmap = cm.viridis
    colors = [cmap(i / n_classes) for i in range(n_classes)]
    
    # Plot 1: Stratigraphic column (grain size distribution by layer)
    bottom = 0
    legend_added = False
    for i in range(n_layers-1, -1, -1):  # Start from bottom (oldest)
        height = layer_thicknesses[i]
        if height > 0:  # Only plot non-empty layers
            # Calculate grain size distribution for this layer
            with np.errstate(divide='ignore', invalid='ignore'):
                total_volume = np.sum(sediment_volumes[i, :])
                if total_volume > 0:
                    gsd = sediment_volumes[i, :] / total_volume
                else:
                    gsd = np.zeros(n_classes)
            
            # Create stacked bar for grain size classes
            left = 0
            for j in range(n_classes):
                if gsd[j] > 0:
                    label = f'{grain_sizes_mm[j]:.2f} mm' if not legend_added and i == n_layers-1 else ''
                    ax1.barh(bottom + height/2, gsd[j], height=height, 
                           left=left, color=colors[j], edgecolor='black', linewidth=0.5,
                           label=label)
                    left += gsd[j]
            
            if i == n_layers-1:
                legend_added = True
            
            bottom += height
    
    ax1.set_xlabel('Grain Size Fraction', fontsize=13)
    ax1.set_ylabel('Depth (m³ equivalent)', fontsize=13)
    ax1.set_title(f'Sediment Core - Grain Size Distribution\nReach {reach_id}, Timestep {timestep}', fontsize=14)
    ax1.legend(title='Grain Sizes', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax1.set_xlim([0, 1])
    ax1.grid(axis='y', alpha=0.3)
    
    # Plot 2: Provenance tracking (which reach each layer came from)
    bottom = 0
    provenance_values = core[:, 0]  # First column is provenance
    unique_provenances = np.unique(provenance_values[provenance_values >= 0])
    
    # Color map for provenance
    if len(unique_provenances) > 0:
        cmap_prov = cm.tab20
        prov_colors = {int(p): cmap_prov(i / max(len(unique_provenances), 1)) 
                      for i, p in enumerate(unique_provenances)}
    else:
        prov_colors = {}
    
    # Track which provenances have been labeled
    labeled_provenances = set()
    
    for i in range(n_layers-1, -1, -1):  # Start from bottom (oldest)
        height = layer_thicknesses[i]
        if height > 0:
            prov = provenance_values[i]
            color = prov_colors.get(int(prov), 'gray') if prov >= 0 else 'gray'
            
            # Only add label if this provenance hasn't been labeled yet
            if prov not in labeled_provenances and prov >= 0:
                label = f'Reach {int(prov)}'
                labeled_provenances.add(prov)
            else:
                label = ''
            
            ax2.barh(bottom + height/2, 1, height=height, 
                    color=color, edgecolor='black', linewidth=0.5,
                    label=label)
            
            bottom += height
    
    ax2.set_xlabel('', fontsize=13)
    ax2.set_ylabel('Depth (m³ equivalent)', fontsize=13)
    ax2.set_title(f'Sediment Core - Provenance\nReach {reach_id}, Timestep {timestep}', fontsize=14)
    ax2.set_xlim([0, 1])
    ax2.set_xticks([])
    ax2.grid(axis='y', alpha=0.3)
    
    # Create legend with unique provenances only
    handles, labels = ax2.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax2.legend(by_label.values(), by_label.keys(), 
              title='Provenance', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Figure saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()


def visualize_core_summary(Qbi_dep, psi, reach_id, output_path=None):
    """
    Create a summary visualization showing the evolution of the sediment core over time.
    
    Parameters:
    -----------
    Qbi_dep : list
        The deposit layer matrix from extended output
    psi : array
        Sediment size class array (Krumbein phi scale)
    reach_id : int
        The reach identifier (0-based)
    output_path : str, optional
        Path to save the figure
    """
    n_timesteps = len(Qbi_dep)
    
    fig, axes = plt.subplots(1, min(n_timesteps, 4), figsize=(15, 8), sharey=True)
    if n_timesteps == 1:
        axes = [axes]
    
    timesteps_to_plot = np.linspace(0, n_timesteps-1, min(n_timesteps, 4), dtype=int)
    
    grain_sizes_mm = 2**(-psi)
    n_classes = len(psi)
    cmap = cm.viridis
    colors = [cmap(i / n_classes) for i in range(n_classes)]
    
    for idx, t in enumerate(timesteps_to_plot):
        if idx >= len(axes):
            break
            
        ax = axes[idx]
        core = Qbi_dep[t][reach_id]
        n_layers = core.shape[0]
        sediment_volumes = core[:, 1:]
        layer_thicknesses = np.sum(sediment_volumes, axis=1)
        
        bottom = 0
        for i in range(n_layers-1, -1, -1):
            height = layer_thicknesses[i]
            if height > 0:
                total_volume = np.sum(sediment_volumes[i, :])
                if total_volume > 0:
                    gsd = sediment_volumes[i, :] / total_volume
                else:
                    gsd = np.zeros(n_classes)
                
                left = 0
                for j in range(n_classes):
                    if gsd[j] > 0:
                        ax.barh(bottom + height/2, gsd[j], height=height, 
                               left=left, color=colors[j], edgecolor='black', linewidth=0.3)
                        left += gsd[j]
                
                bottom += height
        
        ax.set_xlabel('Grain Size Fraction', fontsize=10)
        ax.set_title(f'Timestep {t}', fontsize=11)
        ax.set_xlim([0, 1])
        ax.grid(axis='y', alpha=0.3)
    
    axes[0].set_ylabel('Depth (m³ equivalent)', fontsize=12)
    
    # Add legend
    legend_elements = [plt.Rectangle((0,0),1,1, fc=colors[i], edgecolor='black', 
                                    label=f'{grain_sizes_mm[i]:.2f} mm') 
                      for i in range(n_classes)]
    fig.legend(handles=legend_elements, title='Grain Sizes', 
              bbox_to_anchor=(1.02, 0.5), loc='center left', fontsize=9)
    
    fig.suptitle(f'Sediment Core Evolution - Reach {reach_id}', fontsize=14, y=0.98)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Summary figure saved to: {output_path}")
    else:
        plt.show()
    
    plt.close()


##############################################################################
# Main execution
##############################################################################

if __name__ == "__main__":
    # Load the extended output
    print(f"Loading extended output from: {path + name_simu_ext}.json")
    data_output_ext = load_from_json(path + name_simu_ext + '.json')
    
    # Extract Qbi_dep and parameters
    Qbi_dep = data_output_ext['Qbi_dep [m^3]']
    psi = data_output_ext['Simulation parameters']['psi']
    n_reaches = data_output_ext['Simulation parameters']['n_reaches']
    
    print(f"\nSimulation info:")
    print(f"  Number of reaches: {n_reaches}")
    print(f"  Number of saved timesteps: {len(Qbi_dep)}")
    print(f"  Number of sediment classes: {len(psi)}")
    print(f"  Grain sizes (mm): {[f'{2**(-p):.2f}' for p in psi]}")
    
    # Extract and analyze the core for the specified reach
    core = extract_sediment_core(Qbi_dep, reach_id, timestep_index)
    
    print(f"\nReach {reach_id} at timestep {timestep_index}:")
    print(f"  Number of sediment layers: {core.shape[0]}")
    print(f"  Columns per layer: {core.shape[1]} (1 metadata + {core.shape[1]-1} sediment classes)")
    
    # Calculate total volume
    total_volume = np.sum(core[:, 1:])
    print(f"  Total sediment volume: {total_volume:.2f} m³")
    
    # Visualize the sediment core
    output_file = os.path.join(figure_folder, f'sediment_core_reach_{reach_id}_t_{timestep_index}.png')
    visualize_sediment_core(core, psi, reach_id, timestep_index, output_path=output_file)
    
    # Create summary visualization over time
    if len(Qbi_dep) > 1:
        summary_file = os.path.join(figure_folder, f'sediment_core_summary_reach_{reach_id}.png')
        visualize_core_summary(Qbi_dep, psi, reach_id, output_path=summary_file)
    
    print(f"\nVisualization complete! Figures saved to: {figure_folder}")
