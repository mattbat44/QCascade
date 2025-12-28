import sys
import os
import json
import tempfile
import numpy as np
from pathlib import Path

# Add src and json_runner to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../json_runner')))

from run_dcascade_json import run_simulation

TEST_DIR = Path(__file__).parent
ROOT_DIR = TEST_DIR.parent.parent
INPUTS_DIR = ROOT_DIR / 'inputs' / 'input_trial'


def _base_config(output_name: str):
    return {
        "paths": {
            "river_network_shp": str(INPUTS_DIR / 'River_Network.shp'),
            "discharge_csv": str(INPUTS_DIR / 'Q_Vjosa.csv'),
            "output_name": output_name
        },
        "sediment": {
            "range": [-8, 5],
            "n_classes": 6,
            "deposit_layer_thickness": 100000,
            "active_layer_depth": "2D90",
            "active_layer_method": 2
        },
        "time": {
            "timescale": 20,
            "ts_length": 86400
        },
        "physics": {
            "transport_capacity_formula": 3,
            "transport_partitioning": 2,
            "flow_depth_formula": 1,
            "velocity_formula": 2,
            "velocity_partitioning": 1,
            "slope_reduction": 1,
            "width_calculation": 1,
            "update_slope": False,
            "velocity_height": "2D90",
            "erosion_max": 1
        },
        "options": {
            "save_deposit_layer": "never",
            "round_parameter": 0,
            "force_pass_external_inputs": False
        }
    }


def test_generate_external_inputs_and_use_in_json(tmp_path):
    # Create external inputs directory
    ext_dir = tmp_path / 'ext_inputs'
    ext_dir.mkdir()
    (ext_dir / 'reach_0.csv').write_text('time_idx,D50,volume_m3\n0,2.0,100.0\n')
    (ext_dir / 'reach_3.csv').write_text('time_idx,D50,flux_m3_per_s\n5,3.0,0.005\n')

    # Build config without external inputs
    base_config = _base_config('Vjosa_json_gen_test')

    # Run baseline
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump(base_config, tmp)
        tmp_path_base = tmp.name
    try:
        data_base, _ = run_simulation(tmp_path_base)
    finally:
        if os.path.exists(tmp_path_base):
            os.remove(tmp_path_base)

    # Generate npy using the generator script (import as module)
    from generate_external_inputs import _load_config, _derive_system_stub
    from external_inputs_builder import build_external_inputs_from_dir
    cfg_path = tmp_path / 'cfg.json'
    cfg_path.write_text(json.dumps(base_config))

    config = _load_config(cfg_path)
    # Derive n_reaches by reading network
    from preprocessing import read_network
    from reach_data import ReachData
    reach_data_df = read_network(Path(base_config['paths']['river_network_shp']))
    reach_data = ReachData(reach_data_df)
    stub = _derive_system_stub(config, n_reaches=reach_data.n_reaches)

    tensor = build_external_inputs_from_dir(stub, ext_dir)
    npy_path = tmp_path / 'external_inputs.npy'
    np.save(npy_path, tensor)

    # Run with tensor_npy
    config_ext = dict(base_config)
    config_ext['external_inputs'] = {
        'tensor_npy': str(npy_path)
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump(config_ext, tmp)
        tmp_path_ext = tmp.name
    try:
        data_ext, _ = run_simulation(tmp_path_ext)
    finally:
        if os.path.exists(tmp_path_ext):
            os.remove(tmp_path_ext)

    base_in_sum = np.sum(data_base['Volume in [m^3]'], axis=0)
    ext_in_sum = np.sum(data_ext['Volume in [m^3]'], axis=0)
    assert not np.allclose(base_in_sum, ext_in_sum), 'Using tensor_npy should change delivered volumes'
