# -*- coding: utf-8 -*-
"""
Export D-CASCADE simulation results to an Excel workbook.

Each result variable is written to a dedicated sheet:
  - 2-D variables (time × reach) → one sheet per variable.
  - 3-D variables (time × reach × sediment class) → one sheet per class.
  - Variables with more than 3 dimensions are skipped.

Both the main results (.json) and extended results (_ext.json) are exported
when available.

Requirements:
    pip install pandas openpyxl

@author: D-CASCADE Team
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add source (src) folder to the Python path
sys.path.append(os.path.abspath(os.path.join(SCRIPT_DIR, '../src')))
from json_serializer import load_from_json, results_to_spreadsheet

# ---------------------------------------------------------------------------
# User settings
# ---------------------------------------------------------------------------

#: Folder that contains the simulation output JSON files.
path = os.path.join(SCRIPT_DIR, "..\\cascade_results\\")

#: Base name of the simulation (without extension).
name_simu = 'Vjosa_test'

#: Optional list of reach IDs to use as column headers.
#: Set to None to use sequential integers (1, 2, …).
reach_ids = None  # e.g. [1, 2, 3, 4, 5, 6, 7]

# ---------------------------------------------------------------------------
# Load results
# ---------------------------------------------------------------------------

main_path = os.path.join(path, name_simu + '.json')
ext_path  = os.path.join(path, name_simu + '_ext.json')

data_output = load_from_json(main_path)

extended_output = None
if os.path.exists(ext_path):
    extended_output = load_from_json(ext_path)

# ---------------------------------------------------------------------------
# Export to spreadsheet
# ---------------------------------------------------------------------------

output_xlsx = os.path.join(path, name_simu + '_results.xlsx')

results_to_spreadsheet(
    data_output,
    output_xlsx,
    extended_output=extended_output,
    reach_ids=reach_ids,
)

print(f"Results exported to: {output_xlsx}")
