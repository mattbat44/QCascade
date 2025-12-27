# D-CASCADE AI Coding Instructions

## Project Overview
D-CASCADE (Dynamic CAtchment Sediment Connectivity And Delivery) is a Python-based modeling framework for sediment transport and connectivity analysis in large river networks. It simulates sediment transfer through river reaches over time.

## Architecture & Core Components

### Directory Structure
- `src/`: Core library code.
- `user_scripts/`: Entry points for running simulations (e.g., `00-DCASCADE_user_script_example_Vjosa.py`).
- `inputs/`: Input data (Shapefiles, CSVs, MAT files).
- `post_process_examples/`: Scripts for analyzing output pickle files.
- `unit_tests/`: Test suite.

### Key Classes (`src/`)
- **`DCASCADE`** (`dcascade.py`): The main solver class. Contains the `run()` method which executes the time-loop simulation.
- **`SedimentarySystem`** (`sedimentary_system.py`): Represents the state of the river network, including sediment matrices (`Qbi_dep`, `Qbi_tr`), network topology, and reach data.
- **`ReachData`** (`reach_data.py`): Stores static attributes of river reaches (slope, width, grain sizes) loaded from input files.
- **`Cascade`** (`cascade.py`): Represents a volume of sediment moving through the network during a time step.
- **`DCASCADE_main`** (`main.py`): High-level wrapper function to initialize the system and start the simulation.

## Data Flow
1.  **Input:** User scripts load Shapefiles/CSVs into `ReachData` and `SedimentarySystem`.
2.  **Simulation:** `DCASCADE.run()` iterates through time steps (`timescale`).
    - Calculates hydraulic parameters (width, flow depth, velocity).
    - Computes transport capacity.
    - Moves sediment volumes (`Cascade` objects) between reaches.
3.  **Output:** Results are saved as pickle files (`.p`) in a `cascade_results/` directory.

## Developer Workflows

### Running Simulations
- Execute scripts in `user_scripts/`.
- **Crucial Pattern:** Scripts must add `src/` to `sys.path` to import modules:
  ```python
  import sys
  import os
  sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
  ```

### Testing
- **CRITICAL:** Any code changes MUST pass all existing tests. Run `pytest` to verify before finalizing changes.
- Tests are located in `unit_tests/`.
- Run tests using `pytest`.

### Environment
- Dependencies are managed via `uv` using `pyproject.toml`.
- Key libraries: `numpy`, `pandas`, `networkx`, `geopandas`, `shapely`, `tqdm`.

## Coding Conventions
- **Docstrings:** Use Doxygen-style docstrings (`@brief`, `@param`, `@author`).
- **Paths:** Use `pathlib.Path` for file manipulation.
- **Numerical Computing:** Heavy reliance on `numpy` for matrix operations and `pandas` for data handling.
- **Error Handling:** `numpy.seterr(divide='ignore', invalid='ignore')` is often used to handle division by zero in hydraulic calculations.

## Specific Implementation Details
- **Sediment Classes:** Defined by `psi` (Krumbein phi scale).
- **Transport Formulas:** Selected via indices (e.g., `indx_tr_cap`, `indx_tr_partition`) passed to the solver.
- **Network Topology:** Defined by `FromN` (upstream node) and `ToN` (downstream node) columns in the input dataframe.


