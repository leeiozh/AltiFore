import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
from datetime import datetime
import requests
from tabber import prepare_sheet, convert_list
from calculator import calc_from_file, calc
from skyfield.api import utc

import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import matplotlib.ticker as mticker
from matplotlib.patches import Circle
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.feature as cfe
from datetime import datetime as dt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

path_to_af = __file__[:-len(__file__.split('/')[-1])]
colors = ['yellow', 'red', 'orange', 'green', 'blue', 'purple', 'pink', 'grey']
SAT_NAMES = ['CFOSAT', 'HAIYANG-2B', 'JASON-3', 'SARAL', 'SENTINEL-3A', 'SENTINEL-3B', 'SENTINEL-6', 'CRYOSAT 2']

once = True


class MainWindow:
    def __init__(self, monitor_size=(1920, 1080)):

        self.fig = plt.figure(figsize=(5, 5), dpi=400)
        self.ax = self.fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        self.arr_for_draw = []
        self.result_list = []
        self.tr_lat = []
        self.tr_lon = []
        self.win_x = int(monitor_size[0] * 0.8)
        self.win_y = int(monitor_size[1] * 0.6)
        self.center_x = int(0.5 * (monitor_size[0] - self.win_x))
        self.center_y = int(0.5 * (monitor_size[1] - self.win_y))

        self.root = tk.Tk()
        self.root.title("AltiFore")
        self.root.geometry(f'{self.win_x}x{self.win_y}+{self.center_x}+{self.center_y}')
        self.root.iconbitmap('@' + path_to_af + '/altifore.xbm')

        self.map_frame = tk.Frame(self.root)
        self.map_frame.pack(side='right', expand=True, fill='both')
        self.map_frame.pack_propagate(False)

        self.left_frame = tk.Frame(self.root)
        self.left_frame.pack(side='top', pady=20)
        ttk.Label(self.left_frame,
                  text="Welcome to AltiFore! Here you can prognose altimeters tracks. \n"
                       "Select a .KML file or enter your vessel track manually. \n\n"
                       "After calculation, you will receive a .PNG map with marked altitracks,\n "
                       "a .XLSX with a daily schedule and .TXT with description of each span. \n\n"
                       "In any unclear situation, please restart the app.", justify='center').pack(side='top')

        # self.init_map()

        self.tooltip_label = tk.Label(self.map_frame, text="Calculate smth to show a map", padx=5, pady=5)
        self.tooltip_label.pack(side='bottom')

        ### frame for TLE progress bar and update button ###
        self.tle_frame = tk.Frame(self.left_frame)
        self.tle_frame.pack(side='top', pady=10)

        ### subframe for progress bar ###
        self.bar_frame = tk.Frame(self.tle_frame)
        self.bar_frame.pack(side='left', pady=10, padx=5)
        self.sty = ttk.Style(self.root)
        self.sty.layout("LabeledProgressbar", [('LabeledProgressbar.trough', {
            'children': [('LabeledProgressbar.pbar', {'side': 'left', 'sticky': 'ns'}),
                         ("LabeledProgressbar.label", {"sticky": ""})], 'sticky': 'nswe'})])
        self.bar = ttk.Progressbar(self.bar_frame, orient="horizontal", length=int(self.win_x * 0.3),
                                   style="LabeledProgressbar")
        self.bar.pack()
        tle_date = open("/home/leeiozh/ocean/AltiFore/tle/tle_data.txt", 'r').readline()[16:-1]
        self.sty.configure("LabeledProgressbar", text="Last update of TLE : " + tle_date)

        ### subframe update TLE button ###
        self.but_tle_frame = tk.Frame(self.tle_frame)
        self.but_tle_frame.pack(side='right', padx=5, pady=10)
        self.but_tle_up = tk.Button(self.but_tle_frame, text='Update TLE!', command=self.click_update_tle, width=10)
        self.but_tle_up.pack()

        ### frame for distance entry ###
        self.dist_frame = tk.Frame(self.left_frame)
        self.dist_frame.pack(side='top', padx=5)
        ttk.Label(self.dist_frame, text="Distance between vessel and satellite tracks ").pack(side='left')
        self.km_entry = ttk.Entry(self.dist_frame, width=5)
        self.km_entry.insert(0, "200")
        self.km_entry.pack(side='left')
        ttk.Label(self.dist_frame, text="km").pack(side='left')

        ### frame for selecting a file ###
        self.select_frame = tk.Frame(self.left_frame)
        self.select_frame.pack(side='top', padx=5, pady=10)

        ### subframe for buttons and path ###
        self.select_frame_up = ttk.Frame(self.select_frame)
        self.select_frame_up.pack(side='top', pady=10)
        self.but_select = ttk.Button(self.select_frame_up, text='Select a file', command=self.click_select)
        self.but_select.pack(side='left')

        ### subframe for speed and start_date entries ###
        self.select_frame_down = ttk.Frame(self.select_frame)
        self.select_frame_down.pack(side='top', pady=5)

        ### frame for tabular button ###
        self.add_frame = ttk.Frame(self.left_frame)
        self.add_frame.pack(side='top', pady=10)

        self.add_row_button = tk.Button(self.add_frame, text="Add new row", command=self.add_row_to_column)
        self.add_row_button.pack(pady=10, side='left', padx=5)
        self.add_row_button = tk.Button(self.add_frame, text="Calculate table!", command=self.click_tab)
        self.add_row_button.pack(pady=10, side='right', padx=5)

        ### frame for tabular ###
        self.table_frame = ttk.Frame(self.left_frame)
        self.table_frame.pack(side='top')

        ### subframes for tabular ###
        self.line_frames = []
        self.entry_arr = [[] for _ in range(4)]
        labels = ["Date (dd/mm/yy)", "Time (hh:mm)", u"Latitude (\u00B1dd mm ss)", u"Longitude (\u00B1dd mm ss)"]
        for column in range(4):
            frame = tk.Frame(self.table_frame)
            frame.pack(side="left", padx=int(self.win_x * 0.008), pady=10)
            ttk.Label(frame, text=labels[column]).pack(side="top")
            self.line_frames.append(frame)

    def click_update_tle(self):

        len = sum(1 for line in open(path_to_af + 'tle/tle_sites.txt', 'r'))  # number of satellites
        data = open(path_to_af + 'tle/tle_data.txt', 'w')  # file with previous TLE data
        time = datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S")  # current time to record
        data.write("# last update : " + time + " UTC\n")

        with open(path_to_af + 'tle/tle_sites.txt', 'r') as file:  # reading sites from file with links
            for count, line in enumerate(file):
                f = requests.get(line)

                if f.text == "No GP data found":
                    messagebox.showerror(title="AltiFore: Upload TLE error",
                                         message="Check link in tle_sites.txt!\n Error with " + line + ".")

                if f.text[1] == "!":
                    messagebox.showerror(title="AltiFore: Upload TLE error",
                                         message="Too much requests. \n Try again after 1 hour.")
                    break

                data.write(f.text)
                data.write('\n')
                self.bar['value'] = int(100 * count / (len - 1))  # update progress bar
                self.sty.configure("LabeledProgressbar", text="TLE for " + f.text[:13] + " successfully updated!")
                self.root.update()

        data.close()
        self.sty.configure("LabeledProgressbar", text="Last update of TLE : " + time + " UTC")  # update text on bar
        self.root.update()

    def click_select(self):
        global once

        if not once:
            messagebox.showerror("AltiFore Error", "For new prognose restart a program!")

        ftypes = (('OpenCPN files', '*.kml'), ('All files', '*.*'))
        self.fname = fd.askopenfilename(title='Select a file', initialdir=__file__, filetypes=ftypes)

        short_name = self.fname.rsplit('/', 1)[-1]
        self.lab_file = ttk.Label(self.select_frame_up, text=short_name).pack(side='left', padx=10)

        if once:
            once = not once
            ttk.Label(self.select_frame_down, text='Average speed').pack(side='left', padx=5)
            self.speed_entry = ttk.Entry(self.select_frame_down, width=4)
            self.speed_entry.pack(side='left')
            ttk.Label(self.select_frame_down, text='kn').pack(side='left', padx=10)

            ttk.Label(self.select_frame_down, text='Start date').pack(side='left', padx=5)
            self.date_entry = ttk.Entry(self.select_frame_down, width=10)
            self.date_entry.insert(0, "dd/mm/yy")
            self.date_entry.pack(side='left')
            ttk.Label(self.select_frame_down, text='Time').pack(side='left', padx=5)
            self.time_entry = ttk.Entry(self.select_frame_down, width=6)
            self.time_entry.insert(0, "hh:mm")
            self.time_entry.pack(side='left')
            ttk.Button(self.select_frame_up, text="Calculate file!", command=self.click_calc_file).pack(side='right',
                                                                                                        padx=5)

    def click_tab(self):

        try:
            self.distance = float(self.km_entry.get())
        except ValueError:
            messagebox.showerror('Altifore: Enter error', 'Check distance field!')
            return 0

        datetimes = []
        lats = []
        lons = []

        for i in range(len(self.entry_arr[0])):
            try:
                datetimes.append(datetime.strptime(self.entry_arr[0][i].get() + " " + self.entry_arr[1][i].get(),
                                                   '%d/%m/%y %H:%M').replace(tzinfo=utc))
            except:
                messagebox.showerror("AltiFore: Enter Error", "Check date or time in " + str(i) + "row!")
                return 0

            try:
                lat_str = list(map(int, self.entry_arr[2][i].get().split()))
                lats.append(np.sign(lat_str[0]) * (np.abs(lat_str[0]) + (lat_str[1] + lat_str[2] / 60.) / 60.))
            except:
                messagebox.showerror("AltiFore: Enter Error", "Check latitude in " + str(i) + "row!")
                return 0

            try:
                lon_str = list(map(int, self.entry_arr[3][i].get().split()))
                lons.append(np.sign(lon_str[0]) * (np.abs(lon_str[0]) + (lon_str[1] + lon_str[2] / 60.) / 60.))
            except:
                messagebox.showerror("AltiFore: Enter Error", "Check longitude in " + str(i) + "row!")
                return 0

        self.result_list, self.arr_for_draw = calc(self.distance, lats, lons, datetimes)
        self.tr_lat = lats
        self.tr_lon = lons

        if len(self.arr_for_draw) == 0:
            messagebox.showwarning("AltiFore: Calculation Warning", "No flights for entered data :(")

        else:
            num_of_days = (datetimes[-1] - datetimes[0]).days + 2
            res_sheet = prepare_sheet(datetimes[0], num_of_days)
            convert_list(path_to_af + "test.xlsx", res_sheet, self.result_list)
            self.draw_map()

    def click_calc_file(self):
        try:
            speed = float(self.speed_entry.get())
        except ValueError:
            messagebox.showerror('Altifore: Enter error', 'Check speed field!')
            return 0

        try:
            start_date = datetime.strptime(self.date_entry.get() + " " + self.time_entry.get(),
                                           '%d/%m/%y %H:%M').replace(tzinfo=utc)
        except ValueError:
            messagebox.showerror('Altifore: Enter error', 'Check start date and time fields!')
            return 0

        try:
            self.distance = float(self.km_entry.get())
        except ValueError:
            messagebox.showerror('Altifore: Enter error', 'Check distance field!')
            return 0

        (self.result_list, self.arr_for_draw), last_date, self.tr_lat, self.tr_lon = calc_from_file(self.fname,
                                                                                                    self.distance,
                                                                                                    start_date, speed)

        num_of_days = (last_date - start_date).days + 2
        res_sheet = prepare_sheet(start_date, num_of_days)
        convert_list(path_to_af + "test.xlsx", res_sheet, self.result_list)

        self.draw_map()

    def add_row_to_column(self):
        for col in range(4):
            en = ttk.Entry(self.line_frames[col], width=int(self.win_x * 0.006))

            if len(self.entry_arr[-1]) != 0:
                if self.entry_arr[col][-1].get() != "":
                    en.insert(0, self.entry_arr[col][-1].get())
            en.pack()
            self.entry_arr[col].append(en)

    def draw_map(self):

        lat_min = int(np.min(self.tr_lat)) - 3
        lat_max = int(np.max(self.tr_lat)) + 3
        lon_min = int(np.min(self.tr_lon)) - 3
        lon_max = int(np.max(self.tr_lon)) + 3

        step_lon = (lon_max - lon_min) / 10.
        step_lat = (lat_max - lat_min) / 10.

        if step_lat > 1.: step_lat = round(step_lat)
        if step_lon > 1.: step_lon = round(step_lon)

        print(lat_min, lat_max, lon_min, lon_max, step_lon, step_lat)

        resol = '50m'
        ocean = cfe.NaturalEarthFeature('physical', 'ocean', scale=resol, edgecolor='none', facecolor='white')
        land = cfe.NaturalEarthFeature('physical', 'land', scale=resol, edgecolor='k', facecolor=cfe.COLORS['land'])

        self.ax.add_feature(ocean, zorder=0, linewidth=0.2)
        self.ax.add_feature(land, zorder=0, linewidth=0.2)
        self.ax.add_feature(cfe.COASTLINE, linewidth=0.2, zorder=0)
        self.ax.add_feature(cfe.BORDERS, linestyle=':', linewidth=0.2, zorder=0)

        gl = self.ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=0.2, color='grey', alpha=1)
        gl.bottom_labels = False
        gl.left_labels = False
        gl.xlocator = mticker.FixedLocator(np.arange(-180, 180, step_lon))
        gl.ylocator = mticker.FixedLocator(np.arange(-90, 90, step_lat))
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        gl.xlabel_style = {'size': 4}
        gl.ylabel_style = {'size': 4}

        self.ax.set_extent([lon_min, lon_max, lat_min, lat_max])

        self.color_for_scat = [colors[int(s)] for s in self.arr_for_draw[:, 2]]

        print(len(self.tr_lat))

        self.color_for_loc = ['black' for s in self.tr_lat]
        self.scat_alpha = [0 for s in self.tr_lat]
        self.scat_sat = self.ax.scatter(self.arr_for_draw[:, 0], self.arr_for_draw[:, 1], color=self.color_for_scat,
                                        alpha=1, s=10, zorder=10)
        self.scat_loc = self.ax.scatter(self.tr_lon, self.tr_lat, label='Input locations', zorder=10, marker='+',
                                        color=self.color_for_loc, s=5)
        self.circle = Circle((0, -89.9), self.distance / 111., fill=False, color='aqua', transform=ccrs.PlateCarree())
        self.artist = self.ax.add_artist(self.circle)
        self.flag = True

        for i in range(len(SAT_NAMES)):
            plt.scatter([0], [-89.9], color=colors[i], label=SAT_NAMES[i])
        plt.legend(loc='best', fontsize="4")
        plt.savefig(path_to_af + "test.png", dpi=600, bbox_inches='tight')
        self.fig.tight_layout(h_pad=5, w_pad=5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack()
        self.canvas.mpl_connect('motion_notify_event', self.display_coords)

    def display_coords(self, event):
        x, y = event.xdata, event.ydata

        message = None

        if x is not None and y is not None:
            distance = np.square(y - self.arr_for_draw[:, 1]) + np.square((x - self.arr_for_draw[:, 0]))

            if np.min(distance) < 1:
                arg = int(np.argmin(distance))
                fl_time = dt.fromtimestamp(self.arr_for_draw[arg, 4]).strftime("%d.%m.%Y %H:%M:%S")

                deg_lat = round(np.fix(self.arr_for_draw[arg, 1]))
                min_lat = int((self.arr_for_draw[arg, 1] - deg_lat) * 60 * np.sign(self.arr_for_draw[arg, 1]))
                deg_lon = round(np.fix(self.arr_for_draw[arg, 0]))
                min_lon = int((self.arr_for_draw[arg, 0] - deg_lon) * 60 * np.sign(self.arr_for_draw[arg, 0]))

                coords = " Lat: " + str(deg_lat) + chr(176) + str(min_lat)
                coords += "', Lon: " + str(deg_lon) + chr(176) + str(min_lon) + "'"

                message = f"{SAT_NAMES[int(self.arr_for_draw[arg, 2])]} : " + fl_time + coords + f", Dist = {self.arr_for_draw[arg, 3]} km"

                self.color_for_loc[int(self.arr_for_draw[arg, -1])] = 'aqua'
                self.circle.center = self.arr_for_draw[arg, 6], self.arr_for_draw[arg, 5]

            else:
                self.color_for_loc = ['black' for s in self.tr_lat]
                self.circle.center = 0, -89.9

            self.scat_loc.remove()
            self.scat_loc = self.ax.scatter(self.tr_lon, self.tr_lat, label='Input locations', zorder=10, marker='+',
                                            color=self.color_for_loc, s=5)

            self.canvas.draw()

            if message is None:
                deg_lat = round(np.fix(y))
                min_lat = int((y - deg_lat) * 60 * np.sign(y))
                deg_lon = round(np.fix(x))
                min_lon = int((x - deg_lon) * 60 * np.sign(x))
                message = "Lat: "
                message += (str(deg_lat) + chr(176) + str(min_lat) + "', Lon: " + str(deg_lon) + chr(176) + str(
                    min_lon)) + "'"

        else:
            message = "Hover on map"

        self.tooltip_label.config(text=message)

    def run(self):
        self.root.mainloop()
