import numpy as np
import platform

import os
import sys

os_var = platform.system()
if os_var == 'Windows':
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable) + '\\'
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__)) + '\\'
    path_to_af = app_dir[:-len(app_dir.split('\\')[-1])]
else:
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable) + '/'
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__)) + '/'
    path_to_af = app_dir[:-len(app_dir.split('/')[-1])]

colors = ['yellow', 'red', 'orange', 'green', 'blue', 'purple', 'pink', 'grey', 'LightGreen']
color_rgd = ['FFFF00', 'FF0000', 'FF8000', '009900', '0080FF', '7F00FF', 'FFCCFF', 'C0C0C0', '90EE90']
SAT_NAMES = ['CFOSAT', 'HAIYANG-2B', 'JASON-3', 'SARAL', 'SENTINEL-3A', 'SENTINEL-3B', 'SENTINEL-6', 'CRYOSAT 2', 'SENTINEL-1A']
SAT_HEIGHTS = []
