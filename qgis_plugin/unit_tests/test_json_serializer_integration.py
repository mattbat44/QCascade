"""
Integration test to verify JSON serialization works with D-CASCADE data structures.

@author: GitHub Copilot
"""

import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Add source (src) folder in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from json_serializer import save_to_json, load_from_json


def test_dcascade_data_output_structure():
    """Test serialization of a typical data_output structure from D-CASCADE."""
    # Simulate typical data_output structure
    simulation_param = {
        'psi': [-6, -5, -4, -3],
        'ts length': 86400,
        'update slope': False,
        'idx flow': 1,
        'idx slope red': 1,
        'idx width calc': 1,
        'idx tr cap': 1,
        'idx tr partition': 1,
        'idx velocity': 2,
        'idx vel partition': 1
    }
    
    # Simulate output data with realistic dimensions
    timescale = 100
    n_reaches = 50
    
    data_output = {
        'Simulation parameters': simulation_param,
        'Volume out [m^3]': np.random.rand(timescale, n_reaches).astype(np.float32),
        'Volume in [m^3]': np.random.rand(timescale, n_reaches).astype(np.float32),
        'Sediment budget [m^3]': np.random.rand(timescale, n_reaches).astype(np.float32),
        'Mobilised from reach [m^3]': np.random.rand(timescale, n_reaches).astype(np.float32),
        'Deposited [m^3]': np.random.rand(timescale, n_reaches).astype(np.float32),
        'Volume outlet [m^3]': np.random.rand(timescale).astype(np.float32),
        'D50 volume out [m]': np.random.rand(timescale, n_reaches).astype(np.float32),
        'D50 active layer [m]': np.random.rand(timescale, n_reaches).astype(np.float32),
        'Direct connectivity [m^3]': np.random.rand(timescale, n_reaches, n_reaches + 1).astype(np.float32),
        'Overbank deposited [m^3]': np.random.rand(timescale, n_reaches).astype(np.float32),
        'Transport capacity [m^3]': np.random.rand(timescale, n_reaches).astype(np.float32),
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test_data_output.json'
        
        # Save
        save_to_json(data_output, filepath)
        
        # Check file was created
        assert filepath.exists()
        
        # Load
        loaded_data = load_from_json(filepath)
        
        # Verify structure
        assert set(loaded_data.keys()) == set(data_output.keys())
        
        # Verify simulation parameters
        assert loaded_data['Simulation parameters'] == simulation_param
        
        # Verify numpy arrays
        for key in data_output.keys():
            if key != 'Simulation parameters':
                assert isinstance(loaded_data[key], np.ndarray)
                assert loaded_data[key].shape == data_output[key].shape
                assert loaded_data[key].dtype == data_output[key].dtype
                np.testing.assert_array_almost_equal(loaded_data[key], data_output[key], decimal=5)


def test_dcascade_extended_output_structure():
    """Test serialization of a typical extended_output structure from D-CASCADE."""
    # Simulate extended output with 4D arrays
    timescale = 100
    n_reaches = 50
    n_classes = 4
    n_provenances = 10
    
    extended_output = {
        'Volume out per grain sizes [m^3]': np.random.rand(timescale, n_reaches, n_classes),
        'Volume in per grain sizes [m^3]': np.random.rand(timescale, n_reaches, n_classes),
        'Deposited per grain sizes [m^3]': np.random.rand(timescale, n_reaches, n_classes),
        'Overbank deposited per grain sizes [m^3]': np.random.rand(timescale, n_reaches, n_classes),
        'Qbi_mob [m^3]': [np.random.rand(n_provenances, n_reaches, n_classes) for _ in range(timescale)],
        'Qbi_tr [m^3]': [np.random.rand(n_provenances, n_reaches, n_classes) for _ in range(timescale)],
        'Qbi_mob_from_reach [m^3]': [np.random.rand(n_provenances, n_reaches, n_classes) for _ in range(timescale)],
        'Qbi_dep [m^3]': [np.random.rand(n_provenances, n_reaches, n_classes) for _ in range(timescale)],
        'Qout per class [m^3]': np.random.rand(timescale, n_classes).astype(np.float32),
        'Sediment budget per class [m^3]': np.random.rand(timescale, n_reaches, n_classes).astype(np.float32),
        'Tr_cap per class [m^3]': np.random.rand(timescale, n_reaches, n_classes).astype(np.float32),
        'Node_el [m]': np.random.rand(timescale, n_reaches + 1),
        'Fi_al': np.random.rand(timescale, n_reaches, n_classes).astype(np.float32),
        'AL depth [m]': np.random.rand(timescale, n_reaches).astype(np.float32),
        'Velocity section height [m]': np.random.rand(timescale, n_reaches).astype(np.float32),
        'Velocities [m/s]': np.random.rand(timescale, n_reaches).astype(np.float32),
        'Widths [m]': np.random.rand(timescale, n_reaches).astype(np.float32),
        'Slopes': np.random.rand(timescale, n_reaches).astype(np.float32),
        'Mass balance [m^3]': np.random.rand(timescale, n_reaches).astype(np.float32),
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test_extended_output.json'
        
        # Save
        save_to_json(extended_output, filepath)
        
        # Check file was created
        assert filepath.exists()
        
        # Load
        loaded_data = load_from_json(filepath)
        
        # Verify structure
        assert set(loaded_data.keys()) == set(extended_output.keys())
        
        # Verify arrays (including lists of arrays)
        for key in extended_output.keys():
            if isinstance(extended_output[key], list):
                # List of arrays case
                assert len(loaded_data[key]) == len(extended_output[key])
                for i in range(len(extended_output[key])):
                    np.testing.assert_array_almost_equal(
                        loaded_data[key][i], 
                        extended_output[key][i], 
                        decimal=5
                    )
            else:
                # Regular array case
                assert loaded_data[key].shape == extended_output[key].shape
                assert loaded_data[key].dtype == extended_output[key].dtype
                np.testing.assert_array_almost_equal(loaded_data[key], extended_output[key], decimal=5)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
