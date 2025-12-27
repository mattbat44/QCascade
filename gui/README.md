# D-CASCADE GUI

This is a modern, dockable GUI for the D-CASCADE sediment transport model.

## Installation

1.  Ensure you have Python 3.9+ installed.
2.  Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

    *Note: Installing `geopandas` on Windows can sometimes be tricky. It is recommended to use `conda` or install binary wheels (GDAL, Fiona, Shapely) manually if pip fails.*

## Running the GUI

Run the `main.py` script from the `gui` directory:

```bash
python main.py
```

## Features

*   **Dockable Interface:** Rearrange panels (Map, Configuration, Plots) to suit your workflow.
*   **GIS Viewer:** Interactive map to view River Network shapefiles.
*   **Configuration:** User-friendly forms for all model parameters with validation.
*   **Real-time Logs:** View simulation progress and output.
*   **Results:** (Planned) Interactive plotting of simulation results.

## Project Structure

*   `main.py`: Entry point.
*   `windows/`: Main window and layout logic.
*   `widgets/`: Individual UI components (Map, Docks, Plots).
*   `core/`: Non-UI logic (Config management, Threading).
