"""
Unit tests for external_inputs_builder
"""
import os
import sys
from pathlib import Path

# Add source (src) folder in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import numpy as np
import pandas as pd

from external_inputs_builder import (
    build_external_inputs_from_csv,
    build_external_inputs_from_dir,
)


class SystemStub:
    def __init__(self, timescale, n_reaches, psi, ts_length):
        self.timescale = timescale
        self.n_reaches = n_reaches
        self.psi = psi
        self.n_classes = len(psi)
        self.ts_length = ts_length


def test_build_external_inputs_from_csv(tmp_path):
    # Prepare stub system
    psi = np.array([-2, -1, 0, 1], dtype=float)
    system = SystemStub(timescale=5, n_reaches=3, psi=psi, ts_length=60*60*24)

    # Create CSV with volume and flux rows
    p = tmp_path / 'ext.csv'
    df = pd.DataFrame([
        {"time_idx": 1, "reach_idx": 2, "D50": 2.0, "D16": 1.5, "D84": 2.5, "volume_m3": 10.0},
        {"time_idx": 2, "reach_idx": 0, "D50": 4.0, "flux_m3_per_s": 0.001},
    ])
    df.to_csv(p, index=False)

    ext = build_external_inputs_from_csv(system, p)
    assert ext.shape == (5, 3, 4)

    # Check total volumes placed
    assert np.isclose(ext[1, 2, :].sum(), 10.0)
    assert np.isclose(ext[2, 0, :].sum(), 0.001 * system.ts_length)

    # Fractions normalize to 1 per placement (non-zero rows)
    fracs1 = ext[1, 2, :] / ext[1, 2, :].sum()
    assert np.isclose(fracs1.sum(), 1.0)


def test_build_external_inputs_from_dir(tmp_path):
    psi = np.array([-2, -1, 0, 1], dtype=float)
    system = SystemStub(timescale=4, n_reaches=6, psi=psi, ts_length=60*60*24)

    # File 1 without reach_idx, infer from filename (reach_2.csv)
    f1 = tmp_path / 'reach_2.csv'
    pd.DataFrame([
        {"time_idx": 0, "D50": 2.0, "volume_m3": 5.0}
    ]).to_csv(f1, index=False)

    # File 2 with explicit reach_idx
    f2 = tmp_path / 'custom.csv'
    pd.DataFrame([
        {"time_idx": 1, "reach_idx": 5, "D50": 3.0, "D25": 2.5, "D75": 3.5, "volume_m3": 7.0}
    ]).to_csv(f2, index=False)

    ext = build_external_inputs_from_dir(system, tmp_path)
    assert ext.shape == (4, 6, 4)

    assert np.isclose(ext[0, 2, :].sum(), 5.0)
    assert np.isclose(ext[1, 5, :].sum(), 7.0)
