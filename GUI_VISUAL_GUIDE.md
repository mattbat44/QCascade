# D-CASCADE GUI Visual Guide

## Overview

The enhanced D-CASCADE GUI provides a modern, professional interface for sediment transport modeling. This guide describes the visual layout and features you'll see when using the application.

## Main Window Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│ File  Edit  View  Help                                    [▶ Run] [📊] │  <- Toolbar
├────────────────┬────────────────────────────────────────────────────────┤
│                │                                                        │
│  Configuration │                  Main Workspace                       │
│     Panels     │                                                        │
│                │  - GIS Viewer (Interactive Map)                       │
│  [Input Files] │  - Discharge Data Editor                              │
│  [Physics]     │  - Results Analysis                                   │
│  [Sediment]    │                                                        │
│  [Time]        │  Tabbed interface - click tabs to switch views       │
│  [Options]     │                                                        │
│                │                                                        │
│  (Tabbed)      │                                                        │
│                │                                                        │
├────────────────┴────────────────────────────────────────────────────────┤
│ Simulation Logs                                                         │
│ > Configuration saved to temp_config.json                               │
│ > Starting simulation...                                                │
│ > Time step 1/100 completed                                             │
└─────────────────────────────────────────────────────────────────────────┘
│ Ready | Last action: Simulation completed                              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Configuration Panels (Left Side)

### Input Files Tab
- **River Network (.shp)**: [____________] [Browse...]
- **Discharge (.csv)**: [____________] [Browse...]
- **Output Name**: [simulation_output]
- **Output Directory**: [____________] [Browse...]

*Color Scheme*: White input boxes with blue borders on focus

### Physics Parameters Tab
- **Transport Capacity**: [Dropdown: Wilcock-Crowe ▼]
- **Transport Partitioning**: [Dropdown: Shear stress correction ▼]
- **Update Slope**: ☑ checkbox

*Color Scheme*: Organized form layout with labeled fields

### Sediment Tab
- **Grain Size Range**: [Min: -5.0] to [Max: 2.0] (phi units)
- **Number of Classes**: [10]
- **Deposit Layer Thickness**: [0.1] m
- **Active Layer Depth**: [0.5] m

### Time Tab
- **Timescale**: [365] days
- **Time Step Length**: [1.0] days

### Options Tab
- **Save Deposit Layer**: [never ▼]
- **Round Parameter**: [0]
- **Force Pass External Inputs**: ☐

## Main Workspace (Right Side)

### 1. GIS Viewer Tab

```
┌────────────────────────────────────────────────────────┐
│ [Edit Selected Reach] [Save Changes] [Refresh Map]    │
├────────────────────────────────────────────────────────┤
│                                                        │
│               Interactive Folium Map                   │
│                                                        │
│    River network displayed in BLUE                    │
│    Selected reach highlighted in RED                  │
│    Hover for reach information                        │
│                                                        │
│    Custom reach names shown as labels:                │
│    "Main Channel"  "Tributary A"                      │
│                                                        │
│    OpenStreetMap basemap                              │
│    Zoom controls: [+] [-]                             │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Features Visible**:
- Blue river lines (default)
- Red highlight when selected
- Yellow on hover
- Black text labels for named reaches
- Map controls in top-right corner

### 2. Discharge Data Editor Tab

```
┌────────────────────────────────────────────────────────┐
│ [Load CSV] [Save CSV] [New Dataset] [Plot Time Series]│
├────────────────────────────────────────────────────────┤
│ View Reach: [All Reaches ▼]  Show Rows: [100 ▼]      │
├────────────────────────────────────────────────────────┤
│ Data Shape: 365 time steps × 10 reaches               │
├────────────────────────────────────────────────────────┤
│       Reach 1  Reach 2  Reach 3  Reach 4  ...        │
│ T1      10.5     12.3     8.7      9.2    ...        │
│ T2      11.2     13.1     9.0      9.5    ...        │
│ T3      10.8     12.7     8.9      9.3    ...        │
│ ...      ...      ...     ...      ...    ...        │
│                                                        │
│ (Scrollable table with alternating row colors)        │
├────────────────────────────────────────────────────────┤
│              Discharge Time Series Plot               │
│                                                        │
│  Interactive Plotly chart                             │
│  - Hover for values                                   │
│  - Zoom and pan                                       │
│  - Multiple traces                                    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Color Scheme**:
- White table with light gray alternating rows
- Blue selection highlighting
- Teal/blue line plots

