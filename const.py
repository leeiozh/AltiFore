import numpy as np

path_to_af = __file__[:-len(__file__.split('/')[-1])]
colors = ['yellow', 'red', 'orange', 'green', 'blue', 'purple', 'pink', 'grey']
color_rgd = ['FFFF00', 'FF0000', 'FF8000', '009900', '0080FF', '7F00FF', 'FFCCFF', 'C0C0C0']
SAT_NAMES = ['CFOSAT', 'HAIYANG-2B', 'JASON-3', 'SARAL', 'SENTINEL-3A', 'SENTINEL-3B', 'SENTINEL-6', 'CRYOSAT 2']
SAT_HEIGHTS = np.array([519, 966, 1336, 781, 814, 804, 1336, 728])  # height of altimeters orbits