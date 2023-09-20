import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
from PIL import Image, ImageTk
from suncalc import get_position

from datetime import datetime
import requests
from skyfield.api import utc  # conda install -c conda-forge skyfield
from shutil import move

import matplotlib.pyplot as plt  # conda install -c conda-forge matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.ticker as mticker
from matplotlib.patches import Circle
import cartopy.crs as ccrs  # conda install -c conda-forge cartopy
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.feature as cfe
from datetime import datetime as dt

from tabber import prepare_sheet, convert_list
from calculator import calc_from_file, calc
from const import *

once_sel = True
once_cal = True


class MyToolbar(NavigationToolbar2Tk):
    def set_message(self, s):
        pass


class MainWindow:
    def __init__(self, monitor_size=(1920, 1080)):

        self.draw_arr = np.ndarray
        self.res_list = np.ndarray
        self.tr_lat = []
        self.tr_lon = []
        self.win_x = int(monitor_size[0] * 0.8)
        self.win_y = int(monitor_size[1] * 0.7)
        self.center_x = int(0.5 * (monitor_size[0] - self.win_x))
        self.center_y = int(0.5 * (monitor_size[1] - self.win_y))

        self.root = tk.Tk()
        self.root.title("AltiFore")
        self.root.geometry(f'{self.win_x}x{self.win_y}+{self.center_x}+{self.center_y}')
        self.root.iconbitmap('@' + path_to_af + '/altifore.ico')

        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(side='right', expand=True, fill='both')
        self.right_frame.pack_propagate(False)

        self.sun_frame = tk.Frame(self.right_frame)
        self.sun_frame.pack(side='top', pady=20)
        self.sun_frame_left = tk.Frame(self.sun_frame)
        self.sun_frame_left.pack(side='left', padx=5)
        self.sun_frame_left_up = tk.Frame(self.sun_frame_left)
        self.sun_frame_left_up.pack(side='top', padx=5, pady=10)
        self.sun_frame_left_down = tk.Frame(self.sun_frame_left)
        self.sun_frame_left_down.pack(side='top', padx=5)
        self.sun_frame_right = tk.Frame(self.sun_frame)
        self.sun_frame_right.pack(side='right', padx=5)
        self.map_frame = tk.Frame(self.right_frame)
        self.map_frame.pack(side='top', expand=True, fill='both')

        ttk.Label(self.sun_frame_left_up, text="Your date ").pack(side='left')
        self.dat_entry = ttk.Entry(self.sun_frame_left_up, width=10)
        sup_date = datetime.utcnow().date().strftime("%d/%m/%Y")
        self.dat_entry.insert(0, sup_date)
        self.dat_entry.pack(side='left', padx=10)

        ttk.Label(self.sun_frame_left_down, text="Your latitude ").pack(side='left')
        self.lat_entry = ttk.Entry(self.sun_frame_left_down, width=10)
        self.lat_entry.insert(0, '\u00B1dd mm ss')
        self.lat_entry.pack(side='left', padx=10)
        ttk.Label(self.sun_frame_left_down, text="longitude ").pack(side='left')
        self.lon_entry = ttk.Entry(self.sun_frame_left_down, width=10)
        self.lon_entry.insert(0, '\u00B1dd mm ss')
        self.lon_entry.pack(side='left', padx=10)
        self.slider_label = ttk.Label(self.sun_frame_right, text="Enter coordinates to calculate Sun elevation. "
                                                                 "Use arrows to move Sun through the day.")

        self.slider_label.pack(padx=10, pady=10)
        self.slider = ttk.Scale(self.sun_frame_right, from_=0, to=24 * 60, length=self.win_x * 0.4, orient="horizontal")
        self.slider.pack(padx=10, pady=10)
        self.sun_image = ImageTk.PhotoImage(Image.open(path_to_af + "sun.png").resize((50, 50)))
        self.sun_label = ttk.Label(self.sun_frame_right, image=self.sun_image, background="")
        self.sun_label.pack(side='top')
        self.slider.bind("<Motion>", self.update_elevation)
        self.root.bind("<Left>", self.slide_left)
        self.root.bind("<Right>", self.slide_right)

        self.left_frame = tk.Frame(self.root)
        self.left_frame.pack(side='top', pady=20)
        ttk.Label(self.left_frame,
                  text="Welcome to AltiFore! Here you can prognose altimeters tracks. \n"
                       "Select a .KML file or enter your vessel track manually. \n\n"
                       "After calculation, you will receive a .PNG map with marked altitracks,\n "
                       "a .XLSX with a daily schedule and .TXT with description of each span. \n\n"
                       "In any unclear situation, please restart the app.\n\n"
                       "!!!!! ALL TIMES IN UTC FORMAT !!!!!", justify='center').pack(side='top')

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
        tle_date = open(path_to_af + "tle/tle_data.txt", 'r').readline()[16:-1]
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
        self.calc_table_button = tk.Button(self.add_frame, text="Calculate table!", command=self.click_tab)
        self.calc_table_button.pack(pady=10, side='left', padx=5)
        self.rem_row_button = tk.Button(self.add_frame, text="Remove last row", command=self.remove_row_from_column)
        self.rem_row_button.pack(pady=10, side='right', padx=5)

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

        self.fig = None
        self.ax = None
        self.fname = None
        self.speed_entry = None
        self.date_entry = None
        self.time_entry = None
        self.distance = 200
        self.toolbar = None
        self.canvas = None
        self.canvas_widget = None
        self.col_loc = None
        self.scat_loc = None
        self.col_scat = None
        self.sat_scat = None
        self.circ = None
        self.start_date = None

    def update_elevation(self, event):
        selected_hour = int(self.slider.get() / 60)
        selected_min = int(self.slider.get() - 60 * selected_hour)

        if selected_hour == 24:
            selected_hour = 23
            selected_min = 59

        try:
            lat_str = list(map(int, self.lat_entry.get().split()))
            lat = np.sign(lat_str[0]) * (np.abs(lat_str[0]) + (lat_str[1] + lat_str[2] / 60.) / 60.)
            lon_str = list(map(int, self.lon_entry.get().split()))
            lon = np.sign(lon_str[0]) * (np.abs(lon_str[0]) + (lon_str[1] + lon_str[2] / 60.) / 60.)

            dat_str = self.dat_entry.get().split('/')
            selected_time = datetime(int(dat_str[-1]), int(dat_str[-2]), int(dat_str[-3]), int(selected_hour),
                                     int(selected_min))

            sun_position = get_position(selected_time, lon, lat)
            elevation = sun_position['altitude'] * 180 / np.pi

            self.slider_label.config(
                text=f"Selected time: {selected_hour:2d}:{selected_min:2d}        "
                     f"Sun Elevation: {elevation:.2f}" + chr(176))
            self.sun_label.place(x=self.slider.get() / 24 / 60 * ((self.win_x - 250) * 0.4), y=32)
        except:
            pass

    def slide_left(self, event):
        current_value = self.slider.get()
        if current_value > 0:
            self.slider.set(current_value - 5)
            self.update_elevation(event)

    def slide_right(self, event):
        current_value = self.slider.get()
        if current_value < 24 * 60:
            self.slider.set(current_value + 5)
            self.update_elevation(event)

    def click_update_tle(self):

        len = sum(1 for line in open(path_to_af + 'tle/tle_sites.txt', 'r'))  # number of satellites
        data = open(path_to_af + 'tle/tle_data_tmp.txt', 'w')  # file with previous TLE data
        time = datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S")  # current time to record
        data.write("# last update : " + time + " UTC\n")

        with open(path_to_af + 'tle/tle_sites.txt', 'r') as file:  # reading sites from file with links
            for count, line in enumerate(file):
                try:
                    f = requests.get(line)

                except requests.exceptions.RequestException as e:

                    if str(e)[:2] == 'No':
                        messagebox.showerror(title="AltiFore: Upload TLE error",
                                             message="Check link in tle_sites.txt!\n Error with " + line)

                    else:
                        messagebox.showerror(title="AltiFore: Upload TLE error",
                                             message="Check your internet connection! If the error remains, "
                                                     "write on ezhova.ea@phystech.edu")

                    self.sty.configure("LabeledProgressbar",
                                       text="TLE wasn't updated =(")
                    self.root.update()
                    data.close()
                    move(path_to_af + 'tle/tle_data_tmp.txt', path_to_af + 'tle/tle_data.txt')
                    return 0

                data.write(f.text)
                data.write('\n')
                self.bar['value'] = int(100 * count / (len - 1))  # update progress bar
                self.sty.configure("LabeledProgressbar", text="TLE for " + f.text[:13] + " successfully updated!")
                self.root.update()

        data.close()
        move(path_to_af + 'tle/tle_data_tmp.txt', path_to_af + 'tle/tle_data.txt')
        self.sty.configure("LabeledProgressbar", text="Last update of TLE : " + time + " UTC")  # update text on bar
        self.root.update()

    def click_select(self):
        global once_sel

        if not once_sel:
            messagebox.showerror("AltiFore Error", "For new prognosis restart a program!")
            return 0

        ftypes = (('OpenCPN files', '*.kml'), ('All files', '*.*'))
        self.fname = fd.askopenfilename(title='Select a file', initialdir=__file__, filetypes=ftypes)

        short_name = self.fname.rsplit('/', 1)[-1]
        ttk.Label(self.select_frame_up, text=short_name).pack(side='left', padx=10)

        if once_sel:
            once_sel = False
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
        global once_cal

        if not once_cal:
            messagebox.showerror("AltiFore Error", "For new prognosis restart a program!")
            return 0

        else:
            once_cal = False
            try:
                self.distance = float(self.km_entry.get())
            except ValueError:
                messagebox.showerror('Altifore: Enter error', 'Check distance field!')
                return 0

            datetimes = []

            for i in range(len(self.entry_arr[0])):
                try:
                    datetimes.append(datetime.strptime(self.entry_arr[0][i].get() + " " + self.entry_arr[1][i].get(),
                                                       '%d/%m/%y %H:%M').replace(tzinfo=utc))
                except ValueError:
                    messagebox.showerror("AltiFore: Enter Error", "Check date or time in " + str(i) + "th row!")
                    return 0

                try:
                    lat_str = list(map(int, self.entry_arr[2][i].get().split()))
                    self.tr_lat.append(
                        np.sign(lat_str[0]) * (np.abs(lat_str[0]) + (lat_str[1] + lat_str[2] / 60.) / 60.))
                except ValueError:
                    messagebox.showerror("AltiFore: Enter Error", "Check latitude in " + str(i) + "th row!")
                    return 0

                try:
                    lon_str = list(map(int, self.entry_arr[3][i].get().split()))
                    self.tr_lon.append(
                        np.sign(lon_str[0]) * (np.abs(lon_str[0]) + (lon_str[1] + lon_str[2] / 60.) / 60.))
                except ValueError:
                    messagebox.showerror("AltiFore: Enter Error", "Check longitude in " + str(i) + "th row!")
                    return 0

            self.res_list, self.draw_arr = calc(self.distance, self.tr_lat, self.tr_lon, datetimes)
            self.start_date = datetimes[0]

            if len(self.draw_arr) == 0:
                messagebox.showwarning("AltiFore: Calculation Warning", "No flights for entered data :(")
                self.tr_lat = []
                self.tr_lon = []

            else:
                num_of_days = (datetimes[-1] - datetimes[0]).days + 1
                res_sheet = prepare_sheet(datetimes[0], num_of_days)
                convert_list(path_to_af + "test.xlsx", res_sheet, self.res_list)
                self.draw_map()

    def click_calc_file(self):

        global once_cal

        if not once_cal:
            messagebox.showerror("AltiFore Error", "For new prognosis restart a program!")
            return 0

        else:
            once_cal = False
            try:
                speed = float(self.speed_entry.get())
            except ValueError:
                messagebox.showerror('Altifore: Enter error', 'Check speed field!')
                return 0

            try:
                self.start_date = datetime.strptime(self.date_entry.get() + " " + self.time_entry.get(),
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
                                                                                                 self.start_date, speed)
            num_of_days = (last_date - self.start_date).days + 2
            res_sheet = prepare_sheet(self.start_date, num_of_days)
            convert_list(path_to_af + "test.xlsx", res_sheet, self.res_list)
            self.draw_map()

    def add_row_to_column(self):
        for col in range(4):
            en = ttk.Entry(self.line_frames[col], width=int(self.win_x * 0.006))

            if len(self.entry_arr[-1]) != 0:
                if self.entry_arr[col][-1].get() != "":
                    en.insert(0, self.entry_arr[col][-1].get())
            en.pack()
            self.entry_arr[col].append(en)

    def remove_row_from_column(self):
        for col in range(4):
            if self.entry_arr[col]:
                last_row = self.entry_arr[col].pop()
                last_row.destroy()

    def draw_map(self):

        self.fig = plt.figure(figsize=(5, 5), dpi=400)
        self.ax = self.fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

        lat_min = int(np.min(self.tr_lat)) - 5
        lat_max = int(np.max(self.tr_lat)) + 5
        lon_min = int(np.min(self.tr_lon)) - 5
        lon_max = int(np.max(self.tr_lon)) + 5

        step_lon = (lon_max - lon_min) / 10.
        step_lat = (lat_max - lat_min) / 10.

        if step_lat > 1.: step_lat = round(step_lat)
        if step_lon > 1.: step_lon = round(step_lon)

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

        self.col_scat = [colors[int(s)] for s in self.draw_arr[:, 2]]
        self.col_loc = ['black' for s in self.tr_lat]
        self.sat_scat = self.ax.scatter(self.draw_arr[:, 0], self.draw_arr[:, 1], color=self.col_scat, s=10, zorder=10)
        self.scat_loc = self.ax.scatter(self.tr_lon, self.tr_lat, label='Input locations', zorder=10, marker='+',
                                        color=self.col_loc, s=5)
        self.circ = Circle((0, -89.9), self.distance / 111., fill=False, color='aqua', transform=ccrs.PlateCarree())
        self.ax.add_artist(self.circ)

        for i in range(len(SAT_NAMES)):
            plt.scatter([0], [-89.9], color=colors[i], label=SAT_NAMES[i])
        plt.legend(loc='best', fontsize="4")
        plt.savefig(path_to_af + "test.png", dpi=600, bbox_inches='tight')
        self.fig.tight_layout(h_pad=10, w_pad=10)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas_widget = self.canvas.get_tk_widget()

        self.toolbar = MyToolbar(self.canvas, self.map_frame)
        self.toolbar.update()
        self.toolbar.pack(side='top')

        self.canvas_widget.pack(side='top')
        self.canvas.mpl_connect('motion_notify_event', self.display_coords)

    def display_coords(self, event):
        x, y = event.xdata, event.ydata

        message = None

        if x is not None and y is not None:
            distance = np.square(y - self.draw_arr[:, 1]) + np.square((x - self.draw_arr[:, 0]))

            if np.min(distance) < 0.5:
                arg = int(np.argmin(distance))
                fl_time = dt.fromtimestamp(self.draw_arr[arg, 4]).strftime("%d.%m.%Y %H:%M:%S")

                deg_lat = round(np.fix(self.draw_arr[arg, 1]))
                min_lat = int((self.draw_arr[arg, 1] - deg_lat) * 60 * np.sign(self.draw_arr[arg, 1]))
                deg_lon = round(np.fix(self.draw_arr[arg, 0]))
                min_lon = int((self.draw_arr[arg, 0] - deg_lon) * 60 * np.sign(self.draw_arr[arg, 0]))

                coords = " Lat: " + str(deg_lat) + chr(176) + str(min_lat)
                coords += "', Lon: " + str(deg_lon) + chr(176) + str(min_lon) + "'"

                message = f"{SAT_NAMES[int(self.draw_arr[arg, 2])]} : " + fl_time + coords + f", Dist = {self.draw_arr[arg, 3]} km"

                if self.circ.center[0] != self.draw_arr[arg, -2] and self.circ.center[1] != self.draw_arr[arg, -3]:
                    self.circ.center = self.draw_arr[arg, -2], self.draw_arr[arg, -3]
                    self.circ.radius = self.draw_arr[arg, 3] / 111. / np.cos(self.draw_arr[arg, -3] / 180. * np.pi)
                    self.col_loc = ['black' for s in self.tr_lat]
                    self.col_loc[int(self.draw_arr[arg, -1])] = 'aqua'

            else:
                self.col_loc = ['black' for s in self.tr_lat]
                self.circ.center = 0, -89.9

            self.scat_loc.remove()
            self.scat_loc = self.ax.scatter(self.tr_lon, self.tr_lat, label='Input locations', zorder=10, marker='+',
                                            color=self.col_loc, s=5)
            self.canvas.draw()

            if message is None:
                d_lat = round(np.fix(y))
                m_lat = int((y - d_lat) * 60 * np.sign(y))
                d_lon = round(np.fix(x))
                m_lon = int((x - d_lon) * 60 * np.sign(x))
                message = "Lat: "
                message += (str(d_lat) + chr(176) + str(m_lat) + "', Lon: " + str(d_lon) + chr(176) + str(m_lon)) + "'"

        else:
            message = "Hover on map"

        self.tooltip_label.config(text=message)

    def run(self):
        self.root.mainloop()
