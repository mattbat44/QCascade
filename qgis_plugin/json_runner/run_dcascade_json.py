import sys
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add src to path first so bundled modules resolve correctly
current_dir = Path(__file__).parent
src_path = current_dir.parent / 'src'
sys.path.insert(0, str(src_path))

from dcascade_main import DCASCADE_main
from reach_data import ReachData
from preprocessing import read_network, extract_Q, check_sediment_sizes, graph_preprocessing
from GSD_curvefit import GSDcurvefit
from validate_config import validate_config
from json_serializer import save_to_json
from external_inputs_builder import (
    build_external_inputs_from_csv,
    build_external_inputs_from_dir,
    build_external_inputs_from_csv_for_reach,
)

def run_simulation(config_path):
    config_path = Path(config_path).resolve()
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Validation temporarily disabled (pending schema fixes)
    # if not validate_config(config):
    #     print("Validation failed. Aborting.")
    #     sys.exit(1)

    # Resolve paths relative to config file
    base_dir = config_path.parent
    
    paths = config['paths']
    river_network_path = (base_dir / paths['river_network_shp']).resolve()
    discharge_path = (base_dir / paths['discharge_csv']).resolve()
    overbank_q_path = None
    if isinstance(paths, dict):
        overbank_q_path = paths.get('overbank_q_csv')
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
              Q_new[:, i] = Q.iloc[:, idx]
        else:
              Q_new[:, i] = Q[:, idx]
    Q = Q_new

    # Optional overbank discharge thresholds/widths (one row per reach: reach_id,Q_limit,W_overbank)
    overbank_Q = None
    overbank_width = None
    if overbank_q_path:
        overbank_q_path = (base_dir / overbank_q_path).resolve()
        df_overbank = pd.read_csv(overbank_q_path)
        cols_lower = {c.lower(): c for c in df_overbank.columns}
        if "reach_id" not in cols_lower or "q_limit" not in cols_lower:
            raise ValueError("Overbank Q CSV must have columns reach_id and Q_limit (W_overbank optional).")
        reach_col = cols_lower["reach_id"]
        q_col = cols_lower["q_limit"]
        w_col = cols_lower.get("w_overbank")

        # Map reach_id -> values
        reach_to_q = {}
        reach_to_w = {}
        for _, row in df_overbank.iterrows():
            try:
                rid = int(row[reach_col])
            except Exception:
                continue
            reach_to_q[rid] = float(row[q_col])
            if w_col is not None and not pd.isna(row[w_col]):
                reach_to_w[rid] = float(row[w_col])

        overbank_Q_new = np.zeros((time['timescale'], reach_data.n_reaches))
        overbank_W_new = np.full((time['timescale'], reach_data.n_reaches), np.nan)
        for i, idx in enumerate(sorted_indices):
            rid = int(reach_data.from_n[idx])
            if rid not in reach_to_q:
                raise ValueError(f"Overbank Q CSV missing reach_id {rid}.")
            overbank_Q_new[:, i] = reach_to_q[rid]
            if rid in reach_to_w:
                overbank_W_new[:, i] = reach_to_w[rid]

        overbank_Q = overbank_Q_new
        if not np.all(np.isnan(overbank_W_new)):
            overbank_width = overbank_W_new

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

    # --- External inputs (optional) ---
    external_inputs_cfg = config.get('external_inputs')
    external_inputs_tensor = None
    if isinstance(external_inputs_cfg, dict):
        # Build a lightweight system stub for the builder
        class _SystemStub:
            def __init__(self, timescale, n_reaches, psi, ts_length):
                self.timescale = timescale
                self.n_reaches = n_reaches
                self.psi = psi
                self.n_classes = len(psi)
                self.ts_length = ts_length

        stub = _SystemStub(
            timescale=time['timescale'],
            n_reaches=reach_data.n_reaches,
            psi=psi,
            ts_length=time['ts_length'],
        )

        grain_unit = external_inputs_cfg.get('grain_unit', 'mm')
        default_sigma_g = external_inputs_cfg.get('default_sigma_g', 1.6)

        # Build from dir if provided
        if 'dir' in external_inputs_cfg and external_inputs_cfg['dir']:
            dir_path = (base_dir / external_inputs_cfg['dir']).resolve()
            external_inputs_tensor = build_external_inputs_from_dir(
                stub, dir_path, default_sigma_g=default_sigma_g, grain_unit=grain_unit
            )

        # Aggregate any listed CSV files
        csv_list = external_inputs_cfg.get('csv_files', [])
        if csv_list:
            # Initialize accumulator if not already built
            if external_inputs_tensor is None:
                external_inputs_tensor = np.zeros((stub.timescale, stub.n_reaches, stub.n_classes), dtype=float)
            for rel in csv_list:
                csv_path = (base_dir / rel).resolve()
                external_inputs_tensor += build_external_inputs_from_csv(
                    stub, csv_path, default_sigma_g=default_sigma_g, grain_unit=grain_unit
                )

        # Per-reach CSV mappings (list of {"reach_idx": int, "path": str})
        per_reach = external_inputs_cfg.get('per_reach_csvs', [])
        if per_reach:
            if external_inputs_tensor is None:
                external_inputs_tensor = np.zeros((stub.timescale, stub.n_reaches, stub.n_classes), dtype=float)
            for item in per_reach:
                try:
                    r_idx = int(item['reach_idx'])
                    pth = (base_dir / item['path']).resolve()
                except Exception:
                    continue
                external_inputs_tensor += build_external_inputs_from_csv_for_reach(
                    stub, pth, r_idx, default_sigma_g=default_sigma_g, grain_unit=grain_unit
                )

        # Load precomputed tensor if provided
        if 'tensor_npy' in external_inputs_cfg and external_inputs_cfg['tensor_npy']:
            npy_path = (base_dir / external_inputs_cfg['tensor_npy']).resolve()
            tensor = np.load(npy_path)
            if external_inputs_tensor is None:
                external_inputs_tensor = tensor
            else:
                # Sum with any other sources
                external_inputs_tensor = external_inputs_tensor + tensor

    print("Starting simulation...")
    # Ensure roundpar is an integer (number of decimal digits)
    roundpar = int(opts.get('round_parameter', 0))

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
        roundpar=roundpar,
        external_inputs=external_inputs_tensor, 
        force_pass_external_inputs=opts.get('force_pass_external_inputs', False),
        overbank_Q=overbank_Q,
    )

    # Add reach_id mapping to output
    # This ensures we know which reach index corresponds to which ID (FromN or explicit reach_id)
    if reach_data.reach_id is not None:
        data_output['reach_id'] = reach_data.reach_id
    else:
        data_output['reach_id'] = reach_data.from_n

    # Store the input discharge array so the results viewer can plot it
    data_output['Discharge [m^3/s]'] = Q

    print("Simulation completed.")

    # Save outputs to a logical destination. Prefer `paths.output_dir` if provided,
    # otherwise use the default `cascade_results` folder next to the config file.
    output_dir_cfg = paths.get('output_dir') if isinstance(paths, dict) else None
    if output_dir_cfg:
        results_dir = (base_dir / Path(output_dir_cfg)).resolve()
    else:
        results_dir = base_dir / 'cascade_results'

    results_dir.mkdir(parents=True, exist_ok=True)

    # Primary output
    name_file = results_dir / Path(str(output_name) + '.json')
    save_to_json(data_output, name_file)
    print(f"Saved results to {name_file}")

    # Extended output if present
    if extended_output is not None:
        name_file_ext = results_dir / Path(str(output_name) + '_ext.json')
        save_to_json(extended_output, name_file_ext)
        print(f"Saved extended results to {name_file_ext}")

    return data_output, extended_output

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_dcascade_json.py <config.json>")
        sys.exit(1)
    
    run_simulation(sys.argv[1])
