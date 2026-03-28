"""
JSON serialization wrapper for D-CASCADE output data.

This module provides safe JSON-based serialization as an alternative to pickle.
It handles numpy arrays and preserves data types during round-trip serialization.
It also provides helpers to export simulation results to Excel spreadsheets.

@author: GitHub Copilot
"""

import json
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


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


def results_to_spreadsheet(
    data_output: Dict[str, Any],
    filepath: Union[str, Path],
    extended_output: Optional[Dict[str, Any]] = None,
    reach_ids: Optional[List] = None,
) -> None:
    """
    Export D-CASCADE simulation results to an Excel spreadsheet (.xlsx).

    Each 2-D result variable (time × reach) is written to a dedicated sheet.
    3-D variables (time × reach × sediment class) produce one sheet per
    sediment class, named "<variable> – class <n>".
    Variables with more than 3 dimensions or non-array entries (e.g. the
    'Simulation parameters' dict) are skipped.

    Both *data_output* (standard results) and the optional *extended_output*
    (per-grain-size / raw cascade data) are exported; each is written to its
    own group of sheets.

    @param data_output: Main results dictionary returned by DCASCADE_main.
    @param filepath: Destination path for the Excel file (must end in .xlsx).
    @param extended_output: Optional extended results dictionary.
    @param reach_ids: Optional list of reach IDs used as column headers.
                      Defaults to sequential integers (1, 2, …).
    """
    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError(
            "pandas is required for spreadsheet export. "
            "Install it with: pip install pandas openpyxl"
        ) from exc

    filepath = Path(filepath)
    if filepath.suffix.lower() != ".xlsx":
        filepath = filepath.with_suffix(".xlsx")
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ helpers

    def _safe_sheet_name(base: str, suffix: str = "") -> str:
        """Return an Excel-safe sheet name (max 31 chars, no forbidden chars).

        The *suffix* (e.g. a class index) is always preserved; only *base* is
        truncated when the combined length would exceed 31 characters.
        """
        forbidden = r"\/*?:[]"
        clean_base = "".join(c if c not in forbidden else "_" for c in base)
        clean_suffix = "".join(c if c not in forbidden else "_" for c in suffix)
        max_base = max(0, 31 - len(clean_suffix))
        return clean_base[:max_base] + clean_suffix

    def _unique_sheet_name(candidate: str, used: set) -> str:
        """Resolve duplicate sheet names by appending a counter."""
        name = candidate
        counter = 1
        while name in used:
            tag = f"_{counter}"
            name = candidate[: 31 - len(tag)] + tag
            counter += 1
        used.add(name)
        return name

    def _array_to_dataframe(arr: np.ndarray, col_ids: List) -> "pd.DataFrame":
        """Convert a 2-D (time × reach) array to a labelled DataFrame."""
        import pandas as pd
        cols = [f"Reach {r}" for r in col_ids] if col_ids else [f"Reach {i + 1}" for i in range(arr.shape[1])]
        index = pd.RangeIndex(start=1, stop=arr.shape[0] + 1, name="Time Step")
        return pd.DataFrame(arr, index=index, columns=cols)

    def _write_dict(writer: "pd.ExcelWriter", source: Dict[str, Any], col_ids: List, used_names: set) -> None:
        """Write all exportable arrays from *source* into *writer*."""
        for var_name, value in source.items():
            if not isinstance(value, np.ndarray):
                continue
            arr = np.asarray(value, dtype=float)

            if arr.ndim == 2:
                sheet = _unique_sheet_name(_safe_sheet_name(var_name), used_names)
                df = _array_to_dataframe(arr, col_ids)
                df.to_excel(writer, sheet_name=sheet)

            elif arr.ndim == 3:
                n_classes = arr.shape[2]
                for cls_idx in range(n_classes):
                    suffix = f" C{cls_idx + 1}"
                    sheet = _unique_sheet_name(_safe_sheet_name(var_name, suffix), used_names)
                    df = _array_to_dataframe(arr[:, :, cls_idx], col_ids)
                    df.to_excel(writer, sheet_name=sheet)
            # Arrays with 4+ dimensions are skipped (too complex for flat sheets)

    # ------------------------------------------------------------------ export
    import pandas as pd

    col_ids = list(reach_ids) if reach_ids is not None else []

    # Infer reach count from the first suitable 2-D array when reach_ids not given
    if not col_ids:
        for val in data_output.values():
            if isinstance(val, np.ndarray) and val.ndim >= 2:
                col_ids = list(range(1, val.shape[1] + 1))
                break

    used_names: set = set()
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        _write_dict(writer, data_output, col_ids, used_names)
        if extended_output:
            _write_dict(writer, extended_output, col_ids, used_names)
