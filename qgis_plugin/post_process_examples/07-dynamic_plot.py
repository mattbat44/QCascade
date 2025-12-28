# -*- coding: utf-8 -*-
"""
Created on Wed Aug 20 17:17:11 2025

@author: diane


Creates a dynamic plot

Choose between:
'Volume out [m^3]':         total volume of sediment leaving a reach per time step (= sediment flux x time step)
'Volume in [m^3]':          total volume of sediment entering a reach per time step
'Transport capacity [m^3]': total transport capacity computed in a reach per time step (= volume out if the supply is not limited)
'Sediment budget [m^3]':    total sediment budget per time step (+ deposition, - erosion) (= vol in - vol out)
'D50 active layer [m]':     D50 of the active layer per time step (used to computed the transport capacity)
'D50 volume out [m]' :      D50 of the volume leaving the reach per time step 

"""

# Libraries
import sys, os
import pandas as pd
import geopandas as gpd

# Add source (src) folder in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from plot_function import dynamic_plot
from json_serializer import load_from_json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

#---------------------Path to the JSON output

path = os.path.join(SCRIPT_DIR, "..\\cascade_results\\") 
name_simu = 'Vjosa_test'

#---------------------Path to the input river network (.shp) or (.csv)

path_river_network = os.path.join(SCRIPT_DIR, "..\\inputs\\input_trial\\") #Path to the shp
name_river_network = "River_Network.shp"


       

###########################################################################

data_output = load_from_json(path + name_simu + '.json')
ReachData = gpd.GeoDataFrame.from_file(path_river_network + name_river_network)

keep_slider = dynamic_plot(data_output, ReachData)