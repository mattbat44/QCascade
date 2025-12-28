import sys
import os
import traceback
from qgis.PyQt.QtCore import QThread, pyqtSignal

# Ensure src is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
src_path = os.path.join(project_root, 'src')
json_runner_path = os.path.join(project_root, 'json_runner')

if src_path not in sys.path:
    sys.path.append(src_path)
if json_runner_path not in sys.path:
    sys.path.append(json_runner_path)

# Import run_simulation from json_runner
try:
    from run_dcascade_json import run_simulation
except ImportError as e:
    # Fallback or error handling if paths are tricky
    print(f"Warning: Could not import run_simulation directly. Error: {e}")
    traceback.print_exc()

class RunnerThread(QThread):
    log_message = pyqtSignal(str)
    simulation_finished = pyqtSignal(bool, str)  # success, message/output_path

    def __init__(self, config_path):
        super().__init__()
        self.config_path = config_path

    def run(self):
        self.log_message.emit(f"Starting simulation with config: {self.config_path}")
        try:
            # Redirect stdout/stderr to capture logs?
            # For now, just run it.
            
            # We need to make sure run_simulation doesn't sys.exit() on us.
            # The original script does sys.exit(1) on validation failure.
            # We should probably wrap it or modify it, but let's try running it.
            
            # Since run_simulation is a function, we can call it.
            # However, it prints to stdout.
            
            run_simulation(self.config_path)
            
            self.log_message.emit("Simulation completed successfully.")
            self.simulation_finished.emit(True, "Simulation Done")
            
        except SystemExit as e:
            if e.code != 0:
                self.log_message.emit(f"Simulation failed with exit code {e.code}")
                self.simulation_finished.emit(False, "Simulation Failed")
            else:
                self.log_message.emit("Simulation completed.")
                self.simulation_finished.emit(True, "Simulation Done")
        except Exception as e:
            self.log_message.emit(f"Error: {str(e)}")
            self.log_message.emit(traceback.format_exc())
            self.simulation_finished.emit(False, str(e))

