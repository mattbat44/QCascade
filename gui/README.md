# D-CASCADE GUI

This is a modern, feature-rich GUI for the D-CASCADE sediment transport model.

## Features

### 🗺️ Interactive Map Viewer
- Load and visualize river network shapefiles
- Interactive reach selection and highlighting
- Edit reach attributes (name, length, slope, width, D50, etc.)
- Custom reach naming with persistent storage
- Tooltips showing reach information on hover

### 📊 Discharge Data Management
- View discharge time series in table format
- Create new discharge datasets
- Edit discharge values interactively
- Plot discharge time series for individual reaches or all reaches
- Import/export CSV files

### 📈 Advanced Results Visualization
- **Time Series Plots:** View sediment transport variables over time
  - Volume out/in
  - Transport capacity
  - Sediment budget
  - D50 of active layer and transported sediment
- **Spatial Analysis:** Aggregate results along reaches
  - Mean, median, sum, max, min aggregation
  - Colorful bar charts
- **Dynamic Viewer:** Animate through time steps
  - Interactive time slider
  - Play/pause animation controls
  - Real-time visualization updates
- **Statistics:** Summary statistics for all result variables

### ⚙️ Model Configuration
- User-friendly forms for all model parameters
- Organized into logical tabs:
  - Input Files (shapefiles, discharge, outputs)
  - Physics Parameters (transport formulas, flow calculations)
  - Sediment Properties (grain size classes, active layer)
  - Time Settings (timescale, time step length)
  - Options (deposit layer saving, rounding)
- Tooltips and validation for all inputs

### 🎨 Modern User Interface
- Clean, professional design with custom stylesheet
- Dockable panels - arrange to suit your workflow
- Keyboard shortcuts for common actions
- Persistent window layout and settings
- Status bar with real-time feedback
- Integrated help and documentation

## Installation

1.  Ensure you have Python 3.9+ installed.
2.  Install the required dependencies:

    ```bash
    cd /path/to/dcascade-py-2.0.0
    pip install -r pyproject.toml
    # or using uv:
    uv sync
    ```

    Key dependencies:
    - PyQt6 (GUI framework)
    - PyQt6-WebEngine (for map and plot rendering)
    - geopandas (spatial data handling)
    - folium (interactive maps)
    - plotly (interactive plots)
    - pandas, numpy (data processing)

## Running the GUI

From the project root directory:

```bash
python gui/main.py
```

Or from the `gui` directory:

```bash
cd gui
python main.py
```

## Quick Start Guide

### 1. Load Your Data
1. Click on the **"Input Files"** tab in the left panel
2. Click **"Browse..."** next to "River Network (.shp)" and select your shapefile
3. Click **"Browse..."** next to "Discharge (.csv)" and select your discharge data
4. Set an output name for your simulation

### 2. Configure the Model
Navigate through the configuration tabs to set your model parameters:
- **Physics Parameters:** Choose transport capacity formula (default: Wilcock-Crowe)
- **Sediment:** Set grain size range, number of classes, layer thicknesses
- **Time:** Set total simulation time and time step length
- **Options:** Configure output saving options

### 3. Review Your Setup
- Switch to the **"GIS Viewer"** tab to see your river network on the map
- Click on reaches to see their attributes
- Use **"Edit Selected Reach"** to modify reach properties or add names
- Switch to **"Discharge Data Editor"** to review discharge time series

### 4. Run the Simulation
- Click **"▶ Run Simulation"** in the toolbar (or press Ctrl+R)
- Monitor progress in the "Simulation Logs" panel at the bottom
- The simulation runs in a background thread, so the GUI remains responsive

### 5. Analyze Results
- After completion, results are automatically loaded into the **"Results Analysis"** tab
- Choose from multiple visualization types:
  - **Time Series:** Plot variables over time for selected reaches
  - **Spatial Analysis:** See spatial patterns along the river network
  - **Dynamic Viewer:** Animate through time steps with the slider
  - **Statistics:** Review summary statistics

## Keyboard Shortcuts

- **Ctrl+R:** Run simulation
- **Ctrl+L:** Load results from file
- **Ctrl+S:** Save all changes (shapefile, discharge data)
- **Ctrl+Q:** Quit application
- **F1:** Show help dialog

## Tips and Tricks

### Customizing the Layout
- Drag dock panels to rearrange them
- Dock panels can be tabbed together or floated as separate windows
- Your layout is automatically saved and restored when you reopen the GUI

### Editing Reach Attributes
1. Click on a reach in the map to select it (it will turn red)
2. Click **"Edit Selected Reach"** in the map toolbar
3. The editor dialog has tabs for different attribute groups
4. Give reaches custom names to identify them easily
5. Click **"Save Changes"** when done

### Working with Discharge Data
- The discharge editor shows data in a spreadsheet-like table
- Use **"Show Rows"** to limit the number of displayed rows for performance
- Click **"Plot Time Series"** to visualize discharge patterns
- Select specific reaches from the dropdown to focus on them
- Create new datasets with **"New Dataset"** for testing

### Viewing Results
- Load results from any simulation with **"Load Results (.p)"**
- Use the tabs to switch between different visualization types
- For time series, toggle **"Show all reaches"** to compare multiple reaches
- In the dynamic viewer, use the play button to animate through time
- Export plots for use in reports or publications

## Architecture

The GUI is organized into modules:

- **`main.py`:** Application entry point
- **`windows/`:** Main window and layout
  - `main_window.py`: Main application window with all docks and toolbars
- **`widgets/`:** Individual UI components
  - `map_widget.py`: Interactive GIS map viewer
  - `discharge_editor.py`: Discharge data table and plots
  - `results_viewer.py`: Multi-tab results visualization
  - `reach_editor_dialog.py`: Reach attribute editor
  - `config_docks.py`: Configuration input forms
  - `plot_widget.py`: Legacy plot widget
- **`core/`:** Non-UI logic
  - `config_manager.py`: Configuration data models (Pydantic)
  - `runner_thread.py`: Background simulation runner
- **`styles/`:** Visual themes
  - `theme.py`: Custom stylesheet

## Troubleshooting

### "No module named PyQt6"
Install PyQt6: `pip install PyQt6 PyQt6-WebEngine`

### Map not displaying
Ensure you have internet connection (map tiles are loaded from OpenStreetMap)

### Shapefile won't load
- Check that the shapefile has the required attributes: FromN, ToN, Length, Slope, W, D50
- Verify the shapefile is in a valid coordinate reference system

### Results not loading after simulation
- Check the "Simulation Logs" panel for errors
- Verify the output directory and name in the configuration
- Manually load results with Ctrl+L and browse to the .p file

## Contributing

Contributions are welcome! Areas for improvement:
- Additional visualization types (3D plots, connectivity maps in GUI)
- Export functionality for plots and data
- Batch simulation support
- Real-time progress indicators
- More advanced GIS editing tools

## License

See the main project repository for license information.
