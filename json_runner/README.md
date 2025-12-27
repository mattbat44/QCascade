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

See `validate_config.py` or run `python validate_config.py` (without arguments) for a full description of allowed values.
