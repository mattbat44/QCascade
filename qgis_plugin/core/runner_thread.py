import sys
import os
import traceback
import importlib.util
from importlib.machinery import SourceFileLoader
from qgis.PyQt.QtCore import QThread, pyqtSignal

# Ensure plugin-bundled src/json_runner are on path (src first to avoid plugin package shadowing)
current_dir = os.path.dirname(os.path.abspath(__file__))
plugin_dir = os.path.realpath(os.path.abspath(os.path.join(current_dir, '..')))
src_path = os.path.join(plugin_dir, 'src')
json_runner_path = os.path.join(plugin_dir, 'json_runner')

for p in [json_runner_path, src_path]:
    if p and os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

run_simulation = None
_last_import_error = ""

def _load_run_simulation():
    """Load run_simulation with multiple strategies; return callable or None."""
    global _last_import_error
    _last_import_error = ""
    # 1) Direct import using sys.path
    try:
        from run_dcascade_json import run_simulation as fn  # type: ignore
        return fn
    except Exception as e:
        _last_import_error = f"direct import failed: {e}\n{traceback.format_exc()}"

    # 1b) Try package-style import json_runner.run_dcascade_json
    try:
        from json_runner.run_dcascade_json import run_simulation as fn  # type: ignore
        return fn
    except Exception as e:
        _last_import_error = f"package import failed: {e}\n{traceback.format_exc()}"

    # 2) Import by file path using importlib.util
    loader_paths = [
        os.path.join(json_runner_path, "run_dcascade_json.py"),
    ]
    for loader_path in loader_paths:
        try:
            spec = importlib.util.spec_from_file_location("run_dcascade_json", loader_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)  # type: ignore
                fn = getattr(module, "run_simulation", None)
                if callable(fn):
                    return fn
        except Exception as e:
            _last_import_error = f"spec_from_file_location failed ({loader_path}): {e}\n{traceback.format_exc()}"

    # 3) Legacy SourceFileLoader fallback
    for loader_path in loader_paths:
        try:
            module = SourceFileLoader("run_dcascade_json", loader_path).load_module()
            fn = getattr(module, "run_simulation", None)
            if callable(fn):
                return fn
        except Exception as e:
            _last_import_error = f"SourceFileLoader fallback failed ({loader_path}): {e}\n{traceback.format_exc()}"

    return None

# Attempt load on module import
run_simulation = _load_run_simulation()


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
            
            fn = run_simulation or _load_run_simulation()
            if fn is None:
                err_msg = "run_simulation could not be loaded"
                if _last_import_error:
                    err_msg = f"{err_msg}: {_last_import_error}"
                    self.log_message.emit(err_msg)
                raise ImportError(err_msg)

            fn(self.config_path)
            
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

