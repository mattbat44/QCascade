# -*- coding: utf-8 -*-
"""
Test sediment core visualization functions

@author: D-CASCADE Development Team
"""

import os
import sys
import numpy as np
import pytest
import importlib.util
import tempfile
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for all tests

# Add source (src) folder in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../post_process_examples')))


# Fixture to load the sediment core visualization module
@pytest.fixture(scope="module")
def scv_module():
    """Load the sediment core visualization module dynamically"""
    spec = importlib.util.spec_from_file_location(
        "sediment_core_visualization",
        os.path.join(os.path.dirname(__file__), '../post_process_examples/09-sediment_core_visualization.py')
    )
    scv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scv)
    return scv


def test_extract_sediment_core(scv_module):
    """Test the extract_sediment_core function"""
    scv = scv_module
    
    # Create mock Qbi_dep data structure
    # Structure: [timestep][reach_id] -> numpy array (layers x [metadata + sediment_classes])
    n_timesteps = 2
    n_reaches = 3
    n_classes = 4
    n_metadata = 1
    
    # Create mock data with 5 layers per reach
    n_layers = 5
    Qbi_dep = []
    for t in range(n_timesteps):
        timestep_data = []
        for r in range(n_reaches):
            # Each layer has metadata (provenance) + sediment volumes
            layers = np.random.rand(n_layers, n_metadata + n_classes) * 100
            # Set provenance to reach ID
            layers[:, 0] = r
            timestep_data.append(layers)
        Qbi_dep.append(timestep_data)
    
    # Test extraction
    reach_id = 1
    timestep_index = 0
    core = scv.extract_sediment_core(Qbi_dep, reach_id, timestep_index)
    
    # Verify shape
    assert core.shape == (n_layers, n_metadata + n_classes)
    # Verify it's the correct reach's data
    assert np.all(core[:, 0] == reach_id)


def test_visualize_sediment_core_no_errors(scv_module):
    """Test that visualize_sediment_core runs without errors"""
    scv = scv_module
    
    # Create mock core data
    n_layers = 10
    n_classes = 5
    n_metadata = 1
    
    # Create core with provenance and sediment volumes
    core = np.zeros((n_layers, n_metadata + n_classes))
    core[:, 0] = np.arange(n_layers) % 3  # Provenance from 3 different reaches
    core[:, 1:] = np.random.rand(n_layers, n_classes) * 100  # Random sediment volumes
    
    # Create psi array
    psi = np.linspace(-8, 5, n_classes)
    
    # Test visualization (should not raise errors)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        scv.visualize_sediment_core(core, psi, reach_id=5, timestep=0, output_path=tmp_path)
        # Check that file was created
        assert os.path.exists(tmp_path)
        assert os.path.getsize(tmp_path) > 0
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_visualize_core_summary_no_errors(scv_module):
    """Test that visualize_core_summary runs without errors"""
    scv = scv_module
    
    # Create mock Qbi_dep data
    n_timesteps = 4
    n_reaches = 3
    n_classes = 5
    n_metadata = 1
    n_layers = 8
    
    Qbi_dep = []
    for t in range(n_timesteps):
        timestep_data = []
        for r in range(n_reaches):
            layers = np.random.rand(n_layers, n_metadata + n_classes) * 100
            layers[:, 0] = r  # Set provenance
            timestep_data.append(layers)
        Qbi_dep.append(timestep_data)
    
    psi = np.linspace(-8, 5, n_classes)
    
    # Test visualization
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        scv.visualize_core_summary(Qbi_dep, psi, reach_id=1, output_path=tmp_path)
        # Check that file was created
        assert os.path.exists(tmp_path)
        assert os.path.getsize(tmp_path) > 0
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_empty_layers_handling(scv_module):
    """Test handling of empty sediment layers"""
    scv = scv_module
    
    # Create core with some empty layers
    n_layers = 5
    n_classes = 4
    n_metadata = 1
    
    core = np.zeros((n_layers, n_metadata + n_classes))
    core[:, 0] = 0  # All from reach 0
    # Make some layers empty (all zeros)
    core[1, 1:] = [10, 20, 30, 15]
    core[3, 1:] = [5, 10, 8, 12]
    
    psi = np.linspace(-8, 5, n_classes)
    
    # Should handle empty layers gracefully
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        scv.visualize_sediment_core(core, psi, reach_id=0, timestep=0, output_path=tmp_path)
        assert os.path.exists(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v'])
