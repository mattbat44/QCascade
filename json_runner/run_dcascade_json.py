import sys
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add src to path
current_dir = Path(__file__).parent
src_path = current_dir.parent / 'src'
sys.path.append(str(src_path))

from main import DCASCADE_main
from reach_data import ReachData
from preprocessing import read_network, extract_Q, check_sediment_sizes, graph_preprocessing
from GSD_curvefit import GSDcurvefit
from validate_config import validate_config

def run_simulation(config_path):
    config_path = Path(config_path).resolve()
    with open(config_path, 'r') as f:
        config = json.load(f)

    if not validate_config(config):
        print("Validation failed. Aborting.")
        sys.exit(1)

    # Resolve paths relative to config file
    base_dir = config_path.parent
    
    paths = config['paths']
    river_network_path = (base_dir / paths['river_network_shp']).resolve()
    discharge_path = (base_dir / paths['discharge_csv']).resolve()
    output_name = paths['output_name']

    # Load parameters
    sed = config['sediment']
    time = config['time']
    phys = config['physics']
    opts = config['options']

    # --- Preprocessing ---

    print("Loading river network...")
    reach_data_df = read_network(river_network_path)
    reach_data = ReachData(reach_data_df)

    # Define the initial deposit layer per each reach in [m3/m]
    # Note: In the example script, it overwrites reach_data.deposit with the single value from config
    reach_data.deposit = np.repeat(sed['deposit_layer_thickness'], reach_data.n_reaches)

    print("Loading discharge data...")
    # extract_Q returns a DataFrame or similar, need to check implementation or usage
    # In example: Q = extract_Q(filename_q)
    Q = extract_Q(discharge_path)

    # Sort reach_data according to the from_n, and organise the Q file accordingly
    print("Sorting reach data and discharge...")
    sorted_indices = reach_data.sort_values_by(reach_data.from_n)
    
    # Q is likely a DataFrame or numpy array. Example uses Q.iloc, so it's a DataFrame initially?
    # But then Q_new is np.zeros(Q.shape).
    # Let's assume Q is a DataFrame or has .iloc.
    # If extract_Q returns a numpy array, .iloc won't work.
    # Let's check extract_Q in preprocessing.py if possible, but assuming example usage is correct.
    # Wait, if Q is numpy array, Q[:, idx] works. If DataFrame, Q.iloc[:, idx].
    # I'll assume it behaves like in the example.
    
    if isinstance(Q, pd.DataFrame):
        Q_values = Q.values
    else:
        Q_values = Q

    Q_new = np.zeros(Q_values.shape)
    for i, idx in enumerate(sorted_indices):
        # In example: Q_new[:,i] = Q.iloc[:,idx]
        # If Q is DataFrame:
        if isinstance(Q, pd.DataFrame):
             Q_new[:,i] = Q.iloc[:,idx]
        else:
             Q_new[:,i] = Q[:,idx]
    Q = Q_new

    print("Preprocessing graph...")
    network = graph_preprocessing(reach_data)

    # Sediment classes defined in Krumbein phi (φ) scale
    psi = np.linspace(sed['range'][0], sed['range'][1], num=sed['n_classes'], endpoint=True).astype(float)

    # Sediment classes in mm
    dmi = 2**(-psi).reshape(-1,1)
    
    print("Checking sediment sizes...")
    check_sediment_sizes(reach_data, dmi)

    # Define input sediment load in the deposit layer
    deposit = reach_data.deposit * reach_data.length

    # Define initial sediment fractions per class in each reaches, using a Rosin distribution
    print("Calculating initial grain size distribution...")
    Fi_r, _, _ = GSDcurvefit(reach_data.D16, reach_data.D50, reach_data.D84, psi)

    # Initialise deposit layer
    Qbi_dep_in = np.zeros((reach_data.n_reaches, 1, sed['n_classes']))
    for n in range(reach_data.n_reaches):
        Qbi_dep_in[n] = deposit[n] * Fi_r[n,:]

    print("Starting simulation...")
    data_output, extended_output = DCASCADE_main(
        reach_data=reach_data,
        network=network,
        Q=Q,
        psi=psi,
        timescale=time['timescale'],
        ts_length=time['ts_length'],
        al_depth=sed['active_layer_depth'],
        indx_tr_cap=phys['transport_capacity_formula'],
        indx_tr_partition=phys['transport_partitioning'],
        Qbi_dep_in=Qbi_dep_in,
        save_dep_layer=opts.get('save_deposit_layer', 'never'),
        eros_max=phys.get('erosion_max'),
        al_depth_method=sed.get('active_layer_method', 1),
        vel_height=phys.get('velocity_height', '2D90'),
        indx_flo_depth=phys.get('flow_depth_formula', 1),
        indx_velocity=phys.get('velocity_formula', 2),
        indx_vel_partition=phys.get('velocity_partitioning', 1),
        indx_slope_red=phys.get('slope_reduction', 1),
        indx_width_calc=phys.get('width_calculation', 1),
        update_slope=phys.get('update_slope', False),
        roundpar=opts.get('round_parameter', 0),
        external_inputs=None, 
        force_pass_external_inputs=opts.get('force_pass_external_inputs', False)
    )
    print("Simulation completed.")
    
    return data_output, extended_output

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_dcascade_json.py <config.json>")
        sys.exit(1)
    
    run_simulation(sys.argv[1])