### 3. Results Analysis Tab

#### Time Series Sub-tab
```
┌────────────────────────────────────────────────────────┐
│ Variable: [Volume out [m^3] ▼]                        │
│ Reach: [Reach 1 ▼]                                    │
│ ☐ Show all reaches                                    │
│ [Generate Plot]                                        │
├────────────────────────────────────────────────────────┤
│                                                        │
│        Volume out [m^3] - Time Series                 │
│                                                        │
│   Interactive line plot:                              │
│   - X-axis: Time Step (0-365)                         │
│   - Y-axis: Volume (m³)                               │
│   - Blue line with markers                            │
│   - Hover tooltips                                    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### Spatial Analysis Sub-tab
```
┌────────────────────────────────────────────────────────┐
│ Variable: [Sediment budget [m^3] ▼]                   │
│ Aggregation: [Mean ▼]                                 │
│ Year: [0 (all) ▼]                                     │
│ [Generate Spatial Plot]                               │
├────────────────────────────────────────────────────────┤
│                                                        │
│    Mean Sediment budget [m^3] - Along Reaches         │
│                                                        │
│   Colorful bar chart:                                 │
│   - X-axis: Reach Index (R1, R2, ...)                │
│   - Y-axis: Aggregated value                          │
│   - Bars colored by value (Viridis colorscale)        │
│   - Color scale legend                                │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### Dynamic Viewer Sub-tab
```
┌────────────────────────────────────────────────────────┐
│ Variable: [Transport capacity [m^3] ▼]                │
├────────────────────────────────────────────────────────┤
│ Time Step: [━━━━━●━━━━━━━━━━] 45 / 365               │
│ [▶ Play]                                              │
├────────────────────────────────────────────────────────┤
│                                                        │
│    Transport capacity [m^3] - Time Step 45            │
│                                                        │
│   Animated bar chart:                                 │
│   - Updates as slider moves                           │
│   - Plasma colorscale                                 │
│   - Smooth transitions                                │
│                                                        │
└────────────────────────────────────────────────────────┘
```

