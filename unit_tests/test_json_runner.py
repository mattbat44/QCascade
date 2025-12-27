import sys
import os
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Add source (src) folder in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
# Add json_runner folder in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../json_runner')))

from run_dcascade_json import run_simulation

# Define paths relative to this test file
TEST_DIR = Path(__file__).parent
ROOT_DIR = TEST_DIR.parent
INPUTS_DIR = ROOT_DIR / 'inputs' / 'input_trial'

def test_Vjosa_Engelund_json():
    """
    Replicates test_Vjosa_Engelund_all_true_no_tlag from test_Vjosa_case.py
    using the JSON runner.
    """
    
    # Configuration matching the test case
    config = {
        "paths": {
            "river_network_shp": str(INPUTS_DIR / 'River_Network.shp'),
            "discharge_csv": str(INPUTS_DIR / 'Q_Vjosa.csv'),
            "output_name": "Vjosa_test_json_engelund"
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
            "transport_capacity_formula": 3,  # Engelund and Hansen
            "transport_partitioning": 2,      # BMF
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

    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump(config, tmp)
        tmp_path = tmp.name

    try:
        # Run simulation
        data_output, extended_output = run_simulation(tmp_path)

        # Assertions from test_Vjosa_case.py -> test_Vjosa_Engelund_all_true_no_tlag
        
        # Test the total mobilised volume per reach
        test_result_out = np.sum(data_output['Volume out [m^3]'], axis=0)
        expected_result_out = np.array([431292., 177463., 138996.,  71630.,  88802.,   7794.,  13352.])
        np.testing.assert_array_equal(test_result_out, expected_result_out)

        # Test the total transported volume per reach
        test_result_in = np.sum(data_output['Volume in [m^3]'], axis=0)
        expected_result_in = np.array([     0., 520094., 185257., 152348.,      0.,      0.,      0.])
        np.testing.assert_allclose(test_result_in, expected_result_in, atol=1e06)

    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_Vjosa_Wilcock_json():
    """
    Replicates test_Vjosa_Wilcock_all_true_no_tlag from test_Vjosa_case.py
    using the JSON runner.
    """
    
    # Configuration matching the test case
    config = {
        "paths": {
            "river_network_shp": str(INPUTS_DIR / 'River_Network.shp'),
            "discharge_csv": str(INPUTS_DIR / 'Q_Vjosa.csv'),
            "output_name": "Vjosa_test_json_wilcock"
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
            "transport_capacity_formula": 2,  # Wilcock and Crowe
            "transport_partitioning": 4,      # Shear stress correction
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

    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump(config, tmp)
        tmp_path = tmp.name

    try:
        # Run simulation
        data_output, extended_output = run_simulation(tmp_path)

        # Assertions from test_Vjosa_case.py -> test_Vjosa_Wilcock_all_true_no_tlag
        
        # Test the total mobilised volume per reach
        test_result_out = np.sum(data_output['Volume out [m^3]'], axis=0)
        expected_result_out = np.array([2.245782e+06, 5.261160e+05, 2.874930e+05, 7.204900e+04,
                                        8.078890e+05, 1.185800e+05, 1.840180e+05])
        np.testing.assert_array_equal(test_result_out, expected_result_out)

        # Test the total transported volume per reach
        test_result_in = np.sum(data_output['Volume in [m^3]'], axis=0)
        expected_result_in = np.array([0.000000e+00, 3.053671e+06, 6.446960e+05, 4.715110e+05,
                                       0.000000e+00, 0.000000e+00, 0.000000e+00])
        np.testing.assert_array_equal(test_result_in, expected_result_in)

    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_Vjosa_json_with_external_inputs(tmp_path):
    """
    Run JSON runner with and without external inputs and ensure outputs differ.
    """

    # Prepare an external inputs directory with minimal CSVs
    ext_dir = tmp_path / 'ext_inputs'
    ext_dir.mkdir()
    # Reach 0, t=0: 100 m3 with D50=2mm
    (ext_dir / 'reach_0.csv').write_text('time_idx,D50,volume_m3\n0,2.0,100.0\n')
    # Reach 3, t=5: flux row
    (ext_dir / 'reach_3.csv').write_text('time_idx,D50,flux_m3_per_s\n5,3.0,0.005\n')

    # Base configuration
    base_config = {
        "paths": {
            "river_network_shp": str(INPUTS_DIR / 'River_Network.shp'),
            "discharge_csv": str(INPUTS_DIR / 'Q_Vjosa.csv'),
            "output_name": "Vjosa_json_external_inputs_test"
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

    # Run baseline
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump(base_config, tmp)
        tmp_path_base = tmp.name
    try:
        data_base, _ = run_simulation(tmp_path_base)
    finally:
        if os.path.exists(tmp_path_base):
            os.remove(tmp_path_base)

    # Run with external inputs
    config_ext = dict(base_config)
    config_ext["external_inputs"] = {
        "dir": str(ext_dir)
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
    assert not np.allclose(base_in_sum, ext_in_sum), "External inputs should change delivered volumes"

if __name__ == "__main__":
    test_Vjosa_Engelund_json()
    test_Vjosa_Wilcock_json()
    print("All JSON runner tests passed.")
