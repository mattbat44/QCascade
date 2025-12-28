"""
D-CASCADE QGIS Plugin
"""
def classFactory(iface):
    """Load D-CASCADE plugin class from file dcascade_plugin."""
    from .dcascade_plugin import DCascadePlugin
    return DCascadePlugin(iface)

