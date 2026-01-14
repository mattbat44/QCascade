#!/usr/bin/env python3
"""
Example script for batch processing multiple DEMs using the QGIS river network extraction algorithm.

This script demonstrates how to use the river network extraction algorithm programmatically
from Python, which can be useful for processing multiple DEMs or automating workflows.

Requirements:
- QGIS 3.x with Python API
- SAGA GIS installed and configured
- extract_river_network.py in the same directory

Usage:
    python batch_process_dems.py

Note: This script needs to be run from within QGIS Python environment or with QGIS libraries in path.
For standalone use, see the QGIS Processing GUI approach in README.md
"""

import os
from pathlib import Path

# This script is an example and would need to be run within QGIS Python environment
# For actual batch processing, you can:
# 1. Use QGIS Batch Processing (Processing > Batch Processing)
# 2. Use QGIS Python console with this as a template
# 3. Use qgis_process CLI tool (QGIS 3.16+)


def batch_process_with_qgis_process():
    """
    Example using qgis_process command-line tool (QGIS 3.16+)
    
    This is the recommended approach for batch processing as it doesn't
    require writing Python code or using the QGIS GUI.
    """
    
    # Example DEMs to process
    dems = [
        {"input": "catchment_A.tif", "output": "network_A.shp", "area": 1000000},
        {"input": "catchment_B.tif", "output": "network_B.shp", "area": 500000},
        {"input": "catchment_C.tif", "output": "network_C.shp", "area": 2000000},
    ]
    
    for dem in dems:
        cmd = f"""qgis_process run dcascade:extract_river_network_dcascade \
            --INPUT_DEM={dem['input']} \
            --MIN_CONTRIBUTING_AREA={dem['area']} \
            --OUTPUT={dem['output']}"""
        
        print(f"Processing {dem['input']}...")
        print(f"Command: {cmd}")
        # os.system(cmd)  # Uncomment to actually run
    
    print("\nTo run this batch processing:")
    print("1. Save this script")
    print("2. Uncomment the os.system(cmd) line")
    print("3. Run: python batch_process_dems.py")


def batch_process_with_python_api():
    """
    Example using QGIS Python API directly
    
    This approach requires running from QGIS Python console or with QGIS
    libraries properly configured.
    """
    
    example_code = """
    # Run this code in QGIS Python Console
    
    from qgis import processing
    from pathlib import Path
    
    # Define your input DEMs and parameters
    dems = [
        {"input": "/path/to/catchment_A.tif", "output": "/path/to/network_A.shp", "area": 1000000},
        {"input": "/path/to/catchment_B.tif", "output": "/path/to/network_B.shp", "area": 500000},
    ]
    
    # Process each DEM
    for dem in dems:
        print(f"Processing {Path(dem['input']).name}...")
        
        result = processing.run(
            "dcascade:extract_river_network_dcascade",
            {
                'INPUT_DEM': dem['input'],
                'MIN_CONTRIBUTING_AREA': dem['area'],
                'OUTPUT': dem['output']
            }
        )
        
        print(f"  Output: {result['OUTPUT']}")
        print(f"  Done!")
    
    print("All DEMs processed!")
    """
    
    print("To use the Python API approach:")
    print("1. Open QGIS")
    print("2. Go to Plugins > Python Console")
    print("3. Paste and modify the following code:")
    print(example_code)


def batch_process_with_gui():
    """
    Instructions for using QGIS GUI batch processing
    """
    
    instructions = """
    QGIS GUI Batch Processing (Easiest Method):
    
    1. Open QGIS
    2. Go to Processing > Toolbox
    3. Find: D-CASCADE > Extract River Network for D-CASCADE
    4. Right-click on the algorithm > Execute as Batch Process
    5. In the batch dialog:
       - Click "Add Row" for each DEM you want to process
       - Fill in parameters for each row:
         * Input DEM: Select your DEM file
         * Minimum Contributing Area: Enter threshold
         * Output: Specify output shapefile path
    6. Click "Run"
    
    This approach is:
    - User-friendly (no coding required)
    - Allows easy parameter adjustment per DEM
    - Provides visual progress feedback
    - Recommended for most users
    """
    
    print(instructions)


def create_parameter_file():
    """
    Create a CSV file with parameters for batch processing
    
    This can be used as a reference for organizing your batch processing parameters.
    """
    
    csv_content = """input_dem,output_network,min_area_m2,notes
catchment_A.tif,network_A.shp,1000000,Main catchment
catchment_B.tif,network_B.shp,500000,Tributary catchment
catchment_C.tif,network_C.shp,2000000,Large river basin
"""
    
    output_file = "batch_parameters.csv"
    with open(output_file, 'w') as f:
        f.write(csv_content)
    
    print(f"Created example parameter file: {output_file}")
    print("Edit this file with your DEM paths and parameters")
    print("Then use one of the batch processing methods above")


if __name__ == "__main__":
    print("=" * 70)
    print("D-CASCADE: Batch Processing River Network Extraction")
    print("=" * 70)
    print()
    
    print("This script demonstrates three approaches for batch processing:")
    print()
    
    print("OPTION 1: QGIS GUI Batch Processing (RECOMMENDED)")
    print("-" * 70)
    batch_process_with_gui()
    print()
    
    print("OPTION 2: qgis_process Command Line (QGIS 3.16+)")
    print("-" * 70)
    batch_process_with_qgis_process()
    print()
    
    print("OPTION 3: QGIS Python API")
    print("-" * 70)
    batch_process_with_python_api()
    print()
    
    print("=" * 70)
    print("Creating example parameter file...")
    create_parameter_file()
    print()
    
    print("For more information, see:")
    print("  - qgis_processing/README.md")
    print("  - qgis_processing/QUICKSTART.md")
    print("=" * 70)
