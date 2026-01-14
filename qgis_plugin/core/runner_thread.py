import sys
import os
import traceback
import subprocess
from pathlib import Path
from qgis.PyQt.QtCore import QThread, pyqtSignal

# Ensure plugin-bundled src/json_runner are on path (src first to avoid plugin package shadowing)
current_dir = os.path.dirname(os.path.abspath(__file__))
plugin_dir = os.path.realpath(os.path.abspath(os.path.join(current_dir, '..')))
project_root = os.path.realpath(os.path.abspath(os.path.join(plugin_dir, '..')))

def _find_uv_python():
    """Find the Python executable from uv environment."""
    # Check for .venv in project root
    venv_paths = [
        Path(project_root) / '.venv' / 'Scripts' / 'python.exe',
        Path(project_root) / '.venv' / 'bin' / 'python',
    ]
    for venv_path in venv_paths:
        if venv_path.exists():
            return str(venv_path)
    
    # Fallback to system python if no venv found
    return sys.executable


class RunnerThread(QThread):
    log_message = pyqtSignal(str)
    simulation_finished = pyqtSignal(bool, str)  # success, message/output_path

    def __init__(self, config_path):
        super().__init__()
        self.config_path = config_path
        self.process = None

    def run(self):
        self.log_message.emit(f"Starting simulation with config: {self.config_path}")
        
        try:
            # Find the Python executable from uv environment
            python_exe = _find_uv_python()
            self.log_message.emit(f"Using Python: {python_exe}")
            
            # Find the run script
            run_script = Path(plugin_dir) / 'json_runner' / 'run_dcascade_json.py'
            if not run_script.exists():
                raise FileNotFoundError(f"Run script not found: {run_script}")
            
            # Run the simulation in a subprocess
            cmd = [python_exe, str(run_script), str(self.config_path)]
            self.log_message.emit(f"Running command: {' '.join(cmd)}")
            
            # Use subprocess with stdout/stderr capture
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=str(project_root)
            )
            
            # Stream output in real-time
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.log_message.emit(line.rstrip())
            
            # Wait for completion
            self.process.wait()
            return_code = self.process.returncode
            
            if return_code == 0:
                self.log_message.emit("Simulation completed successfully.")
                self.simulation_finished.emit(True, "Simulation Done")
            else:
                self.log_message.emit(f"Simulation failed with exit code {return_code}")
                self.simulation_finished.emit(False, f"Exit code: {return_code}")
                
        except Exception as e:
            self.log_message.emit(f"Error: {str(e)}")
            self.log_message.emit(traceback.format_exc())
            self.simulation_finished.emit(False, str(e))

