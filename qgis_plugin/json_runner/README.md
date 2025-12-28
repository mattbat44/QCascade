# JSON Runner for D-CASCADE

This directory contains scripts to run D-CASCADE simulations using a JSON configuration file, making it easier to manage parameters and automate runs.

## Files

- `run_dcascade_json.py`: The main wrapper script. Reads a JSON config, prepares inputs, and runs the simulation.
- `validate_config.py`: A validation script that checks your JSON configuration against the expected schema and value ranges.
- `example_config.json`: An example configuration file based on the Vjosa river case study.

## Usage

1.  **Create a Configuration File**:
    Copy `example_config.json` and modify it for your simulation.

2.  **Validate Configuration** (Optional but recommended):
    ```bash
    python validate_config.py your_config.json
    ```
    This will check for missing fields, invalid types, and out-of-range values.

3.  **Run Simulation**:
    ```bash
    python run_dcascade_json.py your_config.json
    ```

## Configuration Structure

The JSON file is divided into sections:
- `paths`: Input/output file paths.
- `sediment`: Sediment properties (range, classes, layers).
- `time`: Simulation duration and time step.
- `physics`: Model physics options (transport formulas, flow depth, etc.).
- `options`: Output and execution options.
- `external_inputs` (optional): Define lateral sediment sources via simple CSVs.

### External Inputs Section

You can provide external inputs in two ways:

- `dir`: A directory containing per‑reach CSV files (one file per reach). If a CSV lacks a `reach_idx` column, the reach index is inferred from its filename by the first integer (e.g., `reach_3.csv` → reach 3).
- `csv_files`: A list of CSV files to aggregate. Each file may contain multiple rows across times and reaches.
- `tensor_npy`: A precomputed `.npy` tensor with shape `(timescale, n_reaches, n_classes)`; can be produced by the generator tool below.

Optional fields:
- `grain_unit`: `'mm'` (default) or `'m'` for the D‑quantile units.
- `default_sigma_g`: Fallback geometric std dev (default `1.6`) when only `D50` is provided.

CSV schema (columns):
- Required: `time_idx`, `D50`, and either `volume_m3` or `flux_m3_per_s`
- Optional: `reach_idx` (omit when using per‑reach files and filename inference)
- Optional quantile pairs to constrain spread: `D16/D84` or `D25/D75` or `D35/D65`

Example `external_inputs` in config:

```json
{
    "external_inputs": {
        "dir": "../inputs/external_inputs_example/",
        "grain_unit": "mm",
        "default_sigma_g": 1.6
    }
}
```

### Generate a Reusable Tensor

Use the helper to generate and save a `.npy` external_inputs tensor:

```bash
uv run python json_runner/generate_external_inputs.py path/to/config.json --dir path/to/ext_dir 
# Or combine multiple files
uv run python json_runner/generate_external_inputs.py path/to/config.json --csv path/to/a.csv --csv path/to/b.csv --out external_inputs.npy
```

Then reference it in your config:

```json
{
    "external_inputs": {
        "tensor_npy": "external_inputs.npy"
    }
}
```

See `validate_config.py` or run `python validate_config.py` (without arguments) for a full description of allowed values.
