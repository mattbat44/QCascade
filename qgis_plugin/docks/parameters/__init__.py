"""
@brief Parameters dock components package
@author D-CASCADE Team
"""

from .inputs_tab import InputsTab
from .physics_tab import PhysicsTab
from .sediment_tab import SedimentTab
from .time_tab import TimeTab
from .options_tab import OptionsTab
from .external_inputs_tab import ExternalInputsTab

__all__ = [
    'InputsTab',
    'PhysicsTab',
    'SedimentTab',
    'TimeTab',
    'OptionsTab',
    'ExternalInputsTab'
]
