# -*- coding: utf-8 -*-
"""
@brief Build external_inputs tensors from simple CSVs with D-quantiles per reach/time.

@details
- Fits a log-normal grain-size distribution using provided quantiles (D50 required; optional pairs D16/D84, D25/D75, or D35/D65).
- Discretizes the CDF into psi classes to get per-class fractions.
- Multiplies fractions by total volume per time step (volume_m3 or flux_m3_per_s * ts_length).
- Returns external_inputs shaped (timescale, n_reaches, n_classes).

CSV columns (zero-based indices):
  time_idx, reach_idx?, D50[, D16, D84 | D25, D75 | D35, D65], volume_m3 | flux_m3_per_s

Directory mode:
  Each .csv file represents a reach. If the file rows do not include 'reach_idx', the reach index is inferred
  from the filename by extracting the first integer found in the stem (e.g. 'reach_10.csv' -> 10).

Assumptions:
- D-values are in millimeters by default (grain_unit='mm'). Set grain_unit='m' to convert meters to mm.
- If only D50 is provided, uses default sigma_g (geometric std dev) to set spread.

@author Matt Adams
"""
from __future__ import annotations
from pathlib import Path
import math
import re
import numpy as np
import pandas as pd

# Precomputed z-scores for common percentiles of N(0,1)
_Z = {
    0.16: -0.994457,
    0.25: -0.67448975,
    0.35: -0.385320466,
    0.65:  0.385320466,
    0.75:  0.67448975,
    0.84:  0.994457,
}


def _psi_to_D_mm(psi: np.ndarray) -> np.ndarray:
    """
    @brief Convert psi (Krumbein phi) class centers to diameter in mm.
    @details D_mm = 2 ** (-psi)
    """
    return np.power(2.0, -np.array(psi, dtype=float))


def _class_edges_mm(psi: np.ndarray) -> np.ndarray:
    """
    @brief Build class edges (in mm) from psi class centers by mid-pointing in log(D) space.
    @details Extrapolates end edges by reflecting the end gaps.
    @return edges array of length n_classes+1 in mm.
    """
    D = _psi_to_D_mm(psi)
    logD = np.log(D)
    if len(logD) < 2:
        # Degenerate single-class: build arbitrary edges around D
        gap = 0.25
        edges_logD = np.array([logD[0] - gap, logD[0] + gap])
        return np.exp(edges_logD)
    mids = 0.5 * (logD[:-1] + logD[1:])
    first_edge = logD[0] + (logD[0] - mids[0])
    last_edge  = logD[-1] + (logD[-1] - mids[-1])
    edges_logD = np.concatenate(([first_edge], mids, [last_edge]))
    return np.exp(edges_logD)


def _fit_lognormal_mu_sigma_ln(row: pd.Series, default_sigma_g: float) -> tuple[float, float]:
    """
    @brief Fit log-normal parameters (mu, sigma_ln) from quantiles.
    @details Dp = exp(mu + z_p * sigma_ln)
      - mu = ln(D50)
      - sigma_ln from any symmetric pair if available, else ln(default_sigma_g)
    """
    def _get(name):
        v = row.get(name)
        return float(v) if (v is not None and not (isinstance(v, float) and np.isnan(v))) else None

    D50 = _get("D50")
    if D50 is None or D50 <= 0:
        raise ValueError("D50 must be provided and > 0")

    pairs = [
        ("D16", 0.16, "D84", 0.84),
        ("D25", 0.25, "D75", 0.75),
        ("D35", 0.35, "D65", 0.65),
    ]
    sigma_ln = None
    for n1, p1, n2, p2 in pairs:
        Dlow, Dhigh = _get(n1), _get(n2)
        if Dlow and Dhigh and Dlow > 0 and Dhigh > 0:
            z1, z2 = _Z[p1], _Z[p2]
            sigma_ln = (math.log(Dhigh) - math.log(Dlow)) / (z2 - z1)
            break

    if sigma_ln is None:
        sigma_ln = math.log(default_sigma_g)

    mu = math.log(D50)
    return mu, sigma_ln


def _erf_np(x: np.ndarray) -> np.ndarray:
    """
    @brief Vectorized approximation of erf(x) using Abramowitz-Stegun 7.1.26.
    @details Avoids dependency on numpy.special/scipy which may be unavailable.
    """
    # constants
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911

    sign = np.sign(x)
    x_abs = np.abs(x)
    t = 1.0 / (1.0 + p * x_abs)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * np.exp(-x_abs * x_abs)
    return sign * y

def _lognormal_cdf(D_mm: np.ndarray, mu: float, sigma_ln: float) -> np.ndarray:
    """
    @brief Log-normal CDF at diameters D_mm.
    """
    z = (np.log(D_mm) - mu) / (sigma_ln * math.sqrt(2.0))
    return 0.5 * (1.0 + _erf_np(z))


def _fractions_from_lognormal(psi: np.ndarray, mu: float, sigma_ln: float) -> np.ndarray:
    """
    @brief Discretize log-normal CDF into psi bins to get per-class fractions.
    """
    edges = np.sort(_class_edges_mm(psi))
    cdf = _lognormal_cdf(edges, mu, sigma_ln)
    fracs = np.diff(cdf)
    fracs[fracs < 0] = 0
    s = fracs.sum()
    return fracs / s if s > 0 else np.zeros_like(fracs)


