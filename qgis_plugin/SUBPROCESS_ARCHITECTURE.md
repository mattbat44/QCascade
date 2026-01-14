# D-CASCADE QGIS Plugin - Subprocess Runner Architecture

## Overview

The QGIS plugin now runs D-CASCADE simulations in a **separate Python subprocess** using the uv-managed environment. This architecture provides:

- **Dependency Isolation**: QGIS's Python environment (with numpy 2.x) doesn't interfere with D-CASCADE's requirements (numpy 1.x compatible code)
- **Clean Separation**: QGIS acts purely as a GUI/interface layer
- **Stability**: Simulation crashes don't crash QGIS
- **Proper Logging**: Real-time output streaming to the QGIS log panel

## How It Works

1. **User triggers simulation** in QGIS plugin
2. **Runner thread** (`runner_thread.py`) spawns a subprocess
3. **Subprocess** uses the Python from `.venv` (managed by uv) to run `run_dcascade_json.py`
4. **Output streams** back to QGIS log panel in real-time
5. **Results** are saved to files, which QGIS then loads for visualization

## Setup

### 1. Initialize uv Environment

```powershell
# From project root
uv sync
```

This creates `.venv/` with all dependencies from `pyproject.toml` (numpy 2.x, etc.)

### 2. Install QGIS Plugin

```powershell
.\install_plugin_dev.ps1
```

This creates a junction from QGIS plugins directory to `qgis_plugin/`.

### 3. Restart QGIS

The plugin will automatically find and use the `.venv/Scripts/python.exe` for running simulations.

## File Structure

```
qgis_plugin/
├── core/
│   └── runner_thread.py     # Spawns subprocess with uv Python
├── json_runner/
│   └── run_dcascade_json.py # CLI entry point (runs in subprocess)
└── src/                      # D-CASCADE core (runs in subprocess)
```

## Python Environment Detection

The runner thread looks for Python in this order:

1. `.venv/Scripts/python.exe` (Windows uv environment)
2. `.venv/bin/python` (Linux/Mac uv environment)
3. Fallback to `sys.executable` (QGIS Python - not recommended)

## Debugging

### Check which Python is being used

Look at the QGIS log panel when starting a simulation:
```
Using Python: C:\...\dcascade-py-2.0.0\.venv\Scripts\python.exe
```

### Test the subprocess manually

```powershell
.\.venv\Scripts\python.exe qgis_plugin\json_runner\run_dcascade_json.py inputs\input_trial\config.json
```

### Check uv environment packages

```powershell
uv pip list
```

Should show numpy, pandas, geopandas, networkx, etc. matching `pyproject.toml`.

## Benefits of This Approach

✅ **No need to modify QGIS's Python** - QGIS can keep numpy 2.x  
✅ **Exact dependency matching** - Uses same environment as standalone scripts  
✅ **Easy testing** - Can run simulations outside QGIS for debugging  
✅ **Version control friendly** - All deps defined in `pyproject.toml`  
✅ **No PATH pollution** - Each component uses its own Python  

## Troubleshooting

### "Could not find python.exe in .venv"

Run `uv sync` from project root to create the virtual environment.

### "Module not found" errors in subprocess

The subprocess runs from project root and adds `qgis_plugin/src` to path automatically. Check that all imports are correct in `run_dcascade_json.py`.

### Simulation works in CLI but not in QGIS

- Check QGIS log panel for the actual command being run
- Copy/paste that command into a terminal to see full error output
- Verify config paths are absolute or relative to config file location
