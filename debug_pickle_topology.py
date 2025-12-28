import pickle
import numpy as np
import os

file_path = r"c:\Users\matta\Documents\dcascade-py-2.0.0\cascade_results\vjosa_gui.p"
ext_file_path = r"c:\Users\matta\Documents\dcascade-py-2.0.0\cascade_results\vjosa_gui_ext.p"

def inspect_pickle(path):
    if os.path.exists(path):
        print(f"Loading {path}...")
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            print(f"Keys in {os.path.basename(path)}:")
            for key in data.keys():
                val = data[key]
                if isinstance(val, np.ndarray):
                    print(f"  {key}: {val.shape}")
                elif isinstance(val, list):
                    print(f"  {key}: list len={len(val)}")
                else:
                    print(f"  {key}: {type(val)}")
            return data
        except Exception as e:
            print(f"Error loading pickle: {e}")
            return None
    else:
        print(f"File not found: {path}")
        return None

data = inspect_pickle(file_path)
data_ext = inspect_pickle(ext_file_path)

# Check Simulation parameters
if data and 'Simulation parameters' in data:
    print("\nSimulation parameters content:")
    sim_params = data['Simulation parameters']
    if isinstance(sim_params, dict):
        for k, v in sim_params.items():
            print(f"  {k}: {type(v)}")
            if k == 'network':
                print(f"    Network: {v}")
            if k == 'reach_data':
                print(f"    Reach Data: {v}")


# Check for elevation in data
if data and 'Node_el [m]' in data:
    print("\n'Node_el [m]' found in standard results.")
elif data_ext and 'Node_el [m]' in data_ext:
    print("\n'Node_el [m]' found in extended results.")
