"""
@brief Results viewer dock components package
@author Matt Adams
"""

from .time_series_tab import TimeSeriesTab
from .spatial_tab import SpatialTab
from .long_profile_tab import LongProfileTab
from .animation_tab import AnimationTab

__all__ = [
    'TimeSeriesTab',
    'SpatialTab',
    'LongProfileTab',
    'AnimationTab',
]
