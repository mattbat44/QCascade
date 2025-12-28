"""
Integration test: Run Vjosa with and without external inputs and check outputs differ.
"""
import os
import sys
from pathlib import Path

# Add source (src) folder in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import numpy as np
import pandas as pd

from dcascade_main import DCASCADE_main
from preprocessing import extract_Q, graph_preprocessing, read_network
from reach_data import ReachData
from external_inputs_builder import build_external_inputs_from_dir

# Root and input paths
ROOT_DIR = Path(__file__).resolve().parent.parent
path_river_network = ROOT_DIR / Path('inputs/input_trial/')
filename_river_network = path_river_network / 'River_Network.shp'
path_q = ROOT_DIR / Path('inputs/input_trial/')
filename_q = path_q / 'Q_Vjosa.csv'

# Simulation parameters (aligned with existing Vjosa tests for speed)
deposit_layer = 100000
eros_max = 1
al_depth = '2D90'
al_depth_method = 2
timescale = 20
ts_length = 60 * 60 * 24
sed_range = [-8, 5]
n_classes = 6
roundpar = 0


def _setup_vjosa():
    network = read_network(filename_river_network)
    reach_data = ReachData(network)
    reach_data.deposit = np.repeat(deposit_layer, reach_data.n_reaches)
    sorted_indices = reach_data.sort_values_by(reach_data.from_n)
    Network = graph_preprocessing(reach_data)

    Q = extract_Q(filename_q)
    Q_new = np.zeros(Q.shape)
    for i, idx in enumerate(sorted_indices):
        Q_new[:, i] = Q.iloc[:, idx]

    psi = np.linspace(sed_range[0], sed_range[1], num=n_classes, endpoint=True).astype(float)

    deposit_volumes = reach_data.deposit * reach_data.length
    Qbi_dep_in = np.zeros((reach_data.n_reaches, 1, n_classes))
    # Simple uniform fractions (avoid curve-fit dependency here)
    Fi_uniform = np.full(n_classes, 1.0 / n_classes)
    for n in range(reach_data.n_reaches):
        Qbi_dep_in[n] = deposit_volumes[n] * Fi_uniform

    return reach_data, Network, Q_new, psi, Qbi_dep_in


def test_vjosa_outputs_change_with_external_inputs(tmp_path):
    reach_data, Network, Q, psi, Qbi_dep_in = _setup_vjosa()

    # Baseline run without external inputs
    data_base, _ = DCASCADE_main(
        reach_data, Network, Q, psi, timescale, ts_length,
        al_depth, 3, 2, Qbi_dep_in,
        al_depth_method=al_depth_method,
        eros_max=eros_max,
    )

    # Create a directory of simple external inputs affecting a couple of reaches/timesteps
    # File naming includes reach index for inference
    # Reach 0, t=0: 100 m3 with D50=2mm
    pd.DataFrame([
        {"time_idx": 0, "D50": 2.0, "volume_m3": 100.0}
    ]).to_csv(tmp_path / 'reach_0.csv', index=False)
    # Reach 3, t=5: flux row
    pd.DataFrame([
        {"time_idx": 5, "D50": 3.0, "flux_m3_per_s": 0.005}
    ]).to_csv(tmp_path / 'reach_3.csv', index=False)

    # Build external inputs tensor using a lightweight stub to provide attributes
    class Stub:
        def __init__(self, timescale, n_reaches, psi, ts_length):
            self.timescale = timescale
            self.n_reaches = n_reaches
            self.psi = psi
            self.n_classes = len(psi)
            self.ts_length = ts_length
    stub = Stub(timescale=timescale, n_reaches=reach_data.n_reaches, psi=psi, ts_length=ts_length)

    external_inputs = build_external_inputs_from_dir(stub, tmp_path)

    # Run with external inputs
    data_ext, _ = DCASCADE_main(
        reach_data, Network, Q, psi, timescale, ts_length,
        al_depth, 3, 2, Qbi_dep_in,
        al_depth_method=al_depth_method,
        eros_max=eros_max,
        external_inputs=external_inputs,
        force_pass_external_inputs=False,
    )

    # Compare a key output: total 'Volume in [m^3]' per reach should differ
    base_in_sum = np.sum(data_base['Volume in [m^3]'], axis=0)
    ext_in_sum = np.sum(data_ext['Volume in [m^3]'], axis=0)

    assert not np.allclose(base_in_sum, ext_in_sum), "External inputs should change delivered volumes"