def _unit_scale(grain_unit: str) -> float:
    """@brief Return scale to convert input D-values to millimeters."""
    if str(grain_unit).lower() == "m":
        return 1000.0
    return 1.0


def _infer_reach_index_from_filename(path: Path) -> int | None:
    """
    @brief Try to infer reach index from filename by extracting first integer.
    @return int reach index or None if not found.
    """
    m = re.search(r"(\d+)", path.stem)
    return int(m.group(1)) if m else None


def build_external_inputs_from_csv(
    system,
    csv_path: Path,
    default_sigma_g: float = 1.6,
    grain_unit: str = "mm",
) -> np.ndarray:
    """
    @brief Build external_inputs array from a CSV with D-quantiles per reach/time.
    @param system SedimentarySystem-like object with attributes: timescale, n_reaches, n_classes, psi, ts_length
    @param csv_path Path to CSV
    @param default_sigma_g Fallback geometric std dev if only D50 is given
    @param grain_unit 'mm' or 'm' (D-values in the CSV)
    @return external_inputs (timescale, n_reaches, n_classes), volumes in m3 per time step
    """
    df = pd.read_csv(Path(csv_path))
    required_cols = {"time_idx", "D50"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {sorted(required_cols)}")
    if ("volume_m3" not in df.columns) and ("flux_m3_per_s" not in df.columns):
        raise ValueError("CSV must contain either 'volume_m3' or 'flux_m3_per_s'")

    ext = np.zeros((system.timescale, system.n_reaches, system.n_classes), dtype=float)
    psi = np.array(system.psi, dtype=float)
    unit_scale = _unit_scale(grain_unit)

    # If reach_idx missing in file, attempt to infer from filename and use for all rows
    default_reach_idx = None if ("reach_idx" in df.columns) else _infer_reach_index_from_filename(Path(csv_path))

    for _, row in df.iterrows():
        t = int(row["time_idx"])
        r = int(row["reach_idx"]) if ("reach_idx" in df.columns) else (default_reach_idx if default_reach_idx is not None else None)
        if r is None:
            raise ValueError("reach_idx missing in CSV row and could not be inferred from filename")
        if not (0 <= t < system.timescale):
            raise IndexError(f"time_idx {t} out of bounds [0,{system.timescale})")
        if not (0 <= r < system.n_reaches):
            raise IndexError(f"reach_idx {r} out of bounds [0,{system.n_reaches})")

        # Convert D-columns to mm and fit GSD
        row_mm = row.copy()
        for col in ["D16", "D25", "D35", "D50", "D65", "D75", "D84"]:
            if col in row_mm and pd.notna(row_mm[col]):
                row_mm[col] = float(row_mm[col]) * unit_scale
        mu, sigma_ln = _fit_lognormal_mu_sigma_ln(row_mm, default_sigma_g)
        fracs = _fractions_from_lognormal(psi, mu, sigma_ln)

        # Volume per time step
        vol_val = row.get("volume_m3")
        flux_val = row.get("flux_m3_per_s")
        if pd.notna(vol_val):
            vol_t = float(vol_val)
        elif pd.notna(flux_val):
            vol_t = float(flux_val) * float(system.ts_length)
        else:
            raise ValueError("Row must contain either volume_m3 or flux_m3_per_s")
        vol_t = max(vol_t, 0.0)
        ext[t, r, :] += vol_t * fracs

    return ext


def build_external_inputs_from_dir(
    system,
    dir_path: Path,
    default_sigma_g: float = 1.6,
    grain_unit: str = "mm",
) -> np.ndarray:
    """
    @brief Build external_inputs by aggregating multiple per-reach CSVs in a directory.
    @param dir_path Path to directory containing .csv files; each file represents one reach.
    @details If a file lacks 'reach_idx' column, the reach index is inferred from filename.
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    files = sorted(dir_path.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in directory: {dir_path}")

    ext_total = np.zeros((system.timescale, system.n_reaches, system.n_classes), dtype=float)
    for fp in files:
        ext = build_external_inputs_from_csv(system, fp, default_sigma_g=default_sigma_g, grain_unit=grain_unit)
        ext_total += ext
    return ext_total


def set_external_input_from_csv(
    system,
    csv_path: Path,
    force_pass_external_inputs: bool = False,
    roundpar: int = 3,
    default_sigma_g: float = 1.6,
    grain_unit: str = "mm",
):
    """
    @brief Convenience wrapper: build external inputs from a single CSV and set them on the system.
    """
    external_inputs = build_external_inputs_from_csv(system, csv_path, default_sigma_g=default_sigma_g, grain_unit=grain_unit)
    system.set_external_input(external_inputs, force_pass_external_inputs=force_pass_external_inputs, roundpar=roundpar)


def set_external_input_from_dir(
    system,
    dir_path: Path,
    force_pass_external_inputs: bool = False,
    roundpar: int = 3,
    default_sigma_g: float = 1.6,
    grain_unit: str = "mm",
):
    """
    @brief Convenience wrapper: build external inputs from a directory of CSVs and set them on the system.
    """
    external_inputs = build_external_inputs_from_dir(system, dir_path, default_sigma_g=default_sigma_g, grain_unit=grain_unit)
    system.set_external_input(external_inputs, force_pass_external_inputs=force_pass_external_inputs, roundpar=roundpar)
