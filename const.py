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

colors = ["chocolate", "salmon", "darkorange", "gold", "greenyellow", "mediumseagreen", "turquoise", "deepskyblue",
          "cornflowerblue", "violet", "mediumorchid"]
color_rgd = ['d2691e', 'fa8072', 'ff8c00', 'ffd700', 'adff2f', '3cb371', '40e0d0', '00bfff', '6495ed', 'ee82ee',
             'ba55d3', 'f0e68c']
SAT_NAMES = ['CFOSAT', 'HAIYANG-2B', 'JASON-3', 'SARAL', 'SENTINEL-3A', 'SENTINEL-3B', 'SENTINEL-6', 'CRYOSAT 2',
             'SENTINEL-1A', 'HAIYANG-2C', 'SWOT']
SAT_HEIGHTS = []

SHIP_TIME = 3  # ship time for shifting time of measurements (only at the bottom of picture)

SELECT_FILE = False

PROJECTION = 0  # "Ortho"

GAP = 1  # hours
