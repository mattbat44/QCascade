# Q-Cascade QGIS Plugin

Q-Cascade is the QGIS plugin for the D-CASCADE sediment transport modeling framework.

## Scope and Purpose

This repository provides a QGIS-based interface and workflow for running D-CASCADE and viewing results in a simple user environment.

Important: this codebase does not modify the core scientific D-CASCADE model logic developed by the original teams. It is an integration and usability layer (setup, configuration, execution, and visualization) around that existing model work.

## Model Code

The core D-CASCADE model files are **not stored in this repository**.  They are
downloaded verbatim from the official upstream release when you install the
plugin:

- **Upstream repository**: <https://github.com/dcascade-py/dcascade-py>
- **Release used**: [v2.0.0](https://github.com/dcascade-py/dcascade-py/releases/tag/v2.0.0)

The fetch script `fetch_dcascade_model.py` (in the project root) downloads
those files into `qgis_plugin/src/`.

Install scripts call this fetch automatically:
- `install.bat` (basic user install)
- `install_dev.bat` (development install)

If the files are already present and unchanged, re-running the installer keeps
the same files in place.

If you need to refresh the model files manually (e.g. after a clean clone):

```bash
python fetch_dcascade_model.py
```

## Academic Credit and Citation

Please credit the original D-CASCADE model creators and the Python implementation team when using this plugin in research outputs.

- Original D-CASCADE model (MATLAB):
   - Repository: https://github.com/mtangi/DCASCADEmodel
   - Paper: https://doi.org/10.1029/2021WR030784

- D-CASCADE Python implementation used by this repository:
   - Repository: https://github.com/dcascade-py/dcascade-py
   - Paper: Doolaeghe et al. (in prep)

This plugin repository does not alter those underlying model formulations; it provides a practical environment to run simulations and inspect outputs.

## Quick Start

1. Install the plugin (recommended: Basic Installation below).
2. Enable Q-Cascade in QGIS.
3. Load a valid river network layer and discharge input.
4. Configure parameters in the Parameters dock.
5. Run simulation and inspect outputs in the Results Viewer.

## Installation

### Basic Installation (Recommended for most users)

This is a one-click installer for non-developers.

1. Close QGIS if it is running.
2. In this project folder, double-click `install.bat`.
3. Wait for completion.
4. Start QGIS.
5. Go to **Plugins -> Manage and Install Plugins** and enable **Q-Cascade**.

The installer automatically:
- Copies the plugin to the default QGIS profile.
- Installs required Python dependencies into QGIS Python.
- Fetches the upstream D-CASCADE model files into `qgis_plugin/src/`.

### Development Installation

For development and testing, use the one-command installer:

1. **Create QGIS Profile** (if not already created):
   - Open QGIS
   - Go to **Settings → User Profiles → New Profile**
   - Name it `dcascade-testing`

2. **Run Installation Script**:
   ```powershell
   .\install_dev.bat
   ```
   
   This script does all setup in one pass:
   - Creates/refreshes a junction from the testing profile plugin folder to `qgis_plugin/`
   - Installs dependencies into detected QGIS Python
   - Fetches upstream model files into `qgis_plugin/src/`

3. **For a plain Python / uv workflow** (no QGIS yet):
   ```bash
   uv sync
   python fetch_dcascade_model.py
   pytest qgis_plugin/unit_tests/
   ```

4. **Open QGIS with the profile**:
   - Start QGIS and select the `dcascade-testing` profile
   - Or use: `qgis --profile dcascade-testing`

5. **Enable the plugin**:
   - Go to **Plugins → Manage and Install Plugins**
   - Search for "D-CASCADE"
   - Check the box to enable it

6. **For rapid development**:
   - Install the "Plugin Reloader" plugin (optional but recommended)
   - After code changes, use **Plugins → Plugin Reloader → Reload Plugin** to reload without restarting QGIS

### Production Installation

1. Copy the `qgis_plugin` directory to your QGIS plugins folder:
   - Windows: `C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

2. Rename the directory from `qgis_plugin` to `dcascade`

3. Restart QGIS

4. Enable the plugin:
   - Go to **Plugins → Manage and Install Plugins**
   - Search for "D-CASCADE"
   - Check the box to enable it

5. Access the plugin:
   - Click the D-CASCADE toolbar icon, or
   - Go to **Plugins → D-CASCADE**

## Usage

### Setup

1. **Load Network Layer**: 
   - Load your river network shapefile into QGIS as a vector layer
   - Ensure it has required fields: `FromN`, `ToN`, `Length`, `Slope`, `W`, `D50`, `D90`
   - Select the layer in the **Parameters** dock (right side) using the layer dropdown

2. **Configure Parameters**:
   - Use the tabs in the Parameters dock to set:
     - **Inputs**: Layer selection, discharge CSV, output settings
     - **Physics**: Transport formulas, flow depth, velocity calculations
     - **Sediment**: Grain size range, number of classes, layer thicknesses
     - **Time**: Number of time steps and step length
     - **Options**: Output saving options
     - **External Inputs**: Add CSV files for per-reach external sediment inputs

3. **Run Simulation**:
   - Click **Run Simulation** button
   - Monitor progress in QGIS message log
   - Results will be automatically loaded when complete

### Viewing Results

1. **Results Viewer** (bottom dock):
   - **Time Series**: Graph variables over time for selected or all reaches
   - **Spatial Analysis**: View aggregated results along reaches
   - **Dynamic Viewer**: Animate through time steps
   - **Statistics**: Summary statistics for all variables

2. **Map Interaction**:
   - Select a reach in the map canvas to graph it in the results viewer
   - Use the time slider in Dynamic Viewer to animate layer symbology
   - Layer colors update based on selected variable and time step

3. **External Inputs**:
   - Select a reach in the map
   - Go to **External Inputs** tab in Parameters dock
   - Click "Add External Input CSV" to attach CSV files to the selected reach

## Requirements

- QGIS 3.0 or later
- Python packages (should be available in QGIS Python environment):
  - numpy
  - pandas
  - geopandas
  - matplotlib
  - scipy
  - shapely
  - networkx

## Architecture

- **Main Plugin Class** (`dcascade_plugin.py`): Integrates with QGIS, manages docks and interactions
- **Parameters Dock** (`docks/parameters_dock.py`): Configuration interface with tabs
- **Results Viewer Dock** (`docks/results_viewer_dock.py`): Visualization with matplotlib
- **Core Module** (`core/`): Configuration management and simulation runner

## Troubleshooting

### Plugin not appearing in QGIS
- Check that the plugin directory is in the correct location
- Ensure `__init__.py` and `metadata.txt` are present
- Check QGIS Python console for error messages

### Layer validation fails
- Ensure your vector layer has required fields: `FromN`, `ToN`, `Length`, `Slope`
- Check field names match exactly (case-sensitive)

### Simulation fails
- Check that discharge CSV file path is correct
- Verify layer has valid geometry
- Check QGIS message log for detailed error messages

### Symbology animation not working
- Ensure results are loaded in Results Viewer
- Select a variable in Dynamic Viewer tab
- Move the time slider to see updates

