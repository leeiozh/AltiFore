import numpy as np
import geopy.distance as dist
from skyfield.api import utc
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy
import matplotlib.ticker as mticker
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.feature as cfeature

from tkinter import ttk
from PIL import ImageTk, Image

def add_img(file, win_x, win_y):
    img = ImageTk.PhotoImage(Image.open(file))

    if img.width() > img.height():
        img = ImageTk.PhotoImage(
            Image.open(file).resize(
                (int(0.6 * win_x), int(0.6 * win_x / img.width() * img.height()))))
    else:
        img = ImageTk.PhotoImage(
            Image.open(file).resize((int(win_y / img.height() * img.width()), win_y)))

    return img
