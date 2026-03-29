"""
Q-Cascade QGIS Plugin
"""

# Ensure this package loads instead of the solver module with the same name
# when sys.path contains the bundled src folder ahead of the plugin root.
import os
import sys

_plugin_dir = os.path.dirname(__file__)
_solver_module_path = os.path.join(_plugin_dir, "src", "dcascade.py")

# Drop any preloaded solver module that would shadow the plugin package
_loaded = sys.modules.get(__name__)
if _loaded and getattr(_loaded, "__file__", "") == _solver_module_path:
    sys.modules.pop(__name__, None)

# Ensure plugin root is first so subsequent imports resolve here
if _plugin_dir in sys.path:
    sys.path.remove(_plugin_dir)
sys.path.insert(0, _plugin_dir)

def classFactory(iface):
    """Load Q-Cascade plugin class from file dcascade_plugin."""
    from .dcascade_plugin import DCascadePlugin
    return DCascadePlugin(iface)

