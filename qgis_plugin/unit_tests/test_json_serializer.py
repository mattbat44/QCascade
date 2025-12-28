"""
Tests for JSON serialization wrapper.

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


def test_save_and_load_simple_dict():
    """Test saving and loading a simple dictionary."""
    data = {
        'key1': 'value1',
        'key2': 42,
        'key3': [1, 2, 3]
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.json'
        save_to_json(data, filepath)
        loaded_data = load_from_json(filepath)
        
        assert loaded_data == data


def test_save_and_load_numpy_arrays():
    """Test saving and loading numpy arrays with various dtypes."""
    data = {
        'array_float32': np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
        'array_float64': np.array([1.1, 2.2, 3.3], dtype=np.float64),
        'array_int': np.array([1, 2, 3], dtype=np.int32),
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.json'
        save_to_json(data, filepath)
        loaded_data = load_from_json(filepath)
        
        # Check all arrays are present and equal
        assert set(loaded_data.keys()) == set(data.keys())
        for key in data.keys():
            np.testing.assert_array_equal(loaded_data[key], data[key])
            assert loaded_data[key].dtype == data[key].dtype


def test_save_and_load_3d_array():
    """Test saving and loading 3D numpy arrays (common in D-CASCADE)."""
    data = {
        'connectivity': np.random.rand(10, 50, 50).astype(np.float32),
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.json'
        save_to_json(data, filepath)
        loaded_data = load_from_json(filepath)
        
        assert loaded_data['connectivity'].shape == data['connectivity'].shape
        assert loaded_data['connectivity'].dtype == data['connectivity'].dtype
        np.testing.assert_array_almost_equal(loaded_data['connectivity'], data['connectivity'])


def test_save_and_load_mixed_data():
    """Test saving and loading data with mixed types (like data_output)."""
    data = {
        'Simulation parameters': {
            'psi': [-6, -5, -4],
            'ts length': 86400,
            'update slope': False,
            'idx flow': 1,
        },
        'Volume out [m^3]': np.random.rand(100, 50).astype(np.float32),
        'Volume in [m^3]': np.random.rand(100, 50).astype(np.float32),
        'D50 active layer [m]': np.random.rand(100, 50).astype(np.float32),
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.json'
        save_to_json(data, filepath)
        loaded_data = load_from_json(filepath)
        
        # Check nested dict
        assert loaded_data['Simulation parameters'] == data['Simulation parameters']
        
        # Check arrays
        for key in ['Volume out [m^3]', 'Volume in [m^3]', 'D50 active layer [m]']:
            assert loaded_data[key].shape == data[key].shape
            assert loaded_data[key].dtype == data[key].dtype
            np.testing.assert_array_almost_equal(loaded_data[key], data[key], decimal=5)


def test_directory_creation():
    """Test that parent directories are created if they don't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'subdir' / 'nested' / 'test.json'
        data = {'key': 'value'}
        
        save_to_json(data, filepath)
        assert filepath.exists()
        
        loaded_data = load_from_json(filepath)
        assert loaded_data == data


def test_numpy_scalar_types():
    """Test that numpy scalar types are properly handled."""
    data = {
        'int_val': np.int32(42),
        'float_val': np.float32(3.14),
        'bool_val': np.bool_(True),
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / 'test.json'
        save_to_json(data, filepath)
        loaded_data = load_from_json(filepath)
        
        # After round-trip, numpy scalars become Python types
        assert loaded_data['int_val'] == 42
        assert abs(loaded_data['float_val'] - 3.14) < 0.01
        assert loaded_data['bool_val'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
