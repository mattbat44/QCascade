"""
@brief Results viewer dock components package
@author D-CASCADE Team
"""

from .time_series_tab import TimeSeriesTab
from .spatial_tab import SpatialTab
from .connectivity_tab import ConnectivityTab
from .long_profile_tab import LongProfileTab
from .animation_tab import AnimationTab
from .stats_tab import StatsTab

__all__ = [
    'TimeSeriesTab',
    'SpatialTab',
    'ConnectivityTab',
    'LongProfileTab',
    'AnimationTab',
    'StatsTab'
]
