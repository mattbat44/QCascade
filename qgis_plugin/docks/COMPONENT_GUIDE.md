# Dock Panel Components - Developer Guide

## Overview

The dock panel UI components have been refactored into modular, reusable components to improve maintainability and reduce file complexity.

## Directory Structure

```
qgis_plugin/docks/
├── parameters_dock.py          # Main Parameters Dock coordinator (105 lines)
├── results_viewer_dock.py      # Main Results Viewer Dock coordinator (1008 lines)
├── parameters/                 # Parameters Dock components
│   ├── __init__.py
│   ├── inputs_tab.py          # Inputs tab with layer selector
│   ├── physics_tab.py         # Physics parameters
│   ├── sediment_tab.py        # Sediment parameters
│   ├── time_tab.py            # Time parameters
│   ├── options_tab.py         # Options
│   └── external_inputs_tab.py # External inputs management
└── results_viewer/             # Results Viewer Dock components
    ├── __init__.py
    ├── time_series_tab.py     # Time series visualization
    ├── spatial_tab.py         # Spatial analysis
    ├── connectivity_tab.py    # Connectivity/heatmap
    ├── long_profile_tab.py    # Long profile visualization
    ├── animation_tab.py       # Animation controls
    └── stats_tab.py           # Statistics summary
```

## Architecture

### Main Dock Files

The main dock files (`parameters_dock.py` and `results_viewer_dock.py`) act as coordinators that:
- Create and manage tab component instances
- Connect signals from components to the main dock's signals
- Expose widget references for backward compatibility
- Handle overall dock behavior and lifecycle

### Component Files

Each component file contains a single `QWidget` subclass that represents one tab of the dock. Components are:
- **Self-contained**: All UI initialization is within the component
- **Reusable**: Can be instantiated independently if needed
- **Testable**: Can be tested in isolation
- **Focused**: Each handles a specific aspect of functionality

## Using the Components

### Importing Components

```python
# Import individual components
from qgis_plugin.docks.parameters.inputs_tab import InputsTab
from qgis_plugin.docks.results_viewer.time_series_tab import TimeSeriesTab

# Or import from the package
from qgis_plugin.docks.parameters import InputsTab, PhysicsTab
from qgis_plugin.docks.results_viewer import TimeSeriesTab, SpatialTab
```

### Creating a Component Instance

```python
# Create a tab component
inputs_tab = InputsTab(parent=self)

# Access widgets
inputs_tab.layer_combo  # Access the layer combo box
inputs_tab.csv_path     # Access the CSV path line edit

# Connect signals
inputs_tab.layer_selected.connect(self.on_layer_selected)
```

### Accessing Components from Main Dock

```python
# Create the main dock
params_dock = ParametersDock()

# Access tab components
params_dock.inputs_tab        # Access the entire inputs tab
params_dock.physics_tab       # Access the physics tab

# Access widgets (backward compatibility)
params_dock.layer_combo       # Same as params_dock.inputs_tab.layer_combo
params_dock.tr_cap           # Same as params_dock.physics_tab.tr_cap
```

## Adding New Components

To add a new tab component:

1. **Create the component file** in the appropriate directory:
   ```python
   # docks/parameters/my_new_tab.py
   from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout
   
   class MyNewTab(QWidget):
       def __init__(self, parent=None):
           super().__init__(parent)
           self.init_ui()
       
       def init_ui(self):
           layout = QVBoxLayout(self)
           # Add your widgets here
   ```

2. **Update the package `__init__.py`**:
   ```python
   from .my_new_tab import MyNewTab
   __all__ = [..., 'MyNewTab']
   ```

3. **Add to the main dock**:
   ```python
   # In ParametersDock.__init__()
   self.my_new_tab = MyNewTab(self)
   self.tabs.addTab(self.my_new_tab, "My New Tab")
   ```

## Backward Compatibility

All widget references that were previously accessed from the main dock are still available for backward compatibility:

```python
# Old code (still works)
dock.layer_combo.currentLayer()

# New code (also works, more explicit)
dock.inputs_tab.layer_combo.currentLayer()
```

This ensures that existing code using the docks continues to work without modification.

## Signal Handling

Components define their own signals which are connected to the main dock's signals:

```python
# In component
class InputsTab(QWidget):
    layer_selected = pyqtSignal(object)
    
# In main dock __init__
self.inputs_tab.layer_selected.connect(self.layer_selected.emit)
```

External code connects to the main dock's signals as before:

```python
# External code remains unchanged
params_dock.layer_selected.connect(my_handler)
```

## Testing

Components can be tested individually:

```python
def test_inputs_tab():
    from qgis.PyQt.QtWidgets import QApplication
    from qgis_plugin.docks.parameters.inputs_tab import InputsTab
    
    app = QApplication([])
    tab = InputsTab()
    
    # Test the component
    assert tab.output_name.text() == "simulation_output"
    
    # Test signals
    received = []
    tab.layer_selected.connect(lambda x: received.append(x))
    # Trigger signal...
```

## Benefits of the Refactoring

1. **Maintainability**: Easier to find and modify specific functionality
2. **Readability**: Smaller files are easier to understand
3. **Reusability**: Components can be used independently
4. **Testability**: Individual components can be tested in isolation
5. **Scalability**: Easy to add new tabs without bloating main files
6. **Collaboration**: Multiple developers can work on different components

## Migration Notes

No migration is required for existing code. The refactoring maintains 100% backward compatibility with:
- All widget references
- All signal connections
- All method calls
- All behavior

The changes are purely internal to improve code organization.
