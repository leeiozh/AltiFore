import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import matplotlib.ticker as mticker
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.feature as cfe

colors = ['yellow', 'red', 'orange', 'green', 'blue', 'purple', 'pink', 'grey']
SAT_NAMES = ['CFOSAT', 'HAIYANG-2B', 'JASON-3', 'SARAL', 'SENTINEL-3A', 'SENTINEL-3B', 'SENTINEL-6', 'CRYOSAT 2']

fig = plt.figure(figsize=(5, 5), dpi=700)
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())


def get_fig():
    return fig, ax


def draw_map(arr_for_draw, tr_lat, tr_lon):
    lat_min = int(np.min(arr_for_draw[1, :])) - 3
    lat_max = int(np.max(arr_for_draw[1, :])) + 3
    lon_min = int(np.min(arr_for_draw[0, :])) - 3
    lon_max = int(np.max(arr_for_draw[0, :])) + 3
    step_lon = int((lon_max - lon_min) / 10.)
    step_lat = int((lat_max - lat_min) / 10.)

    resol = '50m'
    ocean = cfe.NaturalEarthFeature('physical', 'ocean', scale=resol, edgecolor='none', facecolor='white')
    land = cfe.NaturalEarthFeature('physical', 'land', scale=resol, edgecolor='k', facecolor=cfe.COLORS['land'])

    ax.add_feature(ocean, zorder=0, linewidth=0.2)
    ax.add_feature(land, zorder=0, linewidth=0.2)
    ax.add_feature(cfe.COASTLINE)
    ax.add_feature(cfe.BORDERS, linestyle=':')

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=0.2, color='grey', alpha=1)
    gl.xlabels_top = False
    gl.ylabels_left = False
    gl.xlocator = mticker.FixedLocator(np.arange(-180, 180, step_lon))
    gl.ylocator = mticker.FixedLocator(np.arange(-90, 90, step_lat))
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 8}
    gl.ylabel_style = {'size': 8}

    ax.set_extent([lat_min, lat_max, lon_min, lon_max])

    color_for_scat = [colors[s] for s in arr_for_draw[2, :]]
    ax.scatter(arr_for_draw[0, :], arr_for_draw[1, :], color=color_for_scat, alpha=1, s=10)

    ax.scatter(tr_lon, tr_lat, label='Input locations', zorder=10, marker='+', color='black')

    for i in range(len(SAT_NAMES)):
        plt.scatter([0], [0], color=colors[i], label=SAT_NAMES[i], alpha=0.)
    plt.legend(loc='best', fontsize="6")