#### Statistics Sub-tab
```
┌────────────────────────────────────────────────────────┐
│ [Refresh Statistics]                                   │
├────────────────────────────────────────────────────────┤
│ Results Summary                                        │
│                                                        │
│ ┌─────────────┬───────┬────────┬────────┬──────┬─────┐│
│ │ Variable    │ Shape │ Mean   │ Std    │ Min  │ Max ││
│ ├─────────────┼───────┼────────┼────────┼──────┼─────┤│
│ │ Volume out  │365x10 │ 125.43 │ 45.21  │12.3  │345.6││
│ │ Volume in   │365x10 │ 123.87 │ 44.98  │11.9  │342.1││
│ │ D50 active  │365x10 │  0.045 │ 0.012  │0.020 │0.089││
│ │ ...         │...    │ ...    │ ...    │ ...  │ ... ││
│ └─────────────┴───────┴────────┴────────┴──────┴─────┘│
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Color Palette

### Primary Colors
- **Primary Blue**: #3498db - Buttons, selected items, focus borders
- **Dark Gray-Blue**: #2c3e50 - Dock titles, toolbar, headers
- **Success Green**: #27ae60 - Success messages, completed items
- **Warning Orange**: #f39c12 - Warnings, cautions
- **Danger Red**: #e74c3c - Errors, delete actions

### Background Colors
- **Very Light Gray**: #f5f5f5 - Main window background
- **Light Gray**: #ecf0f1 - Alternating table rows, inactive tabs
- **White**: #ffffff - Input fields, tables, active areas

### Text Colors
- **Primary Text**: #2c3e50 - Main text
- **Secondary Text**: #7f8c8d - Disabled items, hints
- **White Text**: #ffffff - On dark backgrounds (buttons, toolbars)

## Interactive Elements

### Buttons
- **Default State**: Blue background, white text, rounded corners
- **Hover**: Darker blue (#2980b9)
- **Pressed**: Even darker blue (#21618c)
- **Disabled**: Light gray (#bdc3c7), gray text

### Input Fields
- **Default**: White background, light gray border
- **Focus**: Blue border (2px)
- **Error**: Red border (not shown by default)

### Tables
- **Header**: Dark gray background, white text, bold
- **Rows**: Alternating white and light gray
- **Selected**: Blue background, white text

### Sliders
- **Track**: Light gray, rounded
- **Handle**: Blue circle, darker blue on hover
- **Active**: Slightly larger handle

## Keyboard Shortcuts Display

When hovering over toolbar items:
```
▶ Run Simulation (Ctrl+R)
📊 Load Results (Ctrl+L)
❓ Help (F1)
```

## Dialog Windows

### Reach Editor Dialog
```
┌──────────────────────────────────────┐
│ Edit Reach: 1                    [×] │
├──────────────────────────────────────┤
│ Reach 1                              │
│                                      │
│ [Basic Info] [Geometry] [Sediment]  │
│ ┌────────────────────────────────┐  │
│ │ Reach Name: [Main Channel___]  │  │
│ │                                │  │
│ │ From Node: 1                   │  │
│ │ To Node: 2                     │  │
│ └────────────────────────────────┘  │
│                                      │
│  [Reset]     [Cancel] [Save Changes] │
└──────────────────────────────────────┘
```

### Help Dialog
```
┌────────────────────────────────────────┐
│ D-CASCADE Help                     [×] │
├────────────────────────────────────────┤
│                                        │
│  Quick Start:                          │
│  1. Load Data                          │
│  2. Configure Model                    │
│  3. Run Simulation                     │
│  4. View Results                       │
│                                        │
│  Features:                             │
│  • GIS Viewer                          │
│  • Discharge Editor                    │
│  • Results Analysis                    │
│                                        │
│  Keyboard Shortcuts:                   │
│  Ctrl+R: Run simulation                │
│  Ctrl+L: Load results                  │
│  ...                                   │
│                                        │
│             [OK]                       │
└────────────────────────────────────────┘
```

## Status Messages

Located at bottom of window:
```
Ready
Simulation running... 45%
Configuration saved
Loading shapefile...
Results loaded successfully
```

## Responsive Design

The GUI adapts to different window sizes:
- **Large (1600x1000+)**: All panels visible, full-width plots
- **Medium (1200x800)**: Panels stack, plots adjust
- **Small (800x600)**: Minimal layout, scrollbars appear

## Accessibility Features

- **High Contrast**: Dark text on light backgrounds
- **Clear Labels**: All inputs have descriptive labels
- **Tooltips**: Hover help on all interactive elements
- **Keyboard Navigation**: Tab through all controls
- **Status Feedback**: Visual and text feedback for all actions

## Performance Indicators

- **Loading**: Spinners and progress messages
- **Large Data**: Row limits with indicators
- **Processing**: Non-blocking UI with background threads
- **Responsive**: Smooth animations and transitions

## Summary

The D-CASCADE GUI provides a modern, intuitive interface with:
- ✅ Clear visual hierarchy
- ✅ Consistent color scheme
- ✅ Professional styling
- ✅ Interactive elements
- ✅ Comprehensive feedback
- ✅ Accessible design
- ✅ Responsive layout

All visual elements work together to create a cohesive, easy-to-use modeling environment.
