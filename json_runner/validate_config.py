import json
import os
import sys

def validate_config(config):
    """
    Validates the configuration dictionary against a defined schema.
    Returns True if valid, False otherwise.
    Prints validation errors to stderr.
    """
    
    # Define schema with types, required fields, and allowed values/ranges
    schema = {
        "paths": {
            "river_network_shp": {"type": str, "required": True, "description": "Path to the river network shapefile (.shp)"},
            "discharge_csv": {"type": str, "required": True, "description": "Path to the discharge CSV file"},
            "output_name": {"type": str, "required": True, "description": "Name of the output simulation"}
        },
        "sediment": {
            "range": {"type": list, "length": 2, "required": True, "description": "Sediment size range in Phi scale [min, max]"},
            "n_classes": {"type": int, "min": 1, "required": True, "description": "Number of sediment classes"},
            "deposit_layer_thickness": {"type": (int, float), "min": 0, "required": True, "description": "Initial deposit layer thickness in meters"},
            "active_layer_depth": {"type": (int, float, str), "required": True, "description": "Active layer depth in meters or '2D90'"},
            "active_layer_method": {"type": int, "allowed": [1, 2], "required": False, "default": 1, "description": "Method for active layer calculation"}
        },
        "time": {
            "timescale": {"type": int, "min": 1, "required": True, "description": "Number of time steps"},
            "ts_length": {"type": (int, float), "min": 1, "required": True, "description": "Length of each time step in seconds"}
        },
        "physics": {
            "transport_capacity_formula": {
                "type": int, 
                "allowed": [1, 2, 3, 4, 5, 6, 7, 8], 
                "required": True,
                "description": "1: Parker-Klingeman, 2: Wilcock-Crowe, 3: Engelund-Hansen, 4: Yang, 5: Wong-Parker, 6: Ackers-White, 7: Rickenmann, 8: WC-Mueller"
            },
            "transport_partitioning": {
                "type": int, 
                "allowed": [1, 2, 3, 4], 
                "required": True,
                "description": "1: Direct, 2: BMF, 3: Molinas, 4: Shear stress correction"
            },
            "flow_depth_formula": {"type": int, "allowed": [1, 2], "required": False, "default": 1, "description": "1: Manning, 2: Ferguson"},
            "velocity_formula": {"type": int, "allowed": [1, 2], "required": False, "default": 2, "description": "Method for calculating velocity"},
            "velocity_partitioning": {"type": int, "allowed": [1], "required": False, "default": 1, "description": "Partitioning in section for velocity"},
            "slope_reduction": {"type": int, "allowed": [1, 2, 3, 4], "required": False, "default": 1, "description": "1: No reduction, >1: Reduction formulas"},
            "width_calculation": {"type": int, "allowed": [1, 2], "required": False, "default": 1, "description": "1: Static, 2: Dynamic (Lugo)"},
            "update_slope": {"type": bool, "required": False, "default": False, "description": "Update slope based on deposition/erosion"},
            "velocity_height": {"type": (str, int, float), "required": False, "default": "2D90", "description": "Height for velocity calculation (e.g., '2D90' or float)"},
            "erosion_max": {"type": (int, float, type(None)), "required": False, "default": None, "description": "Maximum erosion depth per time step"}
        },
        "options": {
            "save_deposit_layer": {"type": str, "allowed": ["yearly", "always", "never"], "required": False, "default": "never", "description": "When to save deposit layer"},
            "round_parameter": {"type": (int, float), "min": 0, "required": False, "default": 0, "description": "Minimum volume for mobilization (decimal digit)"},
            "force_pass_external_inputs": {"type": bool, "required": False, "default": False, "description": "Force passing external inputs"}
        },
        "external_inputs": {
            # Optional section: at least one of 'csv_files' or 'dir' should be provided when section exists
            "csv_files": {"type": list, "required": False, "description": "List of CSV files for per-reach external inputs"},
            "dir": {"type": str, "required": False, "description": "Directory containing per-reach CSVs (one file per reach)"},
            "tensor_npy": {"type": str, "required": False, "description": "Path to a precomputed external_inputs .npy tensor"},
            "per_reach_csvs": {"type": list, "required": False, "description": "List of objects {reach_idx:int, path:str} specifying CSVs attached to specific reaches"},
            "grain_unit": {"type": str, "required": False, "default": "mm", "description": "Units for D-quantiles: 'mm' or 'm'"},
            "default_sigma_g": {"type": (int, float), "required": False, "default": 1.6, "description": "Geometric std dev fallback when only D50 provided"}
        }
    }

    is_valid = True

    for section, fields in schema.items():
        if section not in config:
            # 'external_inputs' is optional; skip if absent
            if section == "external_inputs":
                continue
            print(f"Error: Missing section '{section}' in config.", file=sys.stderr)
            is_valid = False
            continue
        
        for field, rules in fields.items():
            if field not in config[section]:
                if rules.get("required", False):
                    print(f"Error: Missing required field '{field}' in section '{section}'.", file=sys.stderr)
                    is_valid = False
                continue
            
            value = config[section][field]
            
            # Type check
            expected_type = rules["type"]
            if expected_type == (int, float):
                if not isinstance(value, (int, float)):
                     print(f"Error: Field '{field}' in '{section}' must be a number. Got {type(value).__name__}.", file=sys.stderr)
                     is_valid = False
            elif expected_type == (str, int, float):
                 if not isinstance(value, (str, int, float)):
                     print(f"Error: Field '{field}' in '{section}' must be string or number. Got {type(value).__name__}.", file=sys.stderr)
                     is_valid = False
            elif expected_type == (int, float, type(None)):
                 if value is not None and not isinstance(value, (int, float)):
                     print(f"Error: Field '{field}' in '{section}' must be number or null. Got {type(value).__name__}.", file=sys.stderr)
                     is_valid = False
            elif not isinstance(value, expected_type):
                print(f"Error: Field '{field}' in '{section}' must be of type {expected_type.__name__}. Got {type(value).__name__}.", file=sys.stderr)
                is_valid = False
                continue

            # Value checks
            if "allowed" in rules and value not in rules["allowed"]:
                print(f"Error: Field '{field}' in '{section}' has invalid value '{value}'. Allowed: {rules['allowed']}.", file=sys.stderr)
                is_valid = False
            
            if "min" in rules and isinstance(value, (int, float)) and value < rules["min"]:
                print(f"Error: Field '{field}' in '{section}' must be >= {rules['min']}. Got {value}.", file=sys.stderr)
                is_valid = False
                
            if "length" in rules and isinstance(value, list) and len(value) != rules["length"]:
                print(f"Error: Field '{field}' in '{section}' must have length {rules['length']}. Got {len(value)}.", file=sys.stderr)
                is_valid = False

    # Additional cross-field validation for external_inputs section
    if "external_inputs" in config and isinstance(config["external_inputs"], dict):
        ext = config["external_inputs"]
        # Ensure csv_files is a list of strings if present
        if "csv_files" in ext:
            if not isinstance(ext["csv_files"], list) or not all(isinstance(x, str) for x in ext["csv_files"]):
                print("Error: 'external_inputs.csv_files' must be a list of strings.", file=sys.stderr)
                is_valid = False
        # Ensure per_reach_csvs is a list of {reach_idx, path}
        if "per_reach_csvs" in ext:
            ok = isinstance(ext["per_reach_csvs"], list) and all(
                isinstance(el, dict) and "reach_idx" in el and "path" in el for el in ext["per_reach_csvs"]
            )
            if not ok:
                print("Error: 'external_inputs.per_reach_csvs' must be a list of objects with 'reach_idx' and 'path'.", file=sys.stderr)
                is_valid = False
        # Ensure grain_unit is among allowed values if present
        if "grain_unit" in ext and ext["grain_unit"] not in ["mm", "m"]:
            print("Error: 'external_inputs.grain_unit' must be 'mm' or 'm'.", file=sys.stderr)
            is_valid = False
        # Require at least one source when section exists
        has_source = (
            ("dir" in ext and isinstance(ext["dir"], str) and len(ext["dir"]) > 0) or
            ("csv_files" in ext and isinstance(ext["csv_files"], list) and len(ext["csv_files"]) > 0) or
            ("tensor_npy" in ext and isinstance(ext["tensor_npy"], str) and len(ext["tensor_npy"]) > 0)
        )
        if not has_source:
            print("Error: 'external_inputs' section requires at least one of 'dir' or 'csv_files'.", file=sys.stderr)
            is_valid = False

    return is_valid

