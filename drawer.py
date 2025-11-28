import numpy as np  # conda install -c conda-forge numpy
import tkinter as tk  # conda install -c conda-forge tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime as dt
import requests
from skyfield.api import utc  # conda install -c conda-forge skyfield
from shutil import move

import matplotlib.pyplot as plt  # conda install -c conda-forge matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.ticker as mticker
import cartopy.crs as ccrs  # conda install -c conda-forge cartopy
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.feature as cfe

from tabber import prepare_sheet, convert_list
from calculator import calc_from_file, calc  # , calc_sun
from const import *
from pyproj import Geod

geod = Geod(ellps="WGS84")

once_sel = True  # flag for only one select file
once_cal = True  # flag for only one run calculation


class MyToolbar(NavigationToolbar2Tk):
    # special toolbar without coordinates for map
    def set_message(self, s):
        pass


class MainWindow:
    def __init__(self, monitor_size):

        self.draw_arr = np.ndarray  # array of data for drawing [lat_sat, lon_sat, num_sat, dist_km, time, lat_rv, lon_rv, num_dot]]
        self.res_list = np.ndarray  # array for creating a schedule {sat_name, date, time, dist, color}
        self.tr_lat = []  # input track latitudes
        self.tr_lon = []  # input track longitudes
        self.win_x = int(monitor_size[0] * 0.8)  # width of main window
        self.win_y = int(monitor_size[1] * 0.8)  # height of main window
        self.center_x = int(0.5 * (monitor_size[0] - self.win_x))  # x coord of center of main window
        self.center_y = int(0.5 * (monitor_size[1] - self.win_y))  # y coord of center of main window

        self.root = tk.Tk()
        self.root.title("AltiFore")
        self.root.geometry(f'{self.win_x}x{self.win_y}+{self.center_x}+{self.center_y}')

        ### frame for sun and map ###
        self.right_frame = tk.Frame(self.root, width=0.6 * self.win_x)
        self.right_frame.pack(side='right', expand=True, fill='both')
        self.right_frame.pack_propagate(False)

        self.map_frame = tk.Frame(self.right_frame)
        self.map_frame.pack(side='top', expand=True, fill='both')

        ### frame for updating, selection and entering data ###
        self.left_frame = tk.Frame(self.root, width=0.4 * self.win_x)
        self.left_frame.pack(side='top', pady=20)
        ttk.Label(self.left_frame,
                  text="Welcome to AltiFore!\n"
                       "Select a .KML file or enter vessels track in table\n"
                       "You will receive a .PNG map with marked altitracks,\n "
                       "a .XLSX with a daily schedule and .TXT with description.\n\n"
                       "In any unclear situation, please restart the app.\n\n"
                       "!!!!! ALL TIMES IN UTC FORMAT !!!!!", justify='center').pack(side='top')

        self.ship_time_fr = tk.Frame(self.left_frame)
        self.ship_time_fr.pack(side="top", pady=10)
        self.ship_time_lab = tk.Label(self.ship_time_fr, text="Ship timezone   >>>   ")
        self.ship_time_lab.pack(side="left")
        self.ship_time_entry = tk.Entry(self.ship_time_fr, width=3)
        self.ship_time_entry.insert(0, SHIP_TIME)
        self.ship_time_entry.pack(side="left")
        self.tooltip_label = tk.Label(self.map_frame, text="Calculate smth to show a map", padx=5, pady=5)
        self.tooltip_label.pack(side='bottom')

        ### frame for TLE progress bar and update button ###
        self.tle_frame = tk.Frame(self.left_frame, highlightbackground="black", highlightthickness=2)
        self.tle_frame.pack(side='top', pady=20)

        ### subframe for progress bar ###
        self.bar_frame = tk.Frame(self.tle_frame)
        self.bar_frame.pack(side='left', pady=20, padx=5)
        self.sty = ttk.Style(self.root)
        self.sty.layout("LabeledProgressbar", [('LabeledProgressbar.trough', {
            'children': [('LabeledProgressbar.pbar', {'side': 'left', 'sticky': 'ns'}),
                         ("LabeledProgressbar.label", {"sticky": ""})], 'sticky': 'nswe'})])
        self.bar = ttk.Progressbar(self.bar_frame, orient="horizontal", length=int(self.win_x * 0.3),
                                   style="LabeledProgressbar")
        self.bar.pack()
        tle_date = open(path_to_af + "tle/tle_data.txt", 'r').readline()[16:-1]
        self.sty.configure("LabeledProgressbar", text="Last update of TLE : " + tle_date)

        ### subframe update TLE button ###
        self.but_tle_frame = tk.Frame(self.tle_frame)
        self.but_tle_frame.pack(side='right', padx=5, pady=20)
        self.but_tle_up = tk.Button(self.but_tle_frame, text='Update!', command=self.click_update_tle, width=5,
                                    bg='grey75')
        self.but_tle_up.pack()

        ### frame for distance entry ###
        self.dist_frame = tk.Frame(self.left_frame)
        self.dist_frame.pack(side='top', padx=5, pady=20)
        ttk.Label(self.dist_frame, text="Distance between vessel and satellite tracks ").pack(side='left')
        self.km_entry = ttk.Entry(self.dist_frame, width=4)
        self.km_entry.insert(0, "200")
        self.km_entry.pack(side='left')
        ttk.Label(self.dist_frame, text="km").pack(side='left')

        ttk.Label(self.left_frame, text="Name for saving files (without extension) ").pack(side='top')
        self.save_name = ttk.Entry(self.left_frame, width=int(self.win_x * 0.03))
        self.save_name.insert(0, app_dir + "forecast_" + dt.utcnow().date().strftime("%d%m%Y"))
        self.save_name.pack(side='top', pady=10)

        ### frame for selecting a file ###
        self.select_frame = tk.Frame(self.left_frame, highlightbackground="pink", highlightcolor="pink",
                                     highlightthickness=2)
        self.select_frame.pack(side='top', padx=10, pady=10)

        ### subframe for buttons and path ###
        self.select_frame_up = ttk.Frame(self.select_frame)
        self.select_frame_up.pack(side='top', pady=10, padx=10)

        if SELECT_FILE:
            self.but_select = tk.Button(self.select_frame_up, text='Select a file', command=self.click_select,
                                        bg='pink')
        else:
            self.but_select = tk.Button(self.select_frame_up, text='Select a file', bg='pink')
        self.but_select.pack(side='left', padx=10)

        ### subframe for speed and start_date entries ###
        self.select_frame_down = ttk.Frame(self.select_frame)
        self.select_frame_down.pack(side='top', pady=5, padx=10)

        if not SELECT_FILE:
            self.fname = path_to_af + "tomorrow.kml"
            short_name = self.fname.rsplit('/', 1)[-1]  # only file name for displaying
            self.fname_lab = ttk.Label(self.select_frame_up, text=short_name)
            self.fname_lab.pack(side='left', padx=10)

            ttk.Label(self.select_frame_down, text='Average speed').pack(side='left', padx=5)
            self.speed_entry = ttk.Entry(self.select_frame_down, width=4)
            self.speed_entry.pack(side='left')
            ttk.Label(self.select_frame_down, text='kn').pack(side='left', padx=10)

            now = dt.utcnow().strftime("%d/%m/%y %H:%M").split(" ")

            ttk.Label(self.select_frame_down, text='Start date').pack(side='left', padx=5)
            self.date_entry = ttk.Entry(self.select_frame_down, width=8)
            self.date_entry.insert(0, now[0])
            self.date_entry.pack(side='left', padx=10)

            ttk.Label(self.select_frame_down, text='Time').pack(side='left', padx=5)
            self.time_entry = ttk.Entry(self.select_frame_down, width=5)
            self.time_entry.insert(0, now[1])
            self.time_entry.pack(side='left', padx=10)

            tk.Button(self.select_frame_up, text="Calculate from file!", command=self.click_calc_file, bg='pink').pack(
                side='right', padx=5)

        self.frame_green = ttk.Frame(self.left_frame)
        self.frame_green.pack(side='top')

        ### frame for tabular button ###
        self.add_frame = tk.Frame(self.frame_green, highlightbackground="LawnGreen", highlightcolor="LawnGreen",
                                  highlightthickness=2)
        self.add_frame.pack(side='top', pady=10)

        self.add_row_button = tk.Button(self.add_frame, text="Add row", command=self.add_row_to_column,
                                        bg='LawnGreen')
        self.add_row_button.pack(pady=10, side='left', padx=10)
        self.calc_table_button = tk.Button(self.add_frame, text="Calculate!", command=self.click_tab)
        self.calc_table_button.pack(pady=10, side='left', padx=10)
        self.rem_row_button = tk.Button(self.add_frame, text="Remove row", command=self.remove_row_from_column)
        self.rem_row_button.pack(pady=10, side='right', padx=10)

        ### frame for tabular ###
        self.table_frame = ttk.Frame(self.frame_green)
        self.table_frame.pack(side='top')

        ### subframes for tabular ###
        self.line_frames = []
        self.entry_arr = [[] for _ in range(4)]
        labels = ["Date\n(dd/mm/yy)", "Time\n(hh:mm)", u"Latitude\n(\u00B1dd mm ss)", u"Longitude\n(\u00B1dd mm ss)"]
        for column in range(4):
            frame = tk.Frame(self.table_frame)
            frame.pack(side="left", padx=int(self.win_x * 0.008), pady=5)
            ttk.Label(frame, text=labels[column]).pack(side="top")
            self.line_frames.append(frame)

        # initializing stuff which appears next
        self.fig = None  # map figure
        self.ax = None  # map axes

        if SELECT_FILE:
            self.fname = None  # name of kml file
            self.fname_lab = None  # text in label with selected file name
            self.speed_entry = None  # entry of rv speed
            self.date_entry = None  # entry of start date
            self.time_entry = None  # entry of start time
            self.distance = 200  # distance between rv and sat
        self.toolbar = None  # map toolbar
        self.canvas = None  # canvas for map
        self.canvas_widget = None  # canvas widget for map
        self.col_loc = None  # color location for circle
        self.scat_loc = None  # scatter location for circle
        self.col_scat = None  # color of scatter for circle
        self.sat_scat = None  # sat of scatter for circle
        self.circ = None  # circle around current highlight point
        self.circ_cent_lon = 0
        self.circ_cent_lat = 0
        self.start_date = None  # start date of calculation

    def slide_left(self, event):
        """
        process case when user click left arrow
        """
        current_value = self.slider.get()
        if current_value > 0:
            self.slider.set(current_value - 5)  # main time step is 5 minutes
            self.update_elevation(event)

    def slide_right(self, event):
        """
        process case when user click right arrow
        """
        current_value = self.slider.get()
        if current_value < 24 * 60:
            self.slider.set(current_value + 5)  # main time step is 5 minutes
            self.update_elevation(event)

    def click_update_tle(self):
        """
        updating tle/tle_data.txt file from data from links in tle/tle_sites.txt file
        while updating temporary file tle_data_tmp.txt creating for saving backup previous data
        """

        len = sum(1 for line in open(path_to_af + 'tle/tle_sites.txt', 'r'))  # number of satellites
        data = open(path_to_af + 'tle/tle_data_tmp.txt', 'w')  # file with previous TLE data
        time = dt.utcnow().strftime("%d.%m.%Y %H:%M:%S")  # current time to record
        data.write("# last update : " + time + " UTC\n")

        with open(path_to_af + 'tle/tle_sites.txt', 'r') as file:  # reading sites from file with links
            for count, line in enumerate(file):
                try:
                    f = requests.get(line[:-1])
                    if f.status_code != 200:
                        messagebox.showerror(title="AltiFore: Upload TLE error", message="Check your connection!")

                except requests.exceptions.RequestException as e:

                    # if error caught previous data saves and shows an error

                    if str(e)[:2] == 'No':
                        messagebox.showerror(title="AltiFore: Upload TLE error",
                                             message="Check link in tle_sites.txt!\n Error with " + line)

                    else:
                        messagebox.showerror(title="AltiFore: Upload TLE error",
                                             message="Check your internet connection! If the error remains, "
                                                     "write on ezhova.ea@phystech.edu")

                    self.sty.configure("LabeledProgressbar", text="TLE wasn't updated =(")
                    self.root.update()
                    data.close()
                    return 0

                data.write(f.text)
                data.write('\n')
                self.bar['value'] = int(100 * count / (len - 1))  # update progress bar
                self.sty.configure("LabeledProgressbar", text="TLE for " + f.text[:13] + " successfully updated!")
                self.root.update()

        data.close()
        move(path_to_af + 'tle/tle_data_tmp.txt', path_to_af + 'tle/tle_data.txt')  # replace old file by new
        self.sty.configure("LabeledProgressbar", text="Last update of TLE : " + time + " UTC")  # update text on bar
        self.root.update()

    def click_select(self):
        """
        process case when user click "Select file!" button
        """
        global once_sel

        ftypes = (('OpenCPN files', '*.kml'), ('All files', '*.*'))
        self.fname = filedialog.askopenfilename(title='Select a file', initialdir=__file__, filetypes=ftypes)

        short_name = self.fname.rsplit('/', 1)[-1]  # only file name for displaying
        if once_sel:
            self.fname_lab = ttk.Label(self.select_frame_up, text=short_name)
            self.fname_lab.pack(side='left', padx=10)
        else:
            self.fname_lab.config(text=short_name)

        if once_sel:  # currently we do not re-process data, app should be restarted

            ttk.Label(self.select_frame_down, text='Average speed').pack(side='left', padx=5)
            self.speed_entry = ttk.Entry(self.select_frame_down, width=4)
            self.speed_entry.pack(side='left')
            ttk.Label(self.select_frame_down, text='kn').pack(side='left', padx=10)

            now = dt.utcnow().strftime("%d/%m/%y %H:%M").split(" ")

            ttk.Label(self.select_frame_down, text='Start date').pack(side='left', padx=5)
            self.date_entry = ttk.Entry(self.select_frame_down, width=10)
            self.date_entry.insert(0, now[0])
            self.date_entry.pack(side='left', padx=10)

            ttk.Label(self.select_frame_down, text='Time').pack(side='left', padx=5)
            self.time_entry = ttk.Entry(self.select_frame_down, width=6)
            self.time_entry.insert(0, now[1])
            self.time_entry.pack(side='left', padx=10)

            tk.Button(self.select_frame_up, text="Calculate from file!", command=self.click_calc_file, bg='pink').pack(
                side='right', padx=5)
            once_sel = False

    def click_tab(self):
        """
        process case when user click "Calculate from table!" button
        """
        global once_cal

        if not once_cal:
            self.reboot_map()
        else:
            once_cal = False

        self.tr_lat = []
        self.tr_lon = []
        try:
            self.distance = float(self.km_entry.get())
        except ValueError:
            messagebox.showerror('Altifore: Enter error', 'Check distance field!')
            return 0

        datetimes = []

        for i in range(len(self.entry_arr[0])):
            try:
                datetimes.append(dt.strptime(self.entry_arr[0][i].get() + " " + self.entry_arr[1][i].get(),
                                             '%d/%m/%y %H:%M').replace(tzinfo=utc))
            except ValueError:
                messagebox.showerror("AltiFore: Enter Error", "Check date or time in " + str(i + 1) + "th row!")
                return 0

            try:
                lat_str = list(map(int, self.entry_arr[2][i].get().split()))
                self.tr_lat.append(
                    np.sign(lat_str[0]) * (np.abs(lat_str[0]) + (lat_str[1] + lat_str[2] / 60.) / 60.))
            except ValueError:
                messagebox.showerror("AltiFore: Enter Error", "Check latitude in " + str(i + 1) + "th row!")
                return 0

            try:
                lon_str = list(map(int, self.entry_arr[3][i].get().split()))
                self.tr_lon.append(
                    np.sign(lon_str[0]) * (np.abs(lon_str[0]) + (lon_str[1] + lon_str[2] / 60.) / 60.))
            except ValueError:
                messagebox.showerror("AltiFore: Enter Error", "Check longitude in " + str(i + 1) + "th row!")
                return 0

        self.res_list, self.draw_arr = calc(self.distance, self.tr_lat, self.tr_lon, datetimes, self.save_name)
        self.start_date = datetimes[0]

        if len(self.draw_arr) == 0:
            messagebox.showwarning("AltiFore: Calculation Warning", "No flights for entered data :(")
            self.tr_lat = []
            self.tr_lon = []

        else:
            num_of_days = (datetimes[-1] - datetimes[0]).days + 1
            res_sheet = prepare_sheet(datetimes[0], num_of_days)
            path_to_save = self.save_name.get()

            convert_list(path_to_save + ".xlsx", res_sheet, self.res_list)

            self.draw_map()

    def click_calc_file(self):
        """
        process case when user click "Calculate from file!" button
        """
        global once_cal

        if not once_cal:
            self.reboot_map()
        else:
            once_cal = False

        try:
            speed = float(self.speed_entry.get())
        except ValueError:
            messagebox.showerror('Altifore: Enter error', 'Check speed field!')
            return 0

        try:
            self.start_date = dt.strptime(self.date_entry.get() + " " + self.time_entry.get(),
                                          '%d/%m/%y %H:%M').replace(tzinfo=utc)
        except ValueError:
            messagebox.showerror('Altifore: Enter error', 'Check start date and time fields!')
            return 0

        try:
            self.distance = float(self.km_entry.get())
        except ValueError:
            messagebox.showerror('Altifore: Enter error', 'Check distance field!')
            return 0

        (self.res_list, self.draw_arr), last_date, self.tr_lat, self.tr_lon = calc_from_file(self.fname,
                                                                                             self.distance,
                                                                                             self.start_date, speed,
                                                                                             self.save_name)

        if self.res_list == -1:
            messagebox.showerror('Altifore: Saving error', 'Check path for saving!')
            return 0

        num_of_days = (last_date - self.start_date).days + 2
        res_sheet = prepare_sheet(self.start_date, num_of_days)
        path_to_save = self.save_name.get()
        convert_list(path_to_save + ".xlsx", res_sheet, self.res_list)
        self.draw_map()

    def add_row_to_column(self):
        """
        add a new row of entries to the bottom of table
        """
        self.calc_table_button.config(bg='LawnGreen')
        for col in range(4):
            en = ttk.Entry(self.line_frames[col], width=int(self.win_x * 0.006))

            if len(self.entry_arr[-1]) != 0:
                if self.entry_arr[col][-1].get() != "":
                    en.insert(0, self.entry_arr[col][-1].get())
            en.pack()
            self.entry_arr[col].append(en)

    def remove_row_from_column(self):
        """
        remove a last row of entries from the bottom of table
        """
        for col in range(4):
            if self.entry_arr[col]:
                last_row = self.entry_arr[col].pop()
                last_row.destroy()

    def draw_map(self):
        """
        drawing a map
        """
        self.fig = plt.figure(figsize=(4, 8), dpi=300)
        # limits
        lat_min = int(np.min(self.tr_lat)) - 3
        lat_max = int(np.max(self.tr_lat)) + 3
        lon_min = int(np.min(self.tr_lon)) - 3
        lon_max = int(np.max(self.tr_lon)) + 3
        if PROJECTION == "Ortho":
            self.ax = self.fig.add_subplot(1, 1, 1, projection=ccrs.Orthographic(0.5 * (lon_min + lon_max),
                                                                                 0.5 * (lat_min + lat_max)))
        else:
            self.ax = self.fig.add_subplot(1, 1, 1, projection=ccrs.Mercator())
        self.ax.set_extent([lon_min, lon_max, lat_min, lat_max])
        # tick steps
        step_lon = (lon_max - lon_min) / 10.
        step_lat = (lat_max - lat_min) / 10.
        if step_lat > 1.: step_lat = round(step_lat)
        if step_lon > 1.: step_lon = round(step_lon)

        resol = '50m'
        ocean = cfe.NaturalEarthFeature('physical', 'ocean', scale=resol, edgecolor='none', facecolor='white')
        land = cfe.NaturalEarthFeature('physical', 'land', scale=resol, edgecolor='k',
                                       facecolor=cfe.COLORS['land_alt1'])

        self.ax.add_feature(ocean, zorder=0, linewidth=0.2)
        self.ax.add_feature(land, zorder=0, linewidth=0.2)
        self.ax.add_feature(cfe.COASTLINE, linewidth=0.2, zorder=0)

        gl = self.ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=0.2, color='grey', alpha=1)
        gl.bottom_labels = False
        gl.left_labels = False
        gl.xlocator = mticker.FixedLocator(np.arange(-180, 180, step_lon))
        gl.ylocator = mticker.FixedLocator(np.arange(-90, 90, step_lat))
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        gl.xlabel_style = {'size': 4}
        gl.ylabel_style = {'size': 4}

        self.col_scat = [colors[int(s)] for s in self.draw_arr[:, 2]]
        self.col_loc = ['black' for s in self.tr_lat]
        self.sat_scat = self.ax.scatter(self.draw_arr[:, 0], self.draw_arr[:, 1], edgecolors=self.col_scat, s=3,
                                        zorder=10, facecolors=None, transform=ccrs.PlateCarree())

        for i in range(0, self.draw_arr[:, 0].shape[0], 3):
            self.ax.plot(self.draw_arr[i:i + 3, 0], self.draw_arr[i:i + 3, 1], color=self.col_scat[i], lw=1, zorder=10,
                         transform=ccrs.PlateCarree())

        self.scat_loc = self.ax.scatter(self.tr_lon, self.tr_lat, label='Маршрут', zorder=10, marker='+',
                                        color=self.col_loc, s=3, transform=ccrs.PlateCarree())

        self.circ, = self.ax.plot([0], [-89.9], color="black", transform=ccrs.PlateCarree(), zorder=9)
        self.circ_cent_lat = -89.9
        self.circ_cent_lon = 0
        pp = []
        pp.append(self.scat_loc)

        for i in range(len(SAT_NAMES)):
            pp_ = plt.scatter([0], [-89.9], color=colors[i], label=SAT_NAMES[i], transform=ccrs.PlateCarree())
            pp.append(pp_)

        path_to_save = self.save_name.get()
        try:
            plt.savefig(path_to_save + ".png", dpi=300, bbox_inches='tight')
        except:
            messagebox.showerror("AltiFore: Saving Error", "Check entered path to saving!")

        self.fig.tight_layout(h_pad=10, w_pad=10)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas_widget = self.canvas.get_tk_widget()

        self.toolbar = MyToolbar(self.canvas, self.map_frame)
        self.toolbar.update()
        self.toolbar.pack(side='top')

        self.canvas_widget.pack(side='top')
        self.canvas.mpl_connect('motion_notify_event', self.display_coords)

    def reboot_map(self):
        if self.fig:
            self.fig.clf()  # map figure
        self.ax = None  # map axes
        if self.toolbar:
            self.toolbar.destroy()  # map toolbar
        if self.canvas:
            self.canvas.get_tk_widget().pack_forget()  # canvas for map
        self.col_loc = None  # color location for circle
        self.scat_loc = None  # scatter location for circle
        self.col_scat = None  # color of scatter for circle
        self.sat_scat = None  # sat of scatter for circle
        self.circ = None  # circle around current highlight point
        self.circ_cent_lat = -89.9
        self.circ_cent_lon = 0

    def display_coords(self, event):
        """
        displaying coordinates of cursor or the flight, drawing circle around chosen point
        """
        inverse_trans = self.ax.transData.inverted()
        geo_coords = inverse_trans.transform((event.x, event.y))
        longitude, latitude = geo_coords
        x, y = ccrs.PlateCarree().transform_point(longitude, latitude, self.ax.projection)
        message = None

        if x is not None and y is not None:
            distance = np.square(y - self.draw_arr[:, 1]) + np.square((x - self.draw_arr[:, 0]))

            if np.min(distance) < 0.5:
                arg = int(np.argmin(distance))
                fl_time = dt.utcfromtimestamp(self.draw_arr[arg, 4]).strftime("%d.%m.%Y %H:%M")

                ship_time = float(self.ship_time_entry.get())

                fl_ship = dt.utcfromtimestamp(self.draw_arr[arg, 4] + ship_time * 3600).strftime("%H:%M")

                deg_lat = round(np.fix(self.draw_arr[arg, 1]))
                min_lat = int((self.draw_arr[arg, 1] - deg_lat) * 60 * np.sign(self.draw_arr[arg, 1]))
                deg_lon = round(np.fix(self.draw_arr[arg, 0]))
                min_lon = int((self.draw_arr[arg, 0] - deg_lon) * 60 * np.sign(self.draw_arr[arg, 0]))

                coords = f" Lat: {deg_lat:3.0f}° {min_lat:2.0f}', Lon: {deg_lon:3.0f}° {min_lon:2.0f}'"

                message = f"{SAT_NAMES[int(self.draw_arr[arg, 2])]} : " + fl_time + " (" + fl_ship + ")\n" \
                          + coords + f", Dist = {self.draw_arr[arg, 3]:3.0f} km"

                if self.circ_cent_lon != self.draw_arr[arg, -2] and self.circ_cent_lat != self.draw_arr[arg, -3]:
                    # updating place of circle

                    self.circ_cent_lat = self.draw_arr[arg, -3]
                    self.circ_cent_lon = self.draw_arr[arg, -2]

                    ang = np.linspace(0, 360, 36)
                    circle_arr = np.zeros(shape=(ang.shape[0], 2))
                    for i, a in enumerate(ang):
                        circle_arr[i, 0], circle_arr[i, 1], _ = geod.fwd(self.circ_cent_lon, self.circ_cent_lat, a,
                                                                         self.draw_arr[arg, 3] * 1000.)

                    self.circ.remove()
                    self.circ, = self.ax.plot(circle_arr[:, 0], circle_arr[:, 1], transform=ccrs.PlateCarree(),
                                              color='black', lw=0.5)
                    self.col_loc = ['black'] * len(self.tr_lat)
                    self.col_loc[int(self.draw_arr[arg, -1])] = 'red'

            else:
                # removing circle and colorful points
                self.col_loc = ['black' for s in self.tr_lat]
                self.circ_cent_lat = -89.9
                self.circ_cent_lon = 0

            self.scat_loc.remove()
            # updating a color of track points
            self.scat_loc = self.ax.scatter(self.tr_lon, self.tr_lat, label='Input locations', zorder=10, marker='+',
                                            color=self.col_loc, s=5, transform=ccrs.PlateCarree())
            self.canvas.draw()

            if message is None:  # if we far from any flight display cursor coordinates
                d_lat = round(np.fix(y))
                m_lat = int((y - d_lat) * 60 * np.sign(y))
                d_lon = round(np.fix(x))
                m_lon = int((x - d_lon) * 60 * np.sign(x))
                message = f"\nLat: {d_lat:3.0f}° {m_lat:2.0f}', Lon: {d_lon:3.0f}° {m_lon:2.0f}'"
        else:
            message = "Hover on map"

        self.tooltip_label.config(text=message, font=("TkDefaultFont", 16))

    def run(self):
        self.root.mainloop()
