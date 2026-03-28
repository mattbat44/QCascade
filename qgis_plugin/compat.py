"""
@brief Compatibility utilities for QGIS 3.x (PyQt5) and QGIS 4.0 (PyQt6).

This module provides a unified interface for Qt symbols and types that changed
between PyQt5 (used by QGIS 3.x) and PyQt6 (used by QGIS 4.0).

@author D-CASCADE Team
"""

from qgis.PyQt.QtCore import Qt, PYQT_VERSION_STR
from qgis.PyQt.QtWidgets import QDockWidget

# Detect PyQt major version (5 for QGIS 3.x, 6 for QGIS 4.0)
PYQT_MAJOR = int(PYQT_VERSION_STR.split('.')[0])

# ---------------------------------------------------------------------------
# QVariant compatibility
# PyQt5 (QGIS 3.x): QgsField("name", QVariant.Int) uses QVariant.Type constants
# PyQt6 (QGIS 4.0): QVariant is not available; QMetaType.Type constants are used
# ---------------------------------------------------------------------------
if PYQT_MAJOR >= 6:
    try:
        from qgis.PyQt.QtCore import QMetaType

        class QVariant:  # noqa: N801
            """Compatibility shim replacing PyQt5 QVariant type constants."""
            Int = QMetaType.Type.Int
            Double = QMetaType.Type.Double
            String = QMetaType.Type.QString
    except (ImportError, AttributeError):
        # Fallback with raw integer type codes (QMetaType numeric values)
        class QVariant:  # noqa: N801
            Int = 2    # QMetaType::Int
            Double = 6  # QMetaType::Double
            String = 10  # QMetaType::QString
else:
    from qgis.PyQt.QtCore import QVariant  # noqa: F401

# ---------------------------------------------------------------------------
# Qt enum compatibility
# PyQt5 uses a flat namespace (e.g. Qt.Horizontal).
# PyQt6 uses scoped enums (e.g. Qt.Orientation.Horizontal).
# ---------------------------------------------------------------------------

# Orientation
try:
    Qt_Horizontal = Qt.Horizontal
    Qt_Vertical = Qt.Vertical
except AttributeError:
    Qt_Horizontal = Qt.Orientation.Horizontal
    Qt_Vertical = Qt.Orientation.Vertical

# DockWidgetArea
try:
    Qt_BottomDockWidgetArea = Qt.BottomDockWidgetArea
    Qt_RightDockWidgetArea = Qt.RightDockWidgetArea
    Qt_LeftDockWidgetArea = Qt.LeftDockWidgetArea
    Qt_TopDockWidgetArea = Qt.TopDockWidgetArea
except AttributeError:
    Qt_BottomDockWidgetArea = Qt.DockWidgetArea.BottomDockWidgetArea
    Qt_RightDockWidgetArea = Qt.DockWidgetArea.RightDockWidgetArea
    Qt_LeftDockWidgetArea = Qt.DockWidgetArea.LeftDockWidgetArea
    Qt_TopDockWidgetArea = Qt.DockWidgetArea.TopDockWidgetArea

# ContextMenuPolicy
try:
    Qt_CustomContextMenu = Qt.CustomContextMenu
except AttributeError:
    Qt_CustomContextMenu = Qt.ContextMenuPolicy.CustomContextMenu

# CheckState
try:
    Qt_Checked = Qt.Checked
    Qt_Unchecked = Qt.Unchecked
    Qt_PartiallyChecked = Qt.PartiallyChecked
except AttributeError:
    Qt_Checked = Qt.CheckState.Checked
    Qt_Unchecked = Qt.CheckState.Unchecked
    Qt_PartiallyChecked = Qt.CheckState.PartiallyChecked

# ---------------------------------------------------------------------------
# QDockWidget feature flags
# PyQt5: QDockWidget.DockWidgetMovable
# PyQt6: QDockWidget.DockWidgetFeature.DockWidgetMovable
# ---------------------------------------------------------------------------
try:
    DockWidgetMovable = QDockWidget.DockWidgetMovable
    DockWidgetFloatable = QDockWidget.DockWidgetFloatable
    DockWidgetClosable = QDockWidget.DockWidgetClosable
except AttributeError:
    DockWidgetMovable = QDockWidget.DockWidgetFeature.DockWidgetMovable
    DockWidgetFloatable = QDockWidget.DockWidgetFeature.DockWidgetFloatable
    DockWidgetClosable = QDockWidget.DockWidgetFeature.DockWidgetClosable

# ---------------------------------------------------------------------------
# Matplotlib Qt backend
# Matplotlib 3.5+ provides backend_qtagg which works with both PyQt5 and PyQt6.
# Older versions only have backend_qt5agg.
# ---------------------------------------------------------------------------
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg  # noqa: F401
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT  # noqa: F401
    MATPLOTLIB_BACKEND = 'qtagg'
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg  # noqa: F401
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT  # noqa: F401
    MATPLOTLIB_BACKEND = 'qt5agg'
