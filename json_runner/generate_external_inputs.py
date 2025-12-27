# -*- coding: utf-8 -*-
"""
@brief CLI tool to generate a reusable external_inputs tensor (.npy) from user CSVs.

@details
- Loads a JSON config to derive timescale, ts_length, psi (from sediment range and n_classes), and network reach count.
- Builds the external_inputs tensor from a directory of per-reach CSVs and/or a list of CSV files.
- Saves the resulting tensor as a .npy file for reuse in JSON runs via `external_inputs.tensor_npy`.

Usage:
    uv run python json_runner/generate_external_inputs.py <config.json> --dir <folder> [--csv <file> ...] [--out <tensor.npy>] [--grain-unit mm|m] [--sigma-g 1.6]

CSV schema:
- Required: time_idx, D50, and either volume_m3 or flux_m3_per_s
- Optional: reach_idx (omit for per-reach files; inferred from filename integer)
- Optional quantile pairs: D16/D84 or D25/D75 or D35/D65

@author GitHub Copilot
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import numpy as np

# Add src to path
CURRENT_DIR = Path(__file__).parent
SRC_PATH = CURRENT_DIR.parent / 'src'
sys.path.append(str(SRC_PATH))

from external_inputs_builder import (
    build_external_inputs_from_csv,
    build_external_inputs_from_dir,
)
from preprocessing import read_network
from reach_data import ReachData


def _load_config(config_path: Path) -> dict:
    with open(config_path, 'r') as f:
        return json.load(f)


def _derive_system_stub(config: dict, n_reaches: int):
    sed = config['sediment']
    time = config['time']
    psi = np.linspace(sed['range'][0], sed['range'][1], num=sed['n_classes'], endpoint=True).astype(float)

    class _SystemStub:
        def __init__(self, timescale, n_reaches, psi, ts_length):
            self.timescale = timescale
            self.n_reaches = n_reaches
            self.psi = psi
            self.n_classes = len(psi)
            self.ts_length = ts_length

    return _SystemStub(timescale=time['timescale'], n_reaches=n_reaches, psi=psi, ts_length=time['ts_length'])


def main():
    parser = argparse.ArgumentParser(description='Generate external_inputs tensor (.npy) from CSVs using a JSON config.')
    parser.add_argument('config', type=str, help='Path to JSON config file used by the JSON runner')
    parser.add_argument('--dir', type=str, default=None, help='Directory of per-reach CSV files')
    parser.add_argument('--csv', type=str, action='append', default=None, help='CSV file to include (can be passed multiple times)')
    parser.add_argument('--out', type=str, default=None, help='Output .npy file path (default: external_inputs.npy next to config)')
    parser.add_argument('--grain-unit', type=str, default='mm', choices=['mm', 'm'], help='Units for D-quantiles')
    parser.add_argument('--sigma-g', type=float, default=1.6, help='Fallback geometric std dev when only D50 is given')

    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config = _load_config(config_path)

    base_dir = config_path.parent
    # Determine n_reaches by loading network from config paths
    river_network_path = (base_dir / config['paths']['river_network_shp']).resolve()
    reach_data_df = read_network(river_network_path)
    reach_data = ReachData(reach_data_df)

    # Build stub
    stub = _derive_system_stub(config, n_reaches=reach_data.n_reaches)

    # Aggregate sources
    external_inputs = np.zeros((stub.timescale, stub.n_reaches, stub.n_classes), dtype=float)

    if args.dir:
        dir_path = Path(args.dir)
        if not dir_path.is_absolute():
            dir_path = (base_dir / dir_path).resolve()
        external_inputs += build_external_inputs_from_dir(stub, dir_path, default_sigma_g=args.sigma_g, grain_unit=args.grain_unit)

    if args.csv:
        for csv_file in args.csv:
            csv_path = Path(csv_file)
            if not csv_path.is_absolute():
                csv_path = (base_dir / csv_path).resolve()
            external_inputs += build_external_inputs_from_csv(stub, csv_path, default_sigma_g=args.sigma_g, grain_unit=args.grain_unit)

    # Output
    out_path = Path(args.out) if args.out else (config_path.parent / 'external_inputs.npy')
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_path, external_inputs)

    print(f"Saved external_inputs tensor to {out_path}")


if __name__ == '__main__':
    main()
