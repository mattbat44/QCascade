"""
JSON serialization wrapper for D-CASCADE output data.

This module provides safe JSON-based serialization as an alternative to pickle.
It handles numpy arrays and preserves data types during round-trip serialization.

@author: GitHub Copilot
"""

import json
import numpy as np
from pathlib import Path
from typing import Any, Dict, Union


class NumpyEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles numpy arrays and data types.
    """
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return {
                '__ndarray__': obj.tolist(),
                'dtype': str(obj.dtype),
                'shape': obj.shape
            }
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


def numpy_decoder(dct: Dict) -> Any:
    """
    Custom JSON decoder that reconstructs numpy arrays from their JSON representation.
    
    @param dct: Dictionary potentially containing serialized numpy arrays
    @return: Reconstructed object (numpy array if applicable, otherwise original dict)
    """
    if '__ndarray__' in dct:
        return np.array(dct['__ndarray__'], dtype=np.dtype(dct['dtype']))
    return dct


def save_to_json(data: Dict[str, Any], filepath: Union[str, Path]) -> None:
    """
    Save a dictionary containing numpy arrays to a JSON file.
    
    This function serializes data_output or extended_output dictionaries from D-CASCADE
    simulations to JSON format. Numpy arrays are converted to lists with metadata
    to preserve their dtype and shape.
    
    @param data: Dictionary containing simulation results (may include numpy arrays)
    @param filepath: Path where the JSON file will be saved
    """
    filepath = Path(filepath)
    
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to JSON with custom encoder
    with open(filepath, 'w') as f:
        json.dump(data, f, cls=NumpyEncoder, indent=2)


def load_from_json(filepath: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a dictionary from a JSON file, reconstructing numpy arrays.
    
    This function deserializes data_output or extended_output dictionaries that were
    saved using save_to_json(). Numpy arrays are reconstructed with their original
    dtype and shape.
    
    @param filepath: Path to the JSON file to load
    @return: Dictionary containing simulation results with numpy arrays reconstructed
    """
    filepath = Path(filepath)
    
    with open(filepath, 'r') as f:
        data = json.load(f, object_hook=numpy_decoder)
    
    return data