def print_schema_help():
    """Prints the schema documentation."""
    # Re-define schema here or pass it out from validate_config if refactored. 
    # For simplicity, I'll just print a summary based on the structure above.
    print("D-CASCADE JSON Configuration Schema:")
    print("====================================")
    # (In a real implementation, we'd traverse the schema dict to print this)
    # For now, let's just say "See validate_config source for details" or implement a quick traversal if needed.
    # But the user asked to "show the range of values that are possible".
    
    # Let's instantiate the schema again to print it
    schema = {
        "paths": {
            "river_network_shp": {"description": "Path to the river network shapefile (.shp)"},
            "discharge_csv": {"description": "Path to the discharge CSV file"},
            "output_name": {"description": "Name of the output simulation"}
        },
        "sediment": {
            "range": {"description": "Sediment size range in Phi scale [min, max] (e.g., [-8, 5])"},
            "n_classes": {"description": "Number of sediment classes (int >= 1)"},
            "deposit_layer_thickness": {"description": "Initial deposit layer thickness in meters (float >= 0)"},
            "active_layer_depth": {"description": "Active layer depth in meters (float >= 0)"},
            "active_layer_method": {"description": "Method for active layer calculation (default: 1)"}
        },
        "time": {
            "timescale": {"description": "Number of time steps (int >= 1)"},
            "ts_length": {"description": "Length of each time step in seconds (float >= 1)"}
        },
        "physics": {
            "transport_capacity_formula": {"description": "1: Parker-Klingeman, 2: Wilcock-Crowe, 3: Engelund-Hansen, 4: Yang, 5: Wong-Parker, 6: Ackers-White, 7: Rickenmann, 8: WC-Mueller"},
            "transport_partitioning": {"description": "1: Direct, 2: BMF, 3: Molinas, 4: Shear stress correction"},
            "flow_depth_formula": {"description": "1: Manning, 2: Ferguson"},
            "velocity_formula": {"description": "Method for calculating velocity (default: 2)"},
            "velocity_partitioning": {"description": "Partitioning in section for velocity (default: 1)"},
            "slope_reduction": {"description": "1: No reduction, >1: Reduction formulas"},
            "width_calculation": {"description": "1: Static, 2: Dynamic (Lugo)"},
            "update_slope": {"description": "Update slope based on deposition/erosion (bool)"},
            "velocity_height": {"description": "Height for velocity calculation (e.g., '2D90' or float)"},
            "erosion_max": {"description": "Maximum erosion depth per time step (float or null)"}
        },
        "options": {
            "save_deposit_layer": {"description": "When to save deposit layer: 'yearly', 'always', 'never'"},
            "round_parameter": {"description": "Minimum volume for mobilization (decimal digit, >= 0)"},
            "force_pass_external_inputs": {"description": "Force passing external inputs (bool)"}
        }
    }
    
    for section, fields in schema.items():
        print(f"\n[{section}]")
        for field, info in fields.items():
            print(f"  - {field}: {info['description']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r') as f:
                    config = json.load(f)
                if validate_config(config):
                    print(f"Configuration '{json_file}' is valid.")
                else:
                    print(f"Configuration '{json_file}' is INVALID.")
                    sys.exit(1)
            except json.JSONDecodeError:
                print(f"Error: '{json_file}' is not a valid JSON file.")
                sys.exit(1)
        else:
            print(f"Error: File '{json_file}' not found.")
            sys.exit(1)
    else:
        print_schema_help()
